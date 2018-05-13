"""audiofile reads audio files, combing python libraries and external tools"""

import collections
import os
import subprocess
import tempfile
import soundfile
import struct
import numpy as np

from collections import namedtuple
Info = namedtuple('Info', 'format dtype samplerate channels')
Clip = namedtuple('Clip', 'data samplerate')
Format = namedtuple('Format', 'name description extensions')
_Codec = namedtuple('_Codec', 'formats read write info')

FORMATS = {f.name: f for f in [
    Format('AAC', "Advanced Audio Coding", {'.aac'}),
    Format('AIFC', "Compressed AIFF", {'.aifc'}),
    Format('AIFF', "Audio IFF", {'.aiff'}),
    Format('AU', "Sun AU", {'.au'}),
    Format('AVI', "Audio Video Interlaced", {'.avi'}),
    Format('CAF', "Apple Core Audio Format", {'.caf'}),
    Format('FLAC', "FLAC", {'.flac'}),
    Format('M4A', "MPEG-4 Audio Lossless", {'.m4a', '.m4r'}),
    Format('M4B', "MPEG-4 Audio Books", {'.m4b'}),
    Format('MP2', "MPEG audio layer 2", {'.mp2'}),
    Format('MP3', "MPEG audio layer 3", {'.mp3'}),
    Format('MP4', "MPEG-4 Part 14", {'.mp4'}),
    Format('OGG', "Ogg", {'.ogg'}),
    Format('OGA', "Ogg Audio", {'.oga'}),
    Format('MOGG', "Multitrack Ogg", {'.mogg'}),
    Format('OPUS', "Ogg Opus", {'.opus'}),
    Format('WAV', "Waveform Audio", {'.wav'}),
    Format('WEBM', "WebM", {'.webm'}),
    Format('WMA', "Windows Media Audio", {'.wma'}),
]}


class FormatError(Exception):
    def __init__(self, message, format=None):
        super(FormatError, self).__init__(message)
        self.format = format


def _execpipe(*args):
    pipe = subprocess.PIPE
    proc = subprocess.Popen(args, stdin=pipe, stdout=pipe, stderr=pipe)
    output, _ = proc.communicate()
    retcode = proc.returncode
    if retcode:
        raise subprocess.CalledProcessError(retcode, args, output=output)
    return output


def _fail_formats():
    return []


def _fail_read(file):
    if os.path.isfile(file):
        raise FormatError("Cannot read %s" % file)
    else:
        raise FileNotFoundError(file)


def _fail_write(file, clip):
    dtype = clip.data.dtype
    raise FormatError("Cannot write '%s' to %s" % (dtype, file))


def _fail_info(file):
    if os.path.isfile(file):
        raise FormatError("Cannot inspect %s" % (file))
    else:
        raise FileNotFoundError(file)


def _soundfile_formats():
    # Get a list of the formats supported by the soundfile lib.
    names = soundfile.available_formats().iterkeys()
    return [FORMATS[n] for n in names if n in FORMATS]


def _soundfile_read(file):
    data, samplerate = soundfile.read(file)
    # soundfile returns [frames, channels] which is contrary to numpy
    # conventions, so we'll transpose the output if necessary
    return data.transpose(), samplerate


def _soundfile_write(file, clip):
    data, samplerate = clip
    soundfile.write(file, data, samplerate)


def _soundfile_info(file):
    info = soundfile.info(file)
    return Info(
        name=info.name,
        format=info.format,
        dtype=info.subtype,
        samplerate=info.samplerate,
        channels=info.channels,
        length=info.frames,
        duration=info.frames / float(info.samplerate)
    )


_Soundfile = _Codec(
    _soundfile_formats, _soundfile_read, _soundfile_write, _soundfile_info)


def _ffmpeg_formats():
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


def _ffmpeg_read(file):
    try:
        fd, temp = tempfile.mkstemp(suffix='.wav')
        _execpipe('ffmpeg', '-v', '1', '-y', '-i', file,
                '-vn', '-f', 'wav', temp)
        return _wav_read(temp)
    finally:
        os.close(fd)
        os.remove(temp)


_Ffmpeg = _Codec(
    _ffmpeg_formats, _ffmpeg_read, _fail_write, _fail_info)


def _afconvert_formats():
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
            name = Afconvert.apple_aliases.get(name, name)
            fmt = FORMATS.get(name)
            if fmt:
                fmts.append(fmts)
    return fmts


def _afconvert_read(file):
    # use ffmpeg to convert the input file to a temporary wav file we can read
    try:
        fd, temp = tempfile.mkstemp(suffix='.wav')
        _execpipe('afconvert', '-d', 'LEI16', '-f', 'WAVE', file, temp)
        return _wav_read(temp)
    finally:
        os.close(temp)
        os.remove(temp)


_Afconvert = _Codec(
    _afconvert_formats, _afconvert_read, _fail_write, _fail_info)


def _wav_formats():
    return [FORMATS['WAV']]


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
        return struct.unpack(endian%fmt, bytes)
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


_Wav = _Codec(_wav_formats, _wav_read, _fail_write, _fail_info)


_formats = None
_extensions = None
def _init():
    global _formats, _extensions
    if not _formats:
        _formats = dict()
        # Attempt to instantiate each codec and query it. Some will fail,
        # because they are not supported on the current platform.
        for codec in [_Ffmpeg, _Afconvert, _Soundfile, _Wav]:
            try:
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


def formats():
    _init()
    global _formats
    return _formats.keys()


def extensions():
    _init()
    global _extensions
    return _extensions.keys()


def read(file):
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

    return Clip(*_dispatch(file).read(file))


def write(file, clip):
    _dispatch(file).write(file, clip)


def info(file):
    return _dispatch(file).info(file)

