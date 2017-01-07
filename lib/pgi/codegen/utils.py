# Copyright 2012 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import sys
import string
import collections

from pgi import _compat


class TypeTagRegistry(dict):

    def register(self, type_tag):
        def wrap(cls):
            assert type_tag not in self
            self[type_tag] = cls
            return cls
        return wrap

    def get_type(self, type_):
        tag_value = type_.tag.value
        if tag_value in self:
            return self[tag_value].get_class(type_)
        raise LookupError("type: %r", type_.tag)


class VariableFactory(object):
    """A callable the produces unique variable names"""

    def __init__(self, blacklist=None):
        self._count = 0
        self._blacklist = set()
        self._obj_cache = {}
        if blacklist:
            self.add_blacklist(blacklist)

    def add_blacklist(self, seq):
        """seq is a sequence of names to reserve"""

        self._blacklist.update(seq)

    def __call__(self, *args):
        """Get a random new name, pass an obj to get a cached one"""

        if not args:
            self._count += 1
            res = "t%d" % self._count
        else:
            obj = args[0]
            try:
                # use id so this works for non hashable types
                return self._obj_cache[id(obj)][0]
            except KeyError:
                self._count += 1
                res = "e%d" % self._count
                # keep obj alive, so id() is unique
                self._obj_cache[id(obj)] = (res, obj)

        while res in self._blacklist:
            res += "_"
        self._blacklist.add(res)
        return res

    def request_name(self, name):
        """Request a name, might return the name or a similar one if already
        used or reserved
        """

        while name in self._blacklist:
            name += "_"
        self._blacklist.add(name)
        return name


class CodeBlock(object):
    """A piece of code with global dependencies"""

    INDENTATION = 4

    def __init__(self, line=None):
        super(CodeBlock, self).__init__()
        self._lines = []
        self._deps = {}
        if line:
            self.write_line(line)

    def get_dependencies(self):
        return self._deps

    def add_dependency(self, name, obj):
        """Add a code dependency so it gets inserted into globals"""

        if name in self._deps:
            if self._deps[name] is obj:
                return
            raise ValueError(
                "There exists a different dep with the same name : %r" % name)
        self._deps[name] = obj

    def write_into(self, block, level=0):
        """Append this block to another one, passing all dependencies"""

        for line, l in self._lines:
            block.write_line(line, level + l)

        for name, obj in _compat.iteritems(self._deps):
            block.add_dependency(name, obj)

    def write_line(self, line, level=0):
        """Append a new line"""

        self._lines.append((line, level))

    def write_lines(self, lines, level=0):
        """Append multiple new lines"""

        for line in lines:
            self.write_line(line, level)

    def compile(self, **kwargs):
        """Execute the python code and returns the global dict.
        kwargs can contain extra dependencies that get only used
        at compile time.
        """

        code = compile(str(self), "<string>", "exec")
        global_dict = dict(self._deps)
        global_dict.update(kwargs)
        _compat.exec_(code, global_dict)
        return global_dict

    def pprint(self, file_=sys.stdout):
        """Print the code block to stdout.
        Does syntax highlighting if possible.
        """

        code = []
        if self._deps:
            code.append("# dependencies:")
        for k, v in _compat.iteritems(self._deps):
            code.append("#   %s: %r" % (k, v))
        code.append(str(self))
        code = "\n".join(code)

        if file_.isatty():
            try:
                from pygments import highlight
                from pygments.lexers import PythonLexer
                from pygments.formatters import TerminalFormatter
            except ImportError:
                pass
            else:
                formatter = TerminalFormatter(bg="dark")
                lexer = PythonLexer()
                file_.write(highlight(code, lexer, formatter))
                return
        file_.write(code + "\n")

    def clear(self):
        del self._lines[:]
        self._deps.clear()

    def __str__(self):
        lines = []
        for line, level in self._lines:
            lines.append(" " * self.INDENTATION * level + line)
        return "\n".join(lines)

    def __repr__(self):
        name = self.__class__.__name__
        deps = ",".join(self._deps.keys())
        return "<%s lines=%d, deps=%r>" % (name, len(self._deps), deps)


def parse_code(code, var_factory, **kwargs):
    """Parse a piece of text and substitude $var by either unique
    variable names or by the given kwargs mapping. Use $$ to escape $.

    Returns a CodeBlock and the resulting variable mapping.

    parse("$foo = $foo + $bar", bar="1")
    ("t1 = t1 + 1", {'foo': 't1', 'bar': '1'})
    """

    block = CodeBlock()
    defdict = collections.defaultdict(var_factory)
    defdict.update(kwargs)

    indent = -1
    code = code.strip()
    for line in code.splitlines():
        length = len(line)
        line = line.lstrip()
        spaces = length - len(line)
        if spaces:
            if indent < 0:
                indent = spaces
                level = 1
            else:
                level = spaces // indent
        else:
            level = 0

        # if there is a single variable and the to be inserted object
        # is a code block, insert the block with the current indentation level
        if line.startswith("$") and line.count("$") == 1:
            name = line[1:]
            if name in kwargs and isinstance(kwargs[name], CodeBlock):
                kwargs[name].write_into(block, level)
                continue

        block.write_line(string.Template(line).substitute(defdict), level)
    return block, dict(defdict)


def parse_with_objects(code, var, **kwargs):
    """Parse code and include non string/codeblock kwargs as
    dependencies.

    int/long will be inlined.

    Returns a CodeBlock and the resulting variable mapping.
    """

    deps = {}
    for key, value in kwargs.items():
        if isinstance(value, _compat.integer_types):
            value = str(value)

        if _compat.PY3:
            if value is None:
                value = str(value)

        if not isinstance(value, _compat.string_types) and \
                not isinstance(value, CodeBlock):
            new_var = var(value)
            deps[new_var] = value
            kwargs[key] = new_var

    block, var = parse_code(code, var, **kwargs)
    for key, dep in _compat.iteritems(deps):
        block.add_dependency(key, dep)

    return block, var
