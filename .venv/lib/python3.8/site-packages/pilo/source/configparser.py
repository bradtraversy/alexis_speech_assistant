import collections
import ConfigParser
import re
import shlex
import StringIO
import textwrap

from . import Source, Path, ParserMixin, NONE


class ConfigPath(Path):

    # Path

    def __init__(self, src):
        if src.section:
            root = SectionMapping(src.config, src.section, src.defaults)
        else:
            root = Mapping(src.config, src.defaults)
        super(ConfigPath, self).__init__(src, root, src.location)
        self.section = src.section

    def __str__(self):
        parts = []
        if self.location:
            parts.append(self.location)
        if self.section:
            parts.append('[{0}]'.format(self.section))
        parts.append(super(ConfigPath, self).__str__())
        return ':'.join(parts)

    def resolve(self, container, part):
        try:
            if isinstance(container, basestring):
                container = Sequence(container)
            return container[part.key]
        except (KeyError, IndexError, TypeError):
            return NONE


class Sequence(collections.Sequence):

    def __init__(self, value):
        if '\n' in value:
            self.values = [
                line.strip() for line in value.splitlines() if line.strip()
            ]
        else:
            self.values = shlex.split(value)

    def __getitem__(self, i):
        return self.values[i]

    def __len__(self):
        return len(self.values)


class SectionMapping(collections.Mapping):

    def __init__(self, config, section, defaults):
        self.config = config
        self.section = section
        pattern = r'(?P<name>[\w\_]+)\[(?P<key>[\w\_\-\.]+)\]'
        self.defaults = defaults
        self.sub_mappings = collections.defaultdict(dict)
        for option, value in self.config.items(section):
            m = re.match(pattern, option)
            if not m:
                continue
            self.sub_mappings[m.group('name')][m.group('key')] = value

    def __getitem__(self, key):
        if key in self.sub_mappings:
            return self.sub_mappings[key]
        if self.config.has_option(self.section, key):
            return self.config.get(self.section, key)
        if key in self.defaults:
            return self.defaults[key]
        raise KeyError(key)

    def __iter__(self):
        for k, v in self.sub_mappings.iteritems():
            yield k
        for k, v in self.config.items(self.section):
            yield k

    def __len__(self):
        return len(self.sub_mappings) + len(self.config.options(self.section))


class Mapping(collections.Mapping):

    def __init__(self, config, defaults=None):
        self.config = config
        self.defaults = defaults

    def __getitem__(self, key):
        if not self.config.has_section(key):
            raise KeyError(key)
        return SectionMapping(self.config, key, self.defaults.get(key, None))

    def __iter__(self):
        for section in self.config.sections():
            yield section

    def __len__(self):
        return len(self.config.sections())


class ConfigSource(Source, ParserMixin):

    @classmethod
    def from_file(cls, path, *args, **kwargs):
        kwargs['location'] = path
        with open(path, 'r') as fo:
            return cls(fo.read(), *args, **kwargs)

    def __init__(self,
                 config,
                 section=None,
                 location=None,
                 defaults=None,
                 preserve_whitespace=False,
                 preserve_case=False,
        ):
        super(ConfigSource, self).__init__()
        if preserve_whitespace and location is None:
            raise ValueError('preserve_white_space=True without location')
        if preserve_case and not isinstance(config, basestring):
            raise ValueError('preserve_case=True but config is not string')
        if isinstance(config, basestring):
            parser = ConfigParser.ConfigParser()
            if preserve_case:
                config.optionxform = lambda x: x
            parser.readfp(StringIO.StringIO(config))
            config = parser
        self.config = config
        self.section = section
        self.location = location
        self.defaults = defaults
        self.preserve_whitespace = preserve_whitespace

    def as_raw(self, path):
        option = str(path[-1])
        lines = []
        with open(self.location, 'r') as fo:
            section_header = '[{0}]'.format(self.section)
            for line in fo:
                if line.strip() == section_header:
                    break
            for line in fo:
                if line.strip().startswith(option):
                    break
            for line in fo:
                if line and not line[0].isspace():
                    break
                lines.append(line)
        return textwrap.dedent(''.join(lines))

    # Source

    def path(self):
        return ConfigPath(self)

    def sequence(self, path):
        value = path.value
        if isinstance(value, basestring):
            return len(Sequence(value))
        if isinstance(value, collections.Sequence):
            return len(value)
        raise self.error(path, 'not a sequence')

    def mapping(self, path):
        if isinstance(path.value, collections.Mapping):
            return path.value.keys()
        raise self.error(path, 'not a mapping')

    def primitive(self, path, *types):
        value = self.parser(types)(self, path, path.value)

        # preserve white-space for mulit-line strings
        if (self.preserve_whitespace and
            isinstance(value, basestring) and
            value.count('\n') > 0):
            value = self.as_raw(path)

        return value
