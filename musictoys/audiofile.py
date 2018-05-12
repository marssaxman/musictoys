"""audiofile reads audio files, using either soundfile or ffmpeg."""

import os, subprocess
import tempfile
import soundfile


def read(filename):
    """Retrieve audio samples from a file.

    We will attempt to read the file using the soundfile module. If that fails,
    we will try to execute 'ffmpeg' as a subprocess and read its output.

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

    try:
        return soundfile.read(filename)
    except:
        f = _read_ffmpeg(filename)
        if f is None:
            raise
        return f


def _popen(cmd):
    pipe = subprocess.PIPE
    return subprocess.Popen(cmd, stdin=pipe, stdout=pipe, stderr=pipe)


def _has_ffmpeg():
    # try to run ffmpeg -version and see if we get a sane result.
    proc = _popen(['ffmpeg', '-version'])
    proc.communicate()
    return 0 == proc.returncode


def _read_ffmpeg(filename):
    # use ffmpeg to convert the input file to a temporary wav file we can read
    try:
        tempfd, temppath = tempfile.mkstemp(suffix='.wav')
        proc = _popen(['ffmpeg', '-v', '1', '-y', '-i', filename, temppath])
        proc.communicate()
        if 0 == proc.returncode:
            return soundfile.read(temppath)
        return None
    finally:
        os.close(tempfd)
        os.remove(temppath)


def extensions():
    """List file extension suffixes representing audio formats we support.

    This may vary based on the presence of 'ffmpeg' or the capabilities of
    system libraries.

    Returns
    -------
    extensions : set
        A set of possible extensions in upper and lower case.
    """

    extensions = set()

    soundfile_extensions = {
        'WAV': {'wav'},
        'AIFF': {'aiff'},
        'AU': {'au'},
        'FLAC': {'flac'},
        'OGG': {'ogg', 'oga'},
    }
    for format in soundfile.available_formats().iterkeys():
        extensions.update(soundfile_extensions.get(format, set()))

    # which extensions might be readable with ffmpeg?
    ffmpeg_extensions = {
        'aiff', 'au', 'flac', 'mp2', 'mp3', 'mp4', 'oga', 'ogg', 'wav',
    }
    try:
        proc = _popen(['ffmpeg', '-formats'])
        output, _ = proc.communicate()
        lines = output.split('\n') if 0 == proc.returncode else []
        # The ffmpeg -formats output begins each line with some leading
        # spaces, one or both of "D" or "E", and one or two more spaces.
        # The format name always begins on column 4.
        exts = (line[4:].split(' ', 1)[0] for line in lines)
        extensions.update(e for e in exts if e in ffmpeg_extensions)
    except:
        pass

    # Just for Windows-weirdness, allow uppercase versions of all extensions.
    extensions.update([ext.upper() for ext in extensions])
    return extensions

