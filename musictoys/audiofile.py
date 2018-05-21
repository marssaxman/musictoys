"""audiofile reads audio files, combing python libraries and external tools"""

# todo:
# use wavio if available
# call out to sox if present
# implement subproc_write


import os
import subprocess
import tempfile
import struct
import wave
import numpy as np
from collections import namedtuple
import signal
from signal import Clip

# Public API


class FormatError(Exception):
    def __init__(self, message, format=None):
        super(FormatError, self).__init__(message)
        self.format = format


def extensions():
    """List the audio file extensions we recognize."""
    _init()
    global _extensions
    return _extensions.keys()


def read(file):
    """Retrieve audio samples from a file.

    Parameters
    ----------
    file : str
        The file to read from.

    Returns
    -------
    signal : Clip (subclass of numpy.ndarray)
        If the file is monaural, a one-dimensional array of samples; otherwise
        a two-dimensional array of [channels, samples].

    """
    data, sample_rate = _dispatch(file).read(file)
    return Clip(data, sample_rate)


@signal.processor
def write(file, clip):
    _dispatch(file).write(file, clip, clip.sample_rate)


# Internal implementation


_Format = namedtuple('Format', 'name description extensions')
_Codec = namedtuple('_Codec', 'formats read write')

FORMATS = {n: _Format(n, d, x) for n, d, x in [
    ('AAC', "Advanced Audio Coding", {'.aac'}),
    ('AIFC', "Compressed AIFF", {'.aifc'}),
    ('AIFF', "Audio IFF", {'.aiff'}),
    ('AU', "Sun AU", {'.au', '.snd'}),
    ('AVI', "Audio Video Interlaced", {'.avi'}),
    ('CAF', "Apple Core Audio Format", {'.caf'}),
    ('FLAC', "FLAC", {'.flac'}),
    ('M4A', "MPEG-4 Audio Lossless", {'.m4a', '.m4r'}),
    ('M4B', "MPEG-4 Audio Books", {'.m4b'}),
    ('MP2', "MPEG audio layer 2", {'.mp2'}),
    ('MP3', "MPEG audio layer 3", {'.mp3'}),
    ('MP4', "MPEG-4 Part 14", {'.mp4'}),
    ('OGG', "Ogg", {'.ogg'}),
    ('OGA', "Ogg Audio", {'.oga'}),
    ('MOGG', "Multitrack Ogg", {'.mogg'}),
    ('OPUS', "Ogg Opus", {'.opus'}),
    ('WAV', "Waveform Audio", {'.wav'}),
    ('WEBM', "WebM", {'.webm'}),
    ('WMA', "Windows Media Audio", {'.wma'}),
]}


_formats = None
_extensions = None


def _init():
    global _formats, _extensions
    if not _formats:
        _formats = dict()
        # Attempt to instantiate each codec and query it. Some will fail,
        # because they are not supported on the current platform.
        for func in [_ffmpeg, _afconvert, _soundfile, _builtin]:
            try:
                codec = func()
                _formats.update({f.name: codec for f in codec.formats()})
            except:
                pass
    if not _extensions:
        _extensions = dict()
        # Build a table mapping file extensions to the codecs supporting them.
        for fmtname, codec in _formats.iteritems():
            fmt = FORMATS[fmtname]
            for ext in FORMATS[fmtname].extensions:
                _extensions[ext] = codec


def _dispatch(file):
    _init()
    return _extensions[os.path.splitext(file)[1].lower()]


def _fail_write(file, clip, sample_rate):
    raise FormatError("Cannot write '%s' to %s" % (clip.dtype, file))


def _soundfile():
    import soundfile

    def _formats():
        # Get a list of the formats supported by the soundfile lib.
        names = soundfile.available_formats().iterkeys()
        return [FORMATS[n] for n in names if n in FORMATS]

    def _read(file):
        data, samplerate = soundfile.read(file)
        # soundfile returns [frames, channels] which is contrary to numpy
        # conventions, so we'll transpose the output if necessary
        return data.transpose(), samplerate

    return _Codec(_formats, _read, soundfile.write)


def _ffmpeg():
    # Make sure ffmpeg is present and responding.
    _execpipe('ffmpeg', '-version')

    def _formats():
        output = _execpipe('ffmpeg', '-formats')
        # The ffmpeg -formats output begins each line with some leading
        # spaces, one or both of "D" or "E", and one or two more spaces.
        # The format name always begins on column 4.
        out = list()
        for line in output.splitlines():
            fields = line.split()
            if len(fields) < 3:
                continue
            if not fields[0] in ['D', 'E', 'DE']:
                continue
            name = fields[1]
            fmt = FORMATS.get(name.upper())
            if fmt:
                out.append(fmt)
        return out

    def _read(file):
        return _subproc_read('ffmpeg', '-v', '1', '-y', '-i', file,
                             '-vn', '-f', 'wav')

    return _Codec(_formats, _read, _fail_write)


