"""
A `Source` is where a `Form` by *computes*, i.e.:

- resolves (see `Field._resolve`)
- parses (see `Field._parse`)

values from. There is a `DefaultSource` which is used to talk to native
containers:

- dicts
- lists
- tuples

and primitives (e.g. int, basestring, etc). There are also `Source`
specializations for *computing* values from serializations:

- `JsonSource`
- `ConfigSource`
- ...

There's also `UnionSource` which unions a collection of `Source`s.
"""
import collections
import inspect

from .. import NONE, NOT_SET

__all__ = [
    'SourceError',
    'Path',
    'Source',
    'DefaultSource',
    'UnionSource',
    'JsonSource',
    'ConfigSource',
]


class SourceError(Exception):
    """
    Base class for all `Source` errors.
    """

    def __init__(self, path, message):
        super(SourceError, self).__init__(message)
        self.path = path
        self.message = message


class PathPart(object):

    def __init__(self, key, value=NOT_SET):
        self.key = key
        self.value = NOT_SET

    def __str__(self):
        return str(self.key)


class Path(collections.MutableSequence):
    """
    Represents a path to a `Field` within a `Source`.

    `src`

    `root`

    `location`

    """

    def __init__(self, src, root, location=None):
        self.src = src
        self.root = root
        self.location = location
        self.parts = []

    def __str__(self):
        parts = []
        if self:
            parts = ['{0}'.format(self[0])]
            for part in self[1:]:
                if isinstance(part.key, (int, long)):
                    part = '[{0}]'.format(part.key)
                else:
                    part = '.' + part.key
                parts.append(part)
        return ''.join(parts)

    @property
    def value(self):
        if self.parts and self.parts[-1].value is not NOT_SET:
            return self.parts[-1].value

        for i, part in enumerate(reversed(self.parts)):
            if part.value is not NOT_SET:
                i, value = len(self.parts) - i, part.value
                break
        else:
            i, value = 0, self.root

        for part in self.parts[i:]:
            value = part.value = self.resolve(value, part)
            if value is NONE:
                break

        return value

    @value.setter
    def value(self, obj):
        if not self.parts:
            self.root = obj
        else:
            self[-1].value = obj

    def resolve(self, container, part):
        raise NotImplementedError()

    @property
    def name(self):
        return self[-1].key

    @property
    def exists(self):
        return self.value is not NONE

    @property
    def is_null(self):
        return self.value is None

    def primitive(self, *types):
        return self.src.primitive(self, *types)

    def sequence(self):
        return self.src.sequence(self)

    def mapping(self):
        return self.src.mapping(self)

    # collections.Sequence

    def __getitem__(self, index):
        return self.parts[index]

    def __len__(self):
        return len(self.parts)

    # collections.MutableSequence

    def __setitem__(self, index, value):
        if isinstance(value, (long, int, basestring)):
            value = PathPart(key=value)
        self.parts[index] = value

    def __delitem__(self, index):
        del self.parts[index]

    def insert(self, index, value):
        if isinstance(value, (long, int, basestring)):
            value = PathPart(key=value)
        self.parts.insert(index, value)


class Source(object):
    """
    Interface for creating paths and resolving them to primitives:

        - string
        - integer
        - float

    and optionally containers:

        - sequence
        - mapping

    within a source (e.g. MIME string, ConfigParser object, etc).
    """

    #: Used to construct an error when resolving a path for this source fails.
    error = SourceError

    def path(self):
        """
        Constructs a root path for this source.
        """
        raise NotImplementedError()

    def mapping(self, path):
        """
        Resolves a path to a mapping within this source.
        """
        raise NotImplementedError('{0} does not support mappings!'.format(type(self)))

    def sequence(self, path):
        """
        Resolves a path to a sequence within this source.
        """
        raise NotImplementedError('{0} does not support sequences!'.format(type(self)))

    def primitive(self, path, *types):
        """
        Resolves a path to a primitive within this source. If no type is given
        then it'll be inferred if possible.
        """
        raise NotImplementedError('{0} does not support primitives!'.format(type(self)))


class ParserMixin(object):
    """
    Mixin for adding simple parsing capabilities to a `Source`.
    """

    def as_string(self, path, value):
        if isinstance(value, basestring):
            return value
        raise self.error(path, '"{0}" is not a string'.format(value))

    def as_int(self, path, value):
        if isinstance(value, (int, long)) and not isinstance(value, bool):
            pass
        elif isinstance(value, float):
            if not value.is_integer():
                raise self.error(path, '"{0}" is not an integer'.format(value))
            else:
                value = int(value)
        elif isinstance(value, basestring):
            try:
                value = int(value)
            except (ValueError, TypeError):
                raise self.error(path, '"{0}" is not an integer'.format(value))
        else:
            raise self.error(path, '"{0}" is not an integer'.format(value))
        return value

    def as_float(self, path, value):
        if isinstance(value, (float)):
            pass
        elif isinstance(value, (int, long)):
            value = float(value)
        elif isinstance(value, basestring):
            try:
                value = float(value)
            except (ValueError, TypeError):
                raise self.error(path, '"{0}" is not a float'.format(value))
        else:
            raise self.error(path, '"{0}" is not a float'.format(value))
        return value

    def as_bool(self, path, value):
        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            return value != 0
        if isinstance(value, basestring):
            if value.lower() in ('0', 'f', 'false'):
                return False
            elif value.lower() in ('1', 't', 'true'):
                return True
        raise self.error(path, '"{0}" is not a boolean'.format(value))

    def as_auto(self, path, value):
        return value

    parsers = {
        basestring: as_string,
        int: as_int,
        float: as_float,
        bool: as_bool,
        None: as_auto,
    }

    def parser(self, types, default=NONE):
        if not types:
            types = [None]
        if not isinstance(types, (tuple, list)):
            types = [types]
        for t in types:
            if t in self.parsers:
                return self.parsers[t]
            for mro_t in inspect.getmro(t):
                if mro_t in self.parsers:
                    self.parsers[t] = self.types[mro_t]
                    return self.parsers[t]
        if default is not NONE:
            return default
        raise ValueError('No parser for type(s) {0}'.format(types))


from .default import DefaultSource, DefaultPath
from .configparser import ConfigSource, ConfigPath
from .json import JsonSource, JsonPath
from .union import UnionSource, UnionSource as union, UnionPath
from .mount import MountSource, MountSource as mount, MountPath
