import collections

from . import Path, PathPart, Source, NONE, DefaultSource


class UnionPath(Path):

    def __init__(self, src, paths, merge=None):
        super(UnionPath, self).__init__(
            src, root=Mapping(src, paths, merge)
        )
        self.paths = paths
        prefix_len = set([len(path) for path in paths])
        if len(prefix_len) != 1:
            raise ValueError('All paths must have equal length')
        prefix_len = list(prefix_len)[0]
        if prefix_len:
            prefix = set([
                tuple(part.key for part in path[:prefix_len])
                for path in paths
            ])
            if len(prefix) != 1:
                raise ValueError('All paths must have same keys')
            prefix = list(prefix)[0]
            self.parts.extend([PathPart(key=key) for key in prefix])

    # Path

    @property
    def is_null(self):
        if super(UnionPath, self).is_null:
            return True
        if isinstance(self.value, Mapping):
            return len(self.value.mappings) == 0
        if isinstance(self.value, Sequence):
            return len(self.value.sequences) == 0
        return False

    def resolve(self, container, part):
        try:
            return container[part.key]
        except (IndexError, KeyError, TypeError):
            return NONE

    # collections.MutableSequence

    def __setitem__(self, index, value):
        super(UnionPath, self).__setitem__(index, value)
        if isinstance(value, PathPart):
            value = value.key
        for path in self.paths:
            path[index] = value

    def __delitem__(self, index):
        super(UnionPath, self).__delitem__(index)
        for path in self.paths:
            del path[index]

    def insert(self, index, value):
        super(UnionPath, self).insert(index, value)
        if isinstance(value, PathPart):
            value = value.key
        for path in self.paths:
            path.insert(index, value)


class UnionSource(Source):

    def __init__(self,
                 srcs,
                 merge='first',
                 mapping_merge=None,
                 sequence_merge=None,
                 merge_depth=None,
        ):
        super(UnionSource, self).__init__()
        for i, src in enumerate(srcs):
            if isinstance(src, Source):
                continue
            if isinstance(src, collections.Mapping):
                src = DefaultSource(src)
            else:
                raise TypeError(
                   'src[{0}]={1!r} is not Source or mapping'.format(i, src)
                )
            srcs[i] = src

        self.srcs = srcs
        self.mapping_merge = mapping_merge or merge
        self.sequence_merge = sequence_merge or merge
        self.merge_depth = merge_depth

    # Source

    def path(self):
        return UnionPath(self, [s.path() for s in self.srcs], merge='combine')

    def mapping(self, path):
        if isinstance(path.value, Join):
            path.value = path.value.mapping()
        if isinstance(path.value, Mapping):
            return path.value.keys()
        raise self.error(path, 'not a mapping')

    def sequence(self, path):
        if isinstance(path.value, Join):
            path.value = path.value.sequence()
        if isinstance(path.value, Sequence):
            return len(path.value)
        raise self.error(path, 'not a sequence')

    def primitive(self, path, *types):
        if isinstance(path.value, Join):
            path.value = path.value.primitive(*types)
        return path.value


class Join(Source):

    def __init__(self, src, paths):
        self.src = src
        self.paths = paths

    def mapping(self):
        return Mapping(self.src, self.paths)

    def sequence(self):
        return Sequence(self.src, self.paths)

    def primitive(self, *types):
        if not self.paths:
            return NONE
        return self.paths[0].primitive(*types)

    # Source

    def path(self):
        path = UnionPath(self.src, self.paths, None)
        path[-1].value = self
        return path


class Mapping(collections.Mapping):

    def __init__(self, src, paths, merge=None):
        mappings = []
        if merge is None:
            merge = src.mapping_merge
            if src.merge_depth is not None and src.merge_depth <= len(path):
                merge = 'first'
        if merge not in ('first', 'last', 'combine'):
            raise ValueError('merge="{0}" invalid'.format(merge))
        for path in paths:
            if not path.exists:
                continue
            if merge == 'first':
                if not path.is_null:
                    keys = path.mapping()
                    mappings.append((path, keys))
                break
            if path.is_null:
                continue
            keys = path.mapping()
            if not mappings:
                mappings.append((path, keys))
                continue
            if merge == 'combine':
                mappings.append((path, keys))
            elif merge == 'last':
                mappings = [(path, keys)]
        self.src = src
        self.mappings = mappings

    # collections.Mapping

    def __getitem__(self, key):
        paths = []
        for path, keys in self.mappings:
            if key in keys:
                paths.append(path)
        if not paths:
            raise KeyError(key)
        return Join(self.src, paths)

    def __len__(self):
        keys = (key for _, mapping in self.mappings for key in mapping)
        return len(list(set(keys)))

    def __iter__(self):
        keys = (key for _, mapping in self.mappings for key in mapping)
        return iter(list(set(keys)))


class Sequence(collections.Sequence):

    def __init__(self, src, paths, merge=None):
        sequences = []
        for path in paths:
            if not path.exists or path.is_null:
                continue
            length = path.sequence()
            if not sequences:
                sequences.append((path, length))
                continue
            if merge is None:
                merge = src.sequence_merge
                if src.merge_depth is not None and src.merge_depth <= len(path):
                    merge = 'first'
            if merge == 'combine':
                sequences.append((path, length))
            elif merge == 'first':
                pass
            elif merge == 'last':
                sequences[0] = (path, length)
            else:
                raise ValueError('merge="{1}" invalid'.format(merge))
        self.src = src
        self.sequences = sequences

    # collections.Sequence

    def __getitem__(self, key):
        offset = 0
        for path, length in self.sequences:
            if key < offset + length:
                break
            offset += length
        else:
            raise IndexError(key)
        path[-1].key -= offset
        return Join(self.src, [path])

    def __len__(self):
        return sum(length for _, length in self.sequences)
