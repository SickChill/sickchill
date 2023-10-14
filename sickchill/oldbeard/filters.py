def hide(value):
    return "hidden_value" if value else ""


def unhide(old, new):
    return (new, old)[new == "hidden_value"] or None


def hidden(condition: bool) -> str:
    if condition:
        return ""
    return "hidden"


def disabled(condition: bool) -> str:
    if condition:
        return ""
    return "disabled"


def checked(condition: bool) -> str:
    if condition:
        return "checked"
    return ""


def selected(condition: bool) -> str:
    if condition:
        return "selected"
    return ""
