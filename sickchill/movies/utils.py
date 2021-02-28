from enum import Enum
from typing import Dict


def reverse_key(info, value):
    return list(info.keys())[list(info.values()).index(value)]


def reverse_enum(obj: Enum, value):
    for item in obj:
        if item.value == value:
            return item


def make_labeled_enum(name, items: Dict[str, str]):
    for key in items.keys():
        if ' ' in key:
            raise ValueError('Keys cannot have spaces for enums!')

    output = Enum(name, ' '.join(items.keys()))

    def label(self):
        return self.label

    output.__str__ = label
    output.label = name

    for key, value in items.items():
        getattr(output, key).label = value

    return output
