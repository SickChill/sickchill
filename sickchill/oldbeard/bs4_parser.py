import warnings

from subliminal.providers import ParserBeautifulSoup


class BS4Parser(object):
    def __init__(self, *args, **kwargs):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.soup = ParserBeautifulSoup(*args, **kwargs)

    def __enter__(self) -> ParserBeautifulSoup:
        return self.soup

    def __exit__(self, exc_ty, exc_val, tb):
        self.soup.clear(True)
        self.soup = None
