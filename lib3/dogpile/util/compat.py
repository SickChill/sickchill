import collections
import inspect
import sys

py2k = sys.version_info < (3, 0)
py3k = sys.version_info >= (3, 0)
py32 = sys.version_info >= (3, 2)
py27 = sys.version_info >= (2, 7)
jython = sys.platform.startswith("java")
win32 = sys.platform.startswith("win")

try:
    import threading
except ImportError:
    import dummy_threading as threading  # noqa

FullArgSpec = collections.namedtuple(
    "FullArgSpec",
    [
        "args",
        "varargs",
        "varkw",
        "defaults",
        "kwonlyargs",
        "kwonlydefaults",
        "annotations",
    ],
)

ArgSpec = collections.namedtuple(
    "ArgSpec", ["args", "varargs", "keywords", "defaults"]
)


def inspect_getfullargspec(func):
    """Fully vendored version of getfullargspec from Python 3.3."""

    if inspect.ismethod(func):
        func = func.__func__
    if not inspect.isfunction(func):
        raise TypeError("{!r} is not a Python function".format(func))

    co = func.__code__
    if not inspect.iscode(co):
        raise TypeError("{!r} is not a code object".format(co))

    nargs = co.co_argcount
    names = co.co_varnames
    nkwargs = co.co_kwonlyargcount if py3k else 0
    args = list(names[:nargs])
    kwonlyargs = list(names[nargs : nargs + nkwargs])

    nargs += nkwargs
    varargs = None
    if co.co_flags & inspect.CO_VARARGS:
        varargs = co.co_varnames[nargs]
        nargs = nargs + 1
    varkw = None
    if co.co_flags & inspect.CO_VARKEYWORDS:
        varkw = co.co_varnames[nargs]

    return FullArgSpec(
        args,
        varargs,
        varkw,
        func.__defaults__,
        kwonlyargs,
        func.__kwdefaults__ if py3k else None,
        func.__annotations__ if py3k else {},
    )


def inspect_getargspec(func):
    return ArgSpec(*inspect_getfullargspec(func)[0:4])


if py3k:  # pragma: no cover
    string_types = (str,)
    text_type = str
    string_type = str

    if py32:
        callable = callable  # noqa
    else:

        def callable(fn):  # noqa
            return hasattr(fn, "__call__")

    def u(s):
        return s

    def ue(s):
        return s

    import configparser
    import io
    import _thread as thread
else:
    # Using noqa bellow due to tox -e pep8 who use
    # python3.7 as the default interpreter
    string_types = (basestring,)  # noqa
    text_type = unicode  # noqa
    string_type = str

    def u(s):
        return unicode(s, "utf-8")  # noqa

    def ue(s):
        return unicode(s, "unicode_escape")  # noqa

    import ConfigParser as configparser  # noqa
    import StringIO as io  # noqa

    callable = callable  # noqa
    import thread  # noqa


if py3k or jython:
    import pickle
else:
    import cPickle as pickle  # noqa

if py3k:

    def read_config_file(config, fileobj):
        return config.read_file(fileobj)


else:

    def read_config_file(config, fileobj):
        return config.readfp(fileobj)


def timedelta_total_seconds(td):
    if py27:
        return td.total_seconds()
    else:
        return (
            td.microseconds + (td.seconds + td.days * 24 * 3600) * 1e6
        ) / 1e6
