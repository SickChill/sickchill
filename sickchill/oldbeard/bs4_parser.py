import warnings

from bs4 import BeautifulSoup, FeatureNotFound


class ParserBeautifulSoup(BeautifulSoup):
    """A ``bs4.BeautifulSoup`` that picks the first parser available in `parsers`.

    :param markup: markup for the ``bs4.BeautifulSoup``.
    :param list parsers: parser names, in order of preference.

    Snagged from subliminal, because of course it was.
    """

    def __init__(self, markup, parsers, **kwargs):
        # reject features
        if set(parsers).intersection({"fast", "permissive", "strict", "xml", "html", "html5"}):
            raise ValueError("Features not allowed, only parser names")

        # reject some kwargs
        if "features" in kwargs:
            raise ValueError("Cannot use features kwarg")
        if "builder" in kwargs:
            raise ValueError("Cannot use builder kwarg")

        # pick the first parser available
        for parser in parsers:
            try:
                super(ParserBeautifulSoup, self).__init__(markup, parser, **kwargs)
                return
            except FeatureNotFound:
                pass

        raise FeatureNotFound


class BS4Parser(object):
    def __init__(self, markup, parsers=None, language="html", **kwargs):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            if isinstance(parsers, str):
                parsers = [parsers]

            if language == "html":
                extra_parsers = ["lxml", "html5lib", "html.parser"]
            elif language == "xml":
                extra_parsers = ["lxml-xml", "html.parser"]

            if parsers is None:
                parsers = extra_parsers

            try:
                self.soup = ParserBeautifulSoup(markup, parsers, **kwargs)
            except FeatureNotFound:
                self.soup = ParserBeautifulSoup(markup, extra_parsers, **kwargs)

    def __enter__(self) -> ParserBeautifulSoup:
        return self.soup

    def __exit__(self, exc_ty, exc_val, tb):
        self.soup.clear(True)
        self.soup = None
