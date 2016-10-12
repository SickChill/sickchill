class NoUniqueMatch(RuntimeError):
    """There was more that one on no extensions matching the query."""


class NoMatches(NoUniqueMatch):
    """There were no extensions with the diver name found."""


class MultipleMatches(NoUniqueMatch):
    """There were multiple matches for the given name."""
