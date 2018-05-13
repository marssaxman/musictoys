"""audiofile reads audio files, combing python libraries and external tools"""

import collections
import os
import subprocess
import tempfile
import soundfile
import struct
import wave
import numpy as np

from collections import namedtuple
Info = namedtuple('Info', 'format dtype samplerate channels')
Clip = namedtuple('Clip', 'data samplerate')
Format = namedtuple('Format', 'name description extensions')

FORMATS = {f.name: f for f in [
    Format('AAC', "Advanced Audio Coding", {'.aac'}),
    Format('AIFC', "", {'.aifc'}),
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


class lazy_property(object):
    """Decorator to create a lazily evaluated, memoized property.

    The target function will be invoked on its first access, then replaced
    with its result value and never executed again.
    """

    def __init__(self, function):
        # Save the function and its name.
        self.function = function
        self.name = function.__name__

    def __get__(self, obj, cls):
        if obj is None:
            return None
        # Evaluate the function, passing in 'obj', which will become 'self'
        # while the function is evaluating.
        value = self.function(obj)
        # Replace this property with the value we just generated, so that
        # the decorator instance disappears and it becomes a normal attribute.
        setattr(obj, self.name, value)
        return value


def execpipe(*args):
    pipe = subprocess.PIPE
    proc = subprocess.Popen(args, stdin=pipe, stdout=pipe, stderr=pipe)
    output, _ = proc.communicate()
    retcode = proc.returncode
    if retcode:
        raise subprocess.CalledProcessError(retcode, args, output=output)
    return output


class FormatError(Exception):
    def __init__(self, message, format=None):
        super(FormatError, self).__init__(message)
        self.format = format


class SubtypeError(Exception):
    def __init__(self, message, subtype=None):
        super(SubtypeError, self).__init__(message)
        self.subtype = subtype


class Codec(object):
    """Base class for objects which read, write, and identify sound files."""

    def __init__(self):
        pass

    def formats(self):
        return []

    def read(self, file):
        if os.path.isfile(file):
            raise FormatError("Cannot read %s" % file)
        else:
            raise FileNotFoundError(file)

    def write(self, file, clip):
        dtype = clip.data.dtype
        raise FormatError("Cannot write '%s' to %s" % (dtype, file))

    def info(self, file):
        if os.path.isfile(file):
            raise FormatError("Cannot inspect %s" % (file))
        else:
            raise FileNotFoundError(file)


class Soundfile(Codec):

    def __init__(self):
        super(Soundfile, self).__init__()

    def formats(self):
        # Get a list of the formats supported by the soundfile lib.
        names = soundfile.available_formats().iterkeys()
        return [FORMATS[n] for n in names if n in FORMATS]

    def read(self, file):
        data, samplerate = soundfile.read(file)
        return Clip(data, samplerate)

    def write(self, file, clip):
        data, samplerate = clip
        soundfile.write(file, data, samplerate)

    def info(self, file):
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


class Ffmpeg(Codec):

    def __init__(self):
        super(Ffmpeg, self).__init__()

    def formats(self):
        output = execpipe('ffmpeg', '-formats')
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

    def read(self, file):
        try:
            fd, temp = tempfile.mkstemp(suffix='.wav')
            execpipe('ffmpeg', '-v', '1', '-y', '-i', file, temp)
            return soundfile.read(temp)
        finally:
            os.close(fd)
            os.remove(temp)


class Afconvert(Codec):
    apple_aliases = {
        'adts': 'AAC', 'm4af': 'M4A', 'm4bf': 'M4B', 'caff': 'CAF',
        'MPG1': 'MP1', 'MPG2': 'MP2', 'MPG3': 'MP3', 'mp4f': 'MP4',
        'WAVE': 'WAV',
    }

    def __init__(self):
        super(Afconvert, self).__init__()

    def formats(self):
        fmts = []
        try:
            output = execpipe('afconvert', '--help-formats')
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

    def read(self, file):
        # use ffmpeg to convert the input file to a temporary wav file we can read
        try:
            fd, temp = tempfile.mkstemp(suffix='.wav')
            execpipe('afconvert', '-d', 'LEI16', '-f', 'WAVE', file, temp)
            return soundfile.read(temp)
        finally:
            os.close(temp)
            os.remove(temp)


class Wave(Codec):

    def __init__(self):
        super(Wave, self).__init__()

    def formats(self):
        return [FORMATS['WAV']]

    def read(self, file):
        # Python's WAV API can tell us the sample width, but can't tell us
        # whether it is big or little endian, integer or float; we'll read the
        # WAV file header ourselves first to figure that out.
        with open(file, 'rb') as fp:
            riffstruct = "<4sI4s"
            bytes = fp.read(struct.calcsize(riffstruct))
            ChunkID, ChunkSize, Format = struct.unpack(riffstruct, bytes)
            if ChunkID == 'RIFF' and Format == 'WAVE':
                endian = "<"
            elif ChunkID == 'FFIR' and Format == 'EVAW':
                endian = ">"
            else:
                raise ValueError()
            wavstruct = endian + "4sIHHIIHH"
            bytes = fp.read(struct.calcsize(wavstruct))
            (
                Subchunk1ID, Subchunk1Size, AudioFormat, NumChannels,
                SampleRate, ByteRate, BlockAlign, BitsPerSample
            ) = struct.unpack(wavstruct, bytes)

        dtype = np.dtype(endian + {
            # PCM is format 1.
            1: {8: 'u1', 16: 'i2', 24: 'i3', 32: 'i4'},
            # IEEE float is format 3.
            3: {16: 'f2', 32: 'f4', 64: 'f8'}
        }[AudioFormat][BitsPerSample])

        try:
            wp = wave.open(file, 'rb')
            nchannels, _, samplerate, nframes, _, _ = wp.getparams()
            frames = wp.readframes(nframes * nchannels)
            data = np.fromstring(frames, dtype=dtype)
            if nchannels > 1:
                data = data.reshape((nchannels, nframes))
            return data, samplerate
        finally:
            wp.close()


class Dispatch(Codec):
    """Wrapper which distributes requests to a list of codec implementations.

    Each codec is expected to provide a list of formats it supports, and each
    format must supply a list of file extensions which might represent it.
    """

    def __init__(self, codec_classes):
        super(Dispatch, self).__init__()
        self._codec_classes = codec_classes
        self._formats = None
        self._extensions = None

    def formats(self):
        if self._formats:
            return self._formats
        self._formats = dict()
        # Attempt to instantiate each codec and query it. Some will fail,
        # because they are not supported on the current platform.
        for cls in self._codec_classes:
            try:
                codec = cls()
                self._formats.update({f.name: codec for f in codec.formats()})
            except:
                pass
        return self._formats

    def extensions(self):
        if self._extensions:
            return self._extensions
        self._extensions = dict()
        # Build a table mapping file extensions to the codecs supporting them.
        for fmtname, codec in self.formats().iteritems():
            fmt = FORMATS[fmtname]
            for ext in FORMATS[fmtname].extensions:
                self._extensions[ext] = codec
        return self._extensions

    def read(self, file):
        ext = os.path.splitext(file)[1].lower()
        codec = extensions().get(ext)
        return codec.read(file) if codec else super(Codec, self).read(file)

    def write(self, file, clip):
        ext = os.path.splitext(file)[1].lower()
        codec = extensions().get(ext)
        if codec:
            codec.write(file, clip)
        else:
            super(Codec, self).write(file, clip)


_dispatch = Dispatch([Ffmpeg, Afconvert, Soundfile, Wave])


def formats():
    return _dispatch.formats()


def extensions():
    return _dispatch.extensions()


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
    return _dispatch.read(file)


def write(file, (data, samplerate)):
    _dispatch.write(file, (data, samplerate))


def info(file):
    return dispatch.info(file)
