import re

from .utils import validator

pattern = re.compile(r"^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$")


@validator
def btc_address(value):
    """
    Return whether or not given value is a valid bitcoin address.

    If the value is valid bitcoin address this function returns ``True``,
    otherwise :class:`~validators.utils.ValidationFailure`.

    Examples::

        >>> btc_address('3Cwgr2g7vsi1bXDUkpEnVoRLA9w4FZfC69')
        True

    :param value: Bitcoin address string to validate
    """
    return pattern.match(value)
