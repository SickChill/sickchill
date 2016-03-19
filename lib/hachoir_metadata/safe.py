from hachoir_core.error import HACHOIR_ERRORS, warning

def fault_tolerant(func, *args):
    def safe_func(*args, **kw):
        try:
            func(*args, **kw)
        except HACHOIR_ERRORS, err:
            warning("Error when calling function {0!s}(): {1!s}".format(
                func.__name__, err))
    return safe_func

def getFieldAttribute(fieldset, key, attrname):
    try:
        field = fieldset[key]
        if field.hasValue():
            return getattr(field, attrname)
    except HACHOIR_ERRORS, err:
        warning("Unable to get {0!s} of field {1!s}/{2!s}: {3!s}".format(
            attrname, fieldset.path, key, err))
    return None

def getValue(fieldset, key):
    return getFieldAttribute(fieldset, key, "value")

def getDisplay(fieldset, key):
    return getFieldAttribute(fieldset, key, "display")

