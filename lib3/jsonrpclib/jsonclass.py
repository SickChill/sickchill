#!/usr/bin/python
# -- Content-Encoding: UTF-8 --
"""
The serialization module

:authors: Josh Marshall, Thomas Calmant
:copyright: Copyright 2020, Thomas Calmant
:license: Apache License 2.0
:version: 0.4.2

..

    Copyright 2020 Thomas Calmant

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

# Standard library
import inspect
import re

# Local package
import jsonrpclib.config
import jsonrpclib.utils as utils

# ------------------------------------------------------------------------------

# Module version
__version_info__ = (0, 4, 2)
__version__ = ".".join(str(x) for x in __version_info__)

# Documentation strings format
__docformat__ = "restructuredtext en"

# ------------------------------------------------------------------------------

# Supported transmitted code
SUPPORTED_TYPES = (
    (utils.DictType,) + utils.ITERABLE_TYPES + utils.PRIMITIVE_TYPES
)

# Regex of invalid module characters
INVALID_MODULE_CHARS = r"[^a-zA-Z0-9\_\.]"

# ------------------------------------------------------------------------------


class TranslationError(Exception):
    """
    Unmarshalling exception
    """


def _slots_finder(clazz, fields_set):
    """
    Recursively visits the class hierarchy to find all slots

    :param clazz: Class to analyze
    :param fields_set: Set where to store __slots___ content
    """
    # ... class level
    try:
        fields_set.update(clazz.__slots__)
    except AttributeError:
        pass

    # ... parent classes level
    for base_class in clazz.__bases__:
        _slots_finder(base_class, fields_set)


def _find_fields(obj):
    """
    Returns the names of the fields of the given object

    :param obj: An object to analyze
    :return: A set of field names
    """
    # Find fields...
    fields = set()

    # ... using __dict__
    try:
        fields.update(obj.__dict__)
    except AttributeError:
        pass

    # ... using __slots__
    _slots_finder(obj.__class__, fields)
    return fields


def dump(
    obj,
    serialize_method=None,
    ignore_attribute=None,
    ignore=None,
    config=jsonrpclib.config.DEFAULT,
):
    """
    Transforms the given object into a JSON-RPC compliant form.
    Converts beans into dictionaries with a __jsonclass__ entry.
    Doesn't change primitive types.

    :param obj: An object to convert
    :param serialize_method: Custom serialization method
    :param ignore_attribute: Name of the object attribute containing the names
                             of members to ignore
    :param ignore: A list of members to ignore
    :param config: A JSONRPClib Config instance
    :return: A JSON-RPC compliant object
    """
    # Normalize arguments
    serialize_method = serialize_method or config.serialize_method
    ignore_attribute = ignore_attribute or config.ignore_attribute
    ignore = ignore or []

    # Parse / return default "types"...
    # Apply additional types, override built-in types
    # (reminder: config.serialize_handlers is a dict)
    try:
        serializer = config.serialize_handlers[type(obj)]
    except KeyError:
        # Not a serializer
        pass
    else:
        if serializer is not None:
            return serializer(
                obj, serialize_method, ignore_attribute, ignore, config
            )

    # Primitive
    if isinstance(obj, utils.PRIMITIVE_TYPES):
        return obj

    # Iterative
    elif isinstance(obj, utils.ITERABLE_TYPES):
        # List, set or tuple
        return [
            dump(item, serialize_method, ignore_attribute, ignore, config)
            for item in obj
        ]

    elif isinstance(obj, utils.DictType):
        # Dictionary
        return {
            key: dump(value, serialize_method, ignore_attribute, ignore, config)
            for key, value in obj.items()
        }

    # It's not a standard type, so it needs __jsonclass__
    module_name = inspect.getmodule(type(obj)).__name__
    json_class = obj.__class__.__name__

    if module_name not in ("", "__main__"):
        json_class = "{0}.{1}".format(module_name, json_class)

    # Keep the class name in the returned object
    return_obj = {"__jsonclass__": [json_class]}

    # If a serialization method is defined..
    if hasattr(obj, serialize_method):
        # Params can be a dict (keyword) or list (positional)
        # Attrs MUST be a dict.
        serialize = getattr(obj, serialize_method)
        params, attrs = serialize()
        return_obj["__jsonclass__"].append(params)
        return_obj.update(attrs)
    elif utils.is_enum(obj):
        # Add parameters for enumerations
        return_obj["__jsonclass__"].append([obj.value])
    else:
        # Otherwise, try to figure it out
        # Obviously, we can't assume to know anything about the
        # parameters passed to __init__
        return_obj["__jsonclass__"].append([])

        # Prepare filtering lists
        known_types = SUPPORTED_TYPES + tuple(config.serialize_handlers)
        ignore_list = getattr(obj, ignore_attribute, []) + ignore

        # Find fields and filter them by name
        fields = _find_fields(obj)
        fields.difference_update(ignore_list)

        # Dump field values
        attrs = {}
        for attr_name in fields:
            attr_value = getattr(obj, attr_name)
            if (
                isinstance(attr_value, known_types)
                and attr_value not in ignore_list
            ):
                attrs[attr_name] = dump(
                    attr_value,
                    serialize_method,
                    ignore_attribute,
                    ignore,
                    config,
                )
        return_obj.update(attrs)

    return return_obj


# ------------------------------------------------------------------------------


def load(obj, classes=None):
    """
    If 'obj' is a dictionary containing a __jsonclass__ entry, converts the
    dictionary item into a bean of this class.

    :param obj: An object from a JSON-RPC dictionary
    :param classes: A custom {name: class} dictionary
    :return: The loaded object
    """
    # Primitive
    if isinstance(obj, utils.PRIMITIVE_TYPES):
        return obj

    # List, set or tuple
    elif isinstance(obj, utils.ITERABLE_TYPES):
        # This comes from a JSON parser, so it can only be a list...
        return [load(entry) for entry in obj]

    # Otherwise, it's a dict type
    elif "__jsonclass__" not in obj:
        return {key: load(value) for key, value in obj.items()}

    # It's a dictionary, and it has a __jsonclass__
    orig_module_name = obj["__jsonclass__"][0]
    params = obj["__jsonclass__"][1]

    # Validate the module name
    if not orig_module_name:
        raise TranslationError("Module name empty.")

    json_module_clean = re.sub(INVALID_MODULE_CHARS, "", orig_module_name)
    if json_module_clean != orig_module_name:
        raise TranslationError(
            "Module name {0} has invalid characters.".format(orig_module_name)
        )

    # Load the class
    json_module_parts = json_module_clean.split(".")
    if classes and len(json_module_parts) == 1:
        # Local class name -- probably means it won't work
        try:
            json_class = classes[json_module_parts[0]]
        except KeyError:
            raise TranslationError(
                "Unknown class or module {0}.".format(json_module_parts[0])
            )
    else:
        # Module + class
        json_class_name = json_module_parts.pop()
        json_module_tree = ".".join(json_module_parts)
        try:
            # Use fromlist to load the module itself, not the package
            temp_module = __import__(
                json_module_tree, fromlist=[json_class_name]
            )
        except ImportError:
            raise TranslationError(
                "Could not import {0} from module {1}.".format(
                    json_class_name, json_module_tree
                )
            )

        try:
            json_class = getattr(temp_module, json_class_name)
        except AttributeError:
            raise TranslationError(
                "Unknown class {0}.{1}.".format(
                    json_module_tree, json_class_name
                )
            )

    # Create the object
    if isinstance(params, utils.ListType):
        try:
            new_obj = json_class(*params)
        except TypeError as ex:
            raise TranslationError(
                "Error instantiating {0}: {1}".format(json_class.__name__, ex)
            )
    elif isinstance(params, utils.DictType):
        try:
            new_obj = json_class(**params)
        except TypeError as ex:
            raise TranslationError(
                "Error instantiating {0}: {1}".format(json_class.__name__, ex)
            )
    else:
        raise TranslationError(
            "Constructor args must be a dict or a list, "
            "not {0}".format(type(params).__name__)
        )

    # Remove the class information, as it must be ignored during the
    # reconstruction of the object
    raw_jsonclass = obj.pop("__jsonclass__")

    for key, value in obj.items():
        # Recursive loading
        setattr(new_obj, key, load(value, classes))

    # Restore the class information for further usage
    obj["__jsonclass__"] = raw_jsonclass

    return new_obj
