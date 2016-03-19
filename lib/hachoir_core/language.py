from hachoir_core.iso639 import ISO639_2

class Language:
    def __init__(self, code):
        code = str(code)
        if code not in ISO639_2:
            raise ValueError("Invalid language code: {0!r}".format(code))
        self.code = code

    def __cmp__(self, other):
        if other.__class__ != Language:
            return 1
        return cmp(self.code, other.code)

    def __unicode__(self):
       return ISO639_2[self.code]

    def __str__(self):
       return self.__unicode__()

    def __repr__(self):
        return "<Language '{0!s}', code={1!r}>".format(unicode(self), self.code)

