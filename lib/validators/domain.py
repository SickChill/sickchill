import re

from .utils import validator

pattern = re.compile(
    r'^(([a-zA-Z]{1})|([a-zA-Z]{1}[a-zA-Z]{1})|'  # domain pt.1
    r'([a-zA-Z]{1}[0-9]{1})|([0-9]{1}[a-zA-Z]{1})|'  # domain pt.2
    r'([a-zA-Z0-9][-_.a-zA-Z0-9]{0,61}[a-zA-Z0-9]))\.'  # domain pt.3
    r'([a-zA-Z]{2,13}|(xn--[a-zA-Z0-9]{2,30}))$'  # TLD
)


@validator
def domain(value):
    """
    Return whether or not given value is a valid domain.

    If the value is valid domain name this function returns ``True``, otherwise
    :class:`~validators.utils.ValidationFailure`.

    Examples::

        >>> domain('example.com')
        True

        >>> domain('example.com/')
        ValidationFailure(func=domain, ...)


    Supports IDN domains as well::

        >>> domain('xn----gtbspbbmkef.xn--p1ai')
        True

    .. versionadded:: 0.9

    .. versionchanged:: 0.10

        Added support for internationalized domain name (IDN) validation.

    :param value: domain string to validate
    """
    return pattern.match(value)
