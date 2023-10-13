def hide(value):
    return "hidden_value" if value else ""


def unhide(old, new):
    return (new, old)[new == "hidden_value"] or None


def hidden(setting):
    if setting:
        return ""
    return "hidden"


def disabled(setting):
    if setting:
        return ""
    return "disabled"


def checked(setting):
    if setting:
        return "checked"
    return ""
