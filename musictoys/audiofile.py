"""audiofile reads audio files, using either soundfile or ffmpeg."""


import os, subprocess
import tempfile
import soundfile


def read(filename):
    """Retrieve audio samples from a file.

    We will use the 'soundfile' module if it supports the file's format.
    Otherwise, we will attempt to decode the file using 'ffmpeg' or 'afconvert'.

    Parameters
    ----------
    file : str
        The file to read from.

    Returns
    -------
    data : numpy.ndarray
        If the file is monaural, a one-dimensional array of samples; otherwise
        a two-dimensional array of [channels, samples].

    samplerate : int
        The sampling frequency of the audio data in Hz.
    """

    ext = os.path.splitext(filename)[1]
    reader = _typemap()[ext.lower()]
    return reader(filename)


def extensions():
    """List file extension suffixes representing audio formats we support.

    This may vary based on the version of 'libsndfile' present on this system,
    or by the presence of the 'ffmpeg' or 'afconvert' programs.

    Returns
    -------
    extensions : set
        A set of possible extensions in upper and lower case.
    """
    return set(_typemap().iterkeys())


def _typemap(TYPEMAP = dict()):
    # The type map object will only be allocated once, so we can modify it once
    # if it's still empty, then skip the work on future calls.
    if 0 == len(TYPEMAP):
        # Try options in ascending order of preference, so that later choices
        # override the mappings provided by earlier ones.
        TYPEMAP.update(_ffmpeg_types())
        TYPEMAP.update(_afconvert_types())
        TYPEMAP.update(_soundfile_types())
    return TYPEMAP


def _soundfile_types():
    formats = soundfile.available_formats().iterkeys()
    return {'.' + f.lower(): soundfile.read for f in formats}


def _ffmpeg_types():
    try:
        output = _subprocess(['ffmpeg', '-formats'])
        # The ffmpeg -formats output begins each line with some leading
        # spaces, one or both of "D" or "E", and one or two more spaces.
        # The format name always begins on column 4.
        formats = (line[4:].split(' ', 1)[0] for line in output.split('\n'))
        extensions = ('.' + f.lower() for f in formats)
        return {x: _ffmpeg_read for x in extensions if len(x)}
    except:
        return dict()


def _ffmpeg_read(filename):
    # use ffmpeg to convert the input file to a temporary wav file we can read
    try:
        tempfd, tempname = tempfile.mkstemp(suffix='.wav')
        _subprocess(['ffmpeg', '-v', '1', '-y', '-i', filename, tempname])
        return soundfile.read(tempname)
    finally:
        os.close(tempfd)
        os.remove(tempname)


def _afconvert_types():
    try:
        output = _subprocess(['afconvert', '--help-formats'])
        # afconvert documentation here:
        # https://ss64.com/osx/afconvert.html
        # Example output:
        # 'AIFF' = AIFF (.aiff, .aif)
        #               data_formats: I8 BEI16 BEI24 BEI32
        # We'll simply take everything we find between parentheses.
        extensions = []
        for line in output.split('\n'):
            line = line.strip()
            if not line or line[-1] != ')':
                continue
            extpos = line.rfind('(')
            if extpos == -1:
                continue
            extensions.extend(line[extpos:-1].lower().split(", "))
            print "afconvert extensions: %s" % extensions
        return {e: _afconvert_read for e in extensions}
    except:
        return dict()


def _afconvert_read(file):
    # use ffmpeg to convert the input file to a temporary wav file we can read
    try:
        fd, temp = tempfile.mkstemp(suffix='.wav')
        _subprocess(['afconvert', '-d', 'LEI16', '-f', 'WAVE', file, temp])
        return soundfile.read(temp)
    finally:
        os.close(temp)
        os.remove(temp)


def _subprocess(command):
    pipe = subprocess.PIPE
    proc = subprocess.Popen(command, stdin=pipe, stdout=pipe, stderr=pipe)
    output, _ = proc.communicate()
    retcode = proc.returncode
    if retcode:
        raise subprocess.CalledProcessError(retcode, command, output=output)
    return output

