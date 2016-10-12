from .utils import validator


@validator
def ipv4(value):
    """
    Return whether or not given value is a valid IP version 4 address.

    This validator is based on `WTForms IPAddress validator`_

    .. _WTForms IPAddress validator:
       https://github.com/wtforms/wtforms/blob/master/wtforms/validators.py

    Examples::

        >>> ipv4('123.0.0.7')
        True

        >>> ipv4('900.80.70.11')
        ValidationFailure(func=ipv4, args={'value': '900.80.70.11'})

    .. versionadded:: 0.2

    :param value: IP address string to validate
    """
    parts = value.split('.')
    if len(parts) == 4 and all(x.isdigit() for x in parts):
        numbers = list(int(x) for x in parts)
        return all(num >= 0 and num < 256 for num in numbers)
    return False


@validator
def ipv6(value):
    """
    Return whether or not given value is a valid IP version 6 address.

    This validator is based on `WTForms IPAddress validator`_.

    .. _WTForms IPAddress validator:
       https://github.com/wtforms/wtforms/blob/master/wtforms/validators.py

    Examples::

        >>> ipv6('abcd:ef::42:1')
        True

        >>> ipv6('abc.0.0.1')
        ValidationFailure(func=ipv6, args={'value': 'abc.0.0.1'})

    .. versionadded:: 0.2

    :param value: IP address string to validate
    """
    parts = value.split(':')
    if len(parts) > 8:
        return False

    num_blank = 0
    for part in parts:
        if not part:
            num_blank += 1
        else:
            try:
                value = int(part, 16)
            except ValueError:
                return False
            else:
                if value < 0 or value >= 65536:
                    return False

    if num_blank < 2:
        return True
    elif num_blank == 2 and not parts[0] and not parts[1]:
        return True
    return False
