from bs4 import BeautifulSoup

class BS4Parser:
    def __init__(self, *args, **kwargs):
        self.soup = BeautifulSoup(*args, **kwargs)

    def __enter__(self):
        return self.soup

    def __exit__(self, exc_ty, exc_val, tb):
        self.soup.clear(True)
        self.soup = None