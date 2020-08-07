from bs4 import BeautifulSoup


class BS4Parser(object):
    def __init__(self, *args, **kwargs):
        self.soup = BeautifulSoup(*args, **kwargs)

    def __enter__(self) -> BeautifulSoup:
        return self.soup

    def __exit__(self, exc_ty, exc_val, tb):
        self.soup.clear(True)
        self.soup = None