def _afconvert():
    # Make sure afconvert will respond to a hello.
    _execpipe('afconvert', '-h')

    def _formats():
        apple_aliases = {
            'adts': 'AAC', 'm4af': 'M4A', 'm4bf': 'M4B', 'caff': 'CAF',
            'MPG1': 'MP1', 'MPG2': 'MP2', 'MPG3': 'MP3', 'mp4f': 'MP4',
            'WAVE': 'WAV',
        }

        fmts = []
        try:
            output = _execpipe('afconvert', '--help-formats')
        except:
            output = ""
            pass
        # afconvert documentation here:
        # https://ss64.com/osx/afconvert.html
        # Example output:
        # 'AIFF' = AIFF (.aiff, .aif)
        #               data_formats: I8 BEI16 BEI24 BEI32
        # The line begins with a four-char code in single quotes, then.
        # This is Apple's version of the format name.
        for line in output.splitlines():
            line = line.strip()
            if line[0] == "'" and line[5] == "'":
                name = line[1:5]
                name = apple_aliases.get(name, name)
                fmt = FORMATS.get(name)
                if fmt:
                    fmts.append(fmts)
        return fmts

    def _read(file):
        return _subproc_read('afconvert', '-d', 'LEI16', '-f', 'WAVE', file)

    return _Codec(_formats, _read, _fail_write)


def _builtin():

    def _formats():
        return [FORMATS['WAV']]

    return _Codec(_formats, _wav_read, _wav_write)


def _wav_read(file):
    # Read the contents of the file. We'll parse its RIFF tags and find
    # the WAV data to return.
    buffer = np.fromfile(file, dtype=np.uint8)
    # The file should begin with 'RIFF', unless we have a problem with
    # endianness.
    rifftag, _ = struct.unpack("<4sI", buffer[:8])
    if rifftag == 'RIFF':
        endian = "<%s"
    elif rifftag == 'FFIR' or rifftag == 'RIFX':
        endian = ">%s"
    else:
        raise ValueError()

    def unpack(fmt, bytes):
        return struct.unpack(endian % fmt, bytes)
    # The rest of the header should tell us how long the WAV data is.
    chunksize, waveid = unpack("I4s", buffer[4:12])
    assert waveid == "WAVE"
    # The wave buffer should be full of chunks: a 4cc and a length.
    limit = 8 + chunksize
    off = 12
    while off < limit:
        ckid, cksize = unpack("4sI", buffer[off:off+8])
        off += 8
        if ckid == "fmt ":
            (audioformat, nchannels, samplerate, _, blockalign, samplewidth
             ) = unpack("HHIIHH", buffer[off:off+16])
        elif ckid == "data":
            data = buffer[off:off+cksize]
        off += cksize
        if (off % 1):
            off += 1

    # Reinterpret the bytes we found in some more useful datatype.
    data = data.view(dtype=np.dtype(endian % {
        # PCM is format 1.
        1: {8: 'u1', 16: 'i2', 32: 'i4'},
        # IEEE float is format 3.
        3: {16: 'f2', 32: 'f4', 64: 'f8'}
    }[audioformat][samplewidth]))
    if nchannels > 1:
        data = data.reshape((nchannels, -1))
    return data, samplerate


def _wav_write(file, data, sample_rate):
    # Generate a WAV header for this audio data and write it all to disk.
    data = np.asarray(data)
    assert data.ndim <= 2
    # We expect [channel, sample] ordering, but the data may be transposed.
    if data.ndim == 2:
        if data.shape[0] > data.shape[1]:
            data = data.transpose()
        channels = data.shape[0]
    else:
        channels = 1
    # For the time being we'll always write 16-bit integer samples, but in the
    # future it would be nice to retain whatever format we've been provided.
    wf = wave.open(file, 'wb')
    try:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(int(sample_rate))
        samples = (data * np.iinfo(np.int16).max).astype('<i2')
        wf.writeframesraw(samples.tobytes())
        wf.writeframes('')
    finally:
        wf.close()


def _execpipe(*args):
    pipe = subprocess.PIPE
    proc = subprocess.Popen(args, stdin=pipe, stdout=pipe, stderr=pipe)
    output, _ = proc.communicate()
    retcode = proc.returncode
    if retcode:
        raise subprocess.CalledProcessError(retcode, args, output=output)
    return output


def _subproc_read(*args):
    # convert the input file to a temporary wav file
    # read in the contents of the temp and return that
    fd, temp = tempfile.mkstemp(suffix='.wav')
    try:
        args = list(args) + [temp]
        _execpipe(*args)
        return _wav_read(temp)
    finally:
        os.close(fd)
        os.remove(temp)
