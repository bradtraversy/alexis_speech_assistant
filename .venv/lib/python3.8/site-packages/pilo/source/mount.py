import collections

from . import PathPart, Source, NONE, DefaultSource


class MountPath(collections.MutableSequence):

    def __init__(self, src):
        self.part = None
        self.dne = DefaultSource({}).path()
        self.paths = dict(
            (key, src.path()) for key, src in src.srcs.iteritems()
        )

    @property
    def path(self):
        return self.paths.get(self.part.key, self.dne) if self.part else None

    @property
    def parts(self):
        if self.part is None:
            return []
        if self.path is None:
            return [self.part]
        return [self.part] + self.path.parts

    def __str__(self):
        if self.part is None:
            return ''
        if self.path is None or len(self.path) == 0:
            return '@{0}'.format(str(self.part))
        return '@{0}:{1}'.format(self.part, self.path)

    @property
    def value(self):
        if self.path is None:
            return NONE
        return self.path.value

    @value.setter
    def value(self, obj):
        self.path.value = obj

    @property
    def name(self):
        return self[-1].key

    @property
    def exists(self):
        if self.part is None:
            return True
        return self.value is not NONE

    @property
    def is_null(self):
        if self.part is None:
            return False
        return self.value is None

    def primitive(self, *types):
        if self.part is None:
            raise self.error(self, 'not a primitive')
        return self.paths[self.part.key].primitive(*types)

    def sequence(self):
        if self.part is None:
            raise self.error(self, 'not a sequence')
        return self.paths[self.part.key].sequence()

    def mapping(self):
        if self.part is None:
            return self.paths.keys()
        return self.path.mapping()

    # collections.Sequence

    def __getitem__(self, index):
        return self.parts[index]

    def __len__(self):
        return len(self.parts)

    # collections.MutableSequence

    def __setitem__(self, index, value):
        if isinstance(value, (long, int, basestring)):
            value = PathPart(key=value)
        if index < 0:
            index = len(self) + index
        if index == 0:
            self.part = value
        else:
            self.path[index - 1] = value

    def __delitem__(self, index):
        if self.part is None:
            raise IndexError()
        if index < 0:
            index = len(self) + index
        if index == 0:
            if self.path is not None and len(self.path) > 0:
                raise TypeError('Cannot delete mount point')
            self.part = None
            return
        if self.path is None:
            raise IndexError()
        del self.path[index - 1]

    def insert(self, index, value):
        if isinstance(value, (long, int, basestring)):
            value = PathPart(key=value)
        if index < 0:
            index = len(self) + index
        if index == 0:
            self.part = value
        else:
            self.path.insert(index - 1, value)


class MountSource(Source):

    def __init__(self, **srcs):
        for key, src in srcs.items():
            if isinstance(src, Source):
                continue
            if isinstance(src, dict) or src is None:
                srcs[key] = DefaultSource(src)
                continue
            raise TypeError(
                '{0}={1!r} is not None, dict or Source'.format(key, src)
            )
        super(MountSource, self).__init__()
        self.srcs = srcs

    # Source

    def path(self):
        return MountPath(self)

    def mapping(self, path):
        return self.srcs.keys()
