import collections
import copy

from . import Source, Path, ParserMixin, NONE


class DefaultPath(Path):

    def _resolve(self, container, atom):
        if self.src.ignore(self):
            return NONE
        value = self._as_item(container, atom)
        if value is not NONE:
            return value
        value = self._as_alias(container, atom)
        if value is not NONE:
            return value
        return self._as_attr(container, atom)

    def _as_item(self, container, atom):
        try:
            return container[atom]
        except (IndexError, KeyError, TypeError):
            return NONE

    def _as_alias(self, container, atom):
        if (self.src.aliases and
            atom in self.src.aliases and
            len(self) == 1):
            alias = self.src.aliases[atom]
            return self._as_item(container, alias)
        return NONE

    def _as_attr(self, container, atom):
        if isinstance(atom, basestring):
            try:
                return getattr(container, atom)
            except (AttributeError, TypeError):
                return NONE
        return NONE

    # Path

    def __init__(self, src, location=None):
        super(DefaultPath, self).__init__(src, src.data, location)

    def __str__(self):
        parts = []
        if self.location:
            parts.append(self.location)
        parts.append(super(DefaultPath, self).__str__())
        return ':'.join(parts)

    def resolve(self, container, part):
        if isinstance(part.key, basestring) and part.key.endswith('()'):
            part = copy.copy(part)
            part.key = part.key[:-2]
            value = self.resolve(container, part)
            if value is NONE:
                return NONE
            return value()

        if isinstance(part.key, basestring):
            value = self._resolve(container, part.key)
            if value is NONE:
                value = container
                for atom in part.key.split('.'):
                    value = self._resolve(value, atom)
                    if value is NONE:
                        break
        else:
            value = self._resolve(container, part.key)
        return value


class DefaultSource(Source, ParserMixin):

    def __init__(self, data, aliases=None, ignores=None, location=None):
        self.data = data
        self.aliases = aliases
        self.ignores = None
        if ignores:
            self.ignores = [ignore.split('.') for ignore in ignores]
        self.location = location

    def ignore(self, path):
        if not self.ignores:
            return False
        return [part.key for part in path] in self.ignores

    # Source

    def path(self):
        return DefaultPath(self, self.location)

    def sequence(self, path):
        if isinstance(path.value, (collections.Sequence, list, tuple)):
            return len(path.value)
        raise self.error(path, 'is not a sequence')

    def mapping(self, path):
        if isinstance(path.value, (collections.Mapping, dict)):
            if self.aliases and len(path) == 0:
                return self.aliases.keys()
            return path.value.keys()
        if (isinstance(path.value, (collections.Sequence, list, tuple)) and
            self.aliases and
            len(path) == 0):
            return self.aliases.keys()
        raise self.error(path, 'is not a mapping')

    def primitive(self, path, *types):
        return self.parser(types)(self, path, path.value)
