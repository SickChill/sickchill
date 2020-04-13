from six import iteritems
unset = object()


def of(d):
    """
    Remove unset values from a dict.

    :param dict d: A dict to strip.
    :return dict: A dict with unset values removed.
    """
    return {k: v for k, v in iteritems(d) if v != unset}
