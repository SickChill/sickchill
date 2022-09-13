import warnings

from bs4 import FeatureNotFound
from subliminal.providers import ParserBeautifulSoup


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
