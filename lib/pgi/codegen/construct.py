# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

"""Create a gobject constructor object for a specific combination
of property name using g_object_new.

Compared to g_object_newv, this saves us two function calls per parameter.
"""


from .backend import get_backend
from .utils import CodeBlock
from pgi.clib.gir import GITypeTag, GIInfoType
from pgi.util import unescape_parameter, import_attribute


class ConstructorSetter(object):
    TAG = None
    py_type = object

    out_var = ""
    desc = ""

    def setup(self):
        pass

    @classmethod
    def get_class(cls, type_):
        return cls

    def __init__(self, prop_name, type_, backend):
        self.type = type_
        self.backend = backend
        self.name = prop_name

    def get_type(self):
        return self.backend.get_type(self.type, self.desc, may_be_null=True)

    def set(self, name):
        return None, name


class BaseInterfaceSetter(ConstructorSetter):
    TAG = GITypeTag.INTERFACE
    py_type = object

    def setup(self):
        iface = self.type.get_interface()
        try:
            self.py_type = import_attribute(iface.namespace, iface.name)
        except ImportError:
            # fall back to object
            pass

    @classmethod
    def get_class(cls, type_):
        iface = type_.get_interface()
        iface_type = iface.type.value

        if iface_type in [GIInfoType.ENUM, GIInfoType.FLAGS]:
            return EnumFlagsSetter
        elif iface_type == GIInfoType.OBJECT:
            return ObjectSetter
        elif iface_type == GIInfoType.STRUCT:
            return StructSetter
        raise NotImplementedError(iface.type)

    def set(self, name):
        var = self.get_type()
        out = var.pack_in(name)
        self.out_var = out
        return var.block, out


class ObjectSetter(BaseInterfaceSetter):
    pass


class StructSetter(BaseInterfaceSetter):
    pass


class EnumFlagsSetter(BaseInterfaceSetter):
    pass


class BasicSetter(ConstructorSetter):
    def set(self, name):
        var = self.get_type()
        out = var.pack_in(name)
        self.out_var = out
        return var.block, out


class BoolSetter(BasicSetter):
    TAG = GITypeTag.BOOLEAN
    py_type = int


class Int32Setter(BasicSetter):
    TAG = GITypeTag.INT32
    py_type = int


class UInt32Setter(BasicSetter):
    TAG = GITypeTag.UINT32
    py_type = int


class DoubleSetter(BasicSetter):
    TAG = GITypeTag.DOUBLE
    py_type = float


class UTF8Argument(BasicSetter):
    TAG = GITypeTag.UTF8
    py_type = str


_classes = {}


def _find_classes():
    global _classes
    for var in globals().values():
        if not isinstance(var, type):
            continue
        if issubclass(var, ConstructorSetter) and var is not ConstructorSetter:
            _classes[var.TAG] = var
_find_classes()


def get_construct_class(arg_type):
    global _classes
    tag_value = arg_type.tag.value
    try:
        cls = _classes[tag_value]
    except KeyError:
        raise NotImplementedError(
            "%r constructor not implemented" % arg_type.tag)
    else:
        return cls.get_class(arg_type)


def build_constructor_docstring(cls, args):
    from .funcgen import get_type_name

    arg_docs = []
    for arg in args:
        type_name = get_type_name(arg.py_type)
        arg_docs.append(u"%s: %s" % (arg.name, type_name))

    cls_name = u"%s.%s" % (cls.__module__, cls.__name__)
    return u"%s(%s) -> %s" % (cls_name, u", ".join(arg_docs), cls_name)


def _generate_constructor(cls, names, backend):

    gtype = cls.__gtype__
    specs = cls.props

    body = CodeBlock()
    in_args = []
    instances = []

    backend.var.add_blacklist(names)

    for name in names:
        try:
            spec = getattr(specs, name)
        except AttributeError:
            raise TypeError("Property %r not supported" % name)

        type_ = spec._info.get_type()
        const = get_construct_class(type_)
        real_name = unescape_parameter(name)
        instance = const(real_name, type_, backend)
        instance.setup()
        instance.desc = "%s.%s property '%s'" % (
            cls.__module__, cls.__name__, real_name)
        instances.append(instance)

        in_args.append(name)

        block, out = instance.set(name)
        block.write_into(body)

    call_block, return_var = backend.get_constructor(gtype, instances)
    docstring = build_constructor_docstring(cls, instances)

    main, var = backend.parse("""
def _init_($values):
    '''$docstring'''

    $func_body
    $call_block
    return $return_var
""", values=", ".join(in_args), call_block=call_block,
        func_body=body, return_var=return_var, docstring=docstring)

    func = main.compile()["_init_"]
    func._code = main

    return func


def generate_constructor(cls, names):
    # The generated code depends on the gtype / class and the order
    # of the arguments that can be passed to it.

    cache = cls._constructors
    if names in cache:
        return cache[names]
    elif len(cache) > 3:
        cache.clear()

    backend = get_backend("ctypes")()
    return _generate_constructor(cls, names, backend)
