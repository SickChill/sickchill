import re

from .utils import validator

regex = (
    r'^[a-z]+://([^/:]+{tld}|([0-9]{{1,3}}\.)'
    r'{{3}}[0-9]{{1,3}})(:[0-9]+)?(\/.*)?$'
)

pattern_with_tld = re.compile(regex.format(tld=r'\.[a-z]{2,10}'))
pattern_without_tld = re.compile(regex.format(tld=''))


@validator
def url(value, require_tld=True):
    """
    Return whether or not given value is a valid URL.

    If the value is valid URL this function returns ``True``, otherwise
    :class:`~validators.utils.ValidationFailure`.

    This validator is based on `WTForms URL validator`_.

    .. _WTForms URL validator:
       https://github.com/wtforms/wtforms/blob/master/wtforms/validators.py

    Examples::

        >>> url('http://foobar.dk')
        True

        >>> url('http://localhost/foobar', require_tld=False)
        True

        >>> url('http://foobar.d')
        ValidationFailure(func=url, ...)

    .. versionadded:: 0.2

    :param value: URL address string to validate
    """

    if require_tld:
        return pattern_with_tld.match(value)
    return pattern_without_tld.match(value)
