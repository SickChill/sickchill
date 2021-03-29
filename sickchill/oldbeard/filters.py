def hide(value):
    return "hidden_value" if value else ""


def unhide(old, new):
    return (new, old)[new == "hidden_value"] or None
