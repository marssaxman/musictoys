"""audiofile reads audio files, combing python libraries and external tools"""

import collections
import os, subprocess
import tempfile
import soundfile

from collections import namedtuple
Info = namedtuple('Info', 'format dtype samplerate channels')
Clip = namedtuple('Clip', 'data samplerate')
Format = namedtuple('Format', 'name description subtypes extensions')


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
        if obj is None: return None
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
    def __init__(self, message, format):
        super(FormatError, self).__init__(message)
        self.format = format


class SubtypeError(Exception):
    def __init__(self, message, subtype):
        super(SubtypeError, self).__init__(message)
        self.subtype = subtype


class Codec(object):
    """Base class for objects which read, write, and identify sound files."""
    name = "unimplemented"

    def __init__(self):
        pass

    def read(self, file):
        if os.path.isfile(file):
            raise FormatError("Codec %s cannot read %s" % (self.name, file))
        else:
            raise FileNotFoundError(file)

    def write(self, file, clip):
        dtype = clip.data.dtype
        raise FormatError("Codec %s cannot write '%s'" % (self.name, dtype))

    def info(self, file):
        if os.path.isfile(file):
            raise FormatError("Codecx % cannot inspect %s" % (self.name, file))
        else:
            raise FileNotFoundError(file)


class Dispatch(Codec):
    """Wrapper which distributes requests to a list of codec implementations.

    Each codec is expected to provide a list of formats it supports, and each
    format must supply a list of file extensions which might represent it.
    """

    def __init__(self, codecs):
        super(Dispatch, self).__init__()
        self.codecs = codecs
        self.dispatch = dict()

    @lazy_property
    def formats(self):
        found = list()
        for codec in self.codecs:
            for fmt in codec.formats:
                if fmt.name in self.dispatch:
                    continue
                self.dispatch[fmt.name] = codec
                found.append(fmt)
        return found

    @lazy_property
    def extensions(self):
        return []


class Lib_soundfile(Codec):
    name = "soundfile"

    @lazy_property
    def formats(self):
        # Get a list of the formats supported by the soundfile lib.
        formats = list()
        for name, desc in soundfile.available_formats().iteritems():
            subtypes = soundfile.available_subtypes(name)
            formats.append(Format(name, desc, subtypes, '.' + name.lower()))
        return formats

    def read(self, file):
        data, samplerate = soundfile.read(file)
        return Clip(data, samplerate)

    def write(self, file, clip):
        data, samplerate = clip
        soundfile.write(file, data, samplerate)

    def info(self, file):
        info = soundfile.info(file)
        return Info(
            name = info.name,
            format = info.format,
            dtype = info.subtype,
            samplerate = info.samplerate,
            channels = info.channels,
            length = info.frames,
            duration = info.frames / float(info.samplerate)
        )


class Exec_ffmpeg(Codec):
    name = "ffmpeg"

    @lazy_property
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
            extension = "." + name.lower()
            description = " ".join(fields[2:])
            out.append(Format(name, description, (), []))
        return out

    def read(self, file):
        try:
            fd, temp = tempfile.mkstemp(suffix='.wav')
            execpipe('ffmpeg', '-v', '1', '-y', '-i', file, temp)
            return soundfile.read(temp)
        finally:
            os.close(fd)
            os.remove(temp)



class Exec_afconvert(Codec):
    name = "afconvert"

    @lazy_property
    def formats(self):
        try:
            output = execpipe('afconvert', '--help-formats')
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
        return []

    def read(self, file):
        # use ffmpeg to convert the input file to a temporary wav file we can read
        try:
            fd, temp = tempfile.mkstemp(suffix='.wav')
            execpipe('afconvert', '-d', 'LEI16', '-f', 'WAVE', file, temp)
            return soundfile.read(temp)
        finally:
            os.close(temp)
            os.remove(temp)


class Lib_wave(Codec):
    name = "wave"

    @lazy_property
    def formats(self):
        return []


_codecs = [Exec_ffmpeg(), Exec_afconvert(), Lib_soundfile(), Lib_wave()]
_dispatch = Dispatch(_codecs)


def formats():
    return _dispatch.formats


def extensions():
    return _dispatch.extensions


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







