def compare_digest(a, b):
    """
    PyJWT expects hmac.compare_digest to exist for all Python 3.x, however it was added in Python > 3.3
    It has a fallback for Python 2.x but not for Pythons between 2.x and 3.3
    Copied from: https://github.com/python/cpython/commit/6cea65555caf2716b4633827715004ab0291a282#diff-c49659257ec1b129707ce47a98adc96eL16

    Returns the equivalent of 'a == b', but avoids content based short
    circuiting to reduce the vulnerability to timing attacks.
    """
    # Consistent timing matters more here than data type flexibility
    if not (isinstance(a, bytes) and isinstance(b, bytes)):
        raise TypeError("inputs must be bytes instances")

    # We assume the length of the expected digest is public knowledge,
    # thus this early return isn't leaking anything an attacker wouldn't
    # already know
    if len(a) != len(b):
        return False

    # We assume that integers in the bytes range are all cached,
    # thus timing shouldn't vary much due to integer object creation
    result = 0
    for x, y in zip(a, b):
        result |= x ^ y
    return result == 0
