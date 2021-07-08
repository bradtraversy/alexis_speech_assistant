from __future__ import absolute_import

import inspect
import json

from . import Source, Path, NONE


class JsonPath(Path):

    # Path

    def __init__(self, src, location=None):
        super(JsonPath, self).__init__(src, src.data, location=location)

    def __str__(self):
        parts = []
        if self.location:
            parts.append(self.location)
        parts.append(super(JsonPath, self).__str__())
        return ':'.join(parts)

    def resolve(self, container, part):
        try:
            if not isinstance(part.key, basestring) or '.' not in part.key:
                return container[part.key]
            value = container
            for atom in part.key.split('.'):
                value = value[atom]
            return value
        except (IndexError, KeyError, TypeError):
            return NONE


class JsonSource(Source):

    def __init__(self, text, encoding=None, strict=False, location=None):
        super(Source, self).__init__()
        self.strict = strict
        self.location = location
        self.text = text
        self.data = json.loads(text, encoding=encoding)

    def as_string(self, field, value):
        if isinstance(value, basestring):
            return value
        if not self.strict:
            return str(value)
        raise self.error(field, '{0} is not a string'.format(value))

    def as_int(self, field, value):
        if isinstance(value, (int, long)) and not isinstance(value, bool):
            return value
        if not self.strict:
            if isinstance(value, float):
                if value.is_integer():
                    return int(value)
            elif isinstance(value, basestring):
                try:
                    return int(value)
                except ValueError:
                    pass
        raise self.error(field, '{0} is not an integer'.format(value))

    def as_float(self, field, value):
        if isinstance(value, (float)):
            return value
        if isinstance(value, (int, long)):
            return float(value)
        if not self.strict:
            if isinstance(value, basestring):
                try:
                    return float(value)
                except ValueError:
                    pass
        raise self.error(field, '{0} is not a float'.format(value))

    def as_bool(self, field, value):
        if isinstance(value, bool):
            return value
        if not self.strict:
            if isinstance(value, int):
                return value != 0
        raise self.error(field, '{0} is not a boolean'.format(value))

    def as_auto(self, field, value):
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

    # Source

    def path(self):
        return JsonPath(self, self.location)

    def sequence(self, path):
        if not isinstance(path.value, (list, tuple)):
            raise self.error(path, 'not a sequence')
        return len(path.value)

    def mapping(self, path):
        if not isinstance(path.value, (dict,)):
            raise self.error(path, 'not a mapping')
        return path.value.keys()

    def primitive(self, path, *types):
        return self.parser(types)(self, path, path.value)
