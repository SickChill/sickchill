# coding: utf8

u""" This module translates national characters into similar
sounding latin characters (transliteration).

At the moment, Czech, Greek, Latvian, Polish, Turkish, Russian, Ukrainian
and Kazakh alphabets are supported (it covers 99% of needs).

Python 3:

  >>> from trans import trans
  >>> trans('Привет, Мир!')

Python 2:

  >>> import trans
  >>> u'Привет, Мир!'.encode('trans')
  u'Privet, Mir!'
  >>> trans.trans(u'Привет, Мир!')
  u'Privet, Mir!'

Source and full documentations can be found here:
https://github.com/zzzsochi/trans
"""

import sys
import codecs

__version__ = '2.1.0'
__author__ = 'Zelenyak Aleksander aka ZZZ <zzz.sochi@gmail.com>'

PY2 = sys.version_info[0] == 2


class Trans(object):
    """ Main class for transliteration with tables.
    """
    def __init__(self, tables=None, default_table=None):
        self.tables = tables or {}
        self.default_table = default_table

    def __call__(self, input, table=None):
        """ Translate unicode string, using 'table'.

        Table may be tuple (diphthongs, other), dict (other) or string name of table.
        """
        if table is None:
            if self.default_table is not None:
                table = self.default_table
            else:
                raise ValueError('Table not set.')

        if not isinstance(input, unicode if PY2 else str):  # noqa
            raise TypeError(
                'trans codec support only unicode string, {0!r} given.'.format(type(input))
            )

        if isinstance(table, basestring if PY2 else str):  # noqa
            try:
                table = self.tables[table]
            except KeyError:
                raise ValueError(u'Table "{0}" not found in tables!'.format(table))

        if isinstance(table, dict):
            table = ({}, table)

        first = input
        for diphthong, value in table[0].items():
            first = first.replace(diphthong, value)

        default = table[1].get(None, u'_')

        second = u''
        for char in first:
            second += table[1].get(char, default)

        return second


latin = {
    u'à': u'a',  u'á': u'a',  u'â': u'a', u'ã': u'a', u'ä': u'a', u'å': u'a',
    u'æ': u'ae', u'ç': u'c',  u'è': u'e', u'é': u'e', u'ê': u'e', u'ë': u'e',
    u'ì': u'i',  u'í': u'i',  u'î': u'i', u'ï': u'i', u'ð': u'd', u'ñ': u'n',
    u'ò': u'o',  u'ó': u'o',  u'ô': u'o', u'õ': u'o', u'ö': u'o', u'ő': u'o',
    u'ø': u'o',  u'ù': u'u',  u'ú': u'u', u'û': u'u', u'ü': u'u', u'ű': u'u',
    u'ý': u'y',  u'þ': u'th', u'ÿ': u'y',

    u'À': u'A',  u'Á': u'A',  u'Â': u'A', u'Ã': u'A', u'Ä': u'A', u'Å': u'A',
    u'Æ': u'AE', u'Ç': u'C',  u'È': u'E', u'É': u'E', u'Ê': u'E', u'Ë': u'E',
    u'Ì': u'I',  u'Í': u'I',  u'Î': u'I', u'Ï': u'I', u'Ð': u'D', u'Ñ': u'N',
    u'Ò': u'O',  u'Ó': u'O',  u'Ô': u'O', u'Õ': u'O', u'Ö': u'O', u'Ő': u'O',
    u'Ø': u'O',  u'Ù': u'U',  u'Ú': u'U', u'Û': u'U', u'Ü': u'U', u'Ű': u'U',
    u'Ý': u'Y',  u'Þ': u'TH', u'ß': u'ss',
}

greek = {
    u'α': u'a', u'β': u'b', u'γ': u'g', u'δ': u'd', u'ε': u'e',  u'ζ': u'z',
    u'η': u'h', u'θ': u'8', u'ι': u'i', u'κ': u'k', u'λ': u'l',  u'μ': u'm',
    u'ν': u'n', u'ξ': u'3', u'ο': u'o', u'π': u'p', u'ρ': u'r',  u'σ': u's',
    u'τ': u't', u'υ': u'y', u'φ': u'f', u'χ': u'x', u'ψ': u'ps', u'ω': u'w',
    u'ά': u'a', u'έ': u'e', u'ί': u'i', u'ό': u'o', u'ύ': u'y',  u'ή': u'h',
    u'ώ': u'w', u'ς': u's', u'ϊ': u'i', u'ΰ': u'y', u'ϋ': u'y',  u'ΐ': u'i',

    u'Α': u'A', u'Β': u'B', u'Γ': u'G', u'Δ': u'D', u'Ε': u'E',  u'Ζ': u'Z',
    u'Η': u'H', u'Θ': u'8', u'Ι': u'I', u'Κ': u'K', u'Λ': u'L',  u'Μ': u'M',
    u'Ν': u'N', u'Ξ': u'3', u'Ο': u'O', u'Π': u'P', u'Ρ': u'R',  u'Σ': u'S',
    u'Τ': u'T', u'Υ': u'Y', u'Φ': u'F', u'Χ': u'X', u'Ψ': u'PS', u'Ω': u'W',
    u'Ά': u'A', u'Έ': u'E', u'Ί': u'I', u'Ό': u'O', u'Ύ': u'Y',  u'Ή': u'H',
    u'Ώ': u'W', u'Ϊ': u'I', u'Ϋ': u'Y',
}

turkish = {
    u'ş': u's', u'Ş': u'S', u'ı': u'i', u'İ': u'I', u'ç': u'c', u'Ç': u'C',
    u'ü': u'u', u'Ü': u'U', u'ö': u'o', u'Ö': u'O', u'ğ': u'g', u'Ğ': u'G'
}

russian = (
    {
        u'юй': u'yuy', u'ей': u'yay',
        u'Юй': u'Yuy', u'Ей': u'Yay'
    },
    {
    u'а': u'a',  u'б': u'b',  u'в': u'v',  u'г': u'g', u'д': u'd', u'е': u'e',
    u'ё': u'yo', u'ж': u'zh', u'з': u'z',  u'и': u'i', u'й': u'y', u'к': u'k',
    u'л': u'l',  u'м': u'm',  u'н': u'n',  u'о': u'o', u'п': u'p', u'р': u'r',
    u'с': u's',  u'т': u't',  u'у': u'u',  u'ф': u'f', u'х': u'h', u'ц': u'c',
    u'ч': u'ch', u'ш': u'sh', u'щ': u'sh', u'ъ': u'',  u'ы': u'y', u'ь': u'',
    u'э': u'e',  u'ю': u'yu', u'я': u'ya',

    u'А': u'A',  u'Б': u'B',  u'В': u'V',  u'Г': u'G', u'Д': u'D', u'Е': u'E',
    u'Ё': u'Yo', u'Ж': u'Zh', u'З': u'Z',  u'И': u'I', u'Й': u'Y', u'К': u'K',
    u'Л': u'L',  u'М': u'M',  u'Н': u'N',  u'О': u'O', u'П': u'P', u'Р': u'R',
    u'С': u'S',  u'Т': u'T',  u'У': u'U',  u'Ф': u'F', u'Х': u'H', u'Ц': u'C',
    u'Ч': u'Ch', u'Ш': u'Sh', u'Щ': u'Sh', u'Ъ': u'',  u'Ы': u'Y', u'Ь': u'',
    u'Э': u'E',  u'Ю': u'Yu', u'Я': u'Ya',
})

ukrainian = (russian[0].copy(), {
    u'Є': u'Ye', u'І': u'I', u'Ї': u'Yi', u'Ґ': u'G',
    u'є': u'ye', u'і': u'i', u'ї': u'yi', u'ґ': u'g',
})
ukrainian[1].update(russian[1])

czech = {
    u'č': u'c', u'ď': u'd', u'ě': u'e', u'ň': u'n', u'ř': u'r', u'š': u's',
    u'ť': u't', u'ů': u'u', u'ž': u'z',
    u'Č': u'C', u'Ď': u'D', u'Ě': u'E', u'Ň': u'N', u'Ř': u'R', u'Š': u'S',
    u'Ť': u'T', u'Ů': u'U', u'Ž': u'Z',
}

polish = {
    u'ą': u'a', u'ć': u'c', u'ę': u'e', u'ł': u'l', u'ń': u'n', u'ó': u'o',
    u'ś': u's', u'ź': u'z', u'ż': u'z',
    u'Ą': u'A', u'Ć': u'C', u'Ę': u'E', u'Ł': u'L', u'Ń': u'N', u'Ó': u'O',
    u'Ś': u'S', u'Ź': u'Z', u'Ż': u'Z',
}

latvian = {
    u'ā': u'a', u'č': u'c', u'ē': u'e', u'ģ': u'g', u'ī': u'i', u'ķ': u'k',
    u'ļ': u'l', u'ņ': u'n', u'š': u's', u'ū': u'u', u'ž': u'z',
    u'Ā': u'A', u'Č': u'C', u'Ē': u'E', u'Ģ': u'G', u'Ī': u'i', u'Ķ': u'k',
    u'Ļ': u'L', u'Ņ': u'N', u'Š': u'S', u'Ū': u'u', u'Ž': u'Z',
}

kazakh = (russian[0].copy(), {
    u'ә': u'a', u'ғ': u'g', u'қ': u'k', u'ң': 'n', u'ө': u'o', u'ұ': u'u',
    u'ү': u'u', u'һ': u'h', u'і': u'i',
    u'Ә': u'A', u'Ғ': u'G', u'Қ': u'K', u'Ң': 'N', u'Ө': u'O', u'Ұ': u'U',
    u'Ү': u'U', u'Һ': u'H', u'І': u'I',
})
kazakh[1].update(russian[1])

farsi = {
    u'ا': u'a',
    u'أ': u'a', u'\uFE81': u'a', u'\uFE82': u'a',
    u'آ': u'a', u'\uFE83': u'a', u'\uFE84': u'a',
    u'ب': u'b', u'\uFE8F': u'b', u'\uFE90': u'b', u'\uFE92': u'b', u'\uFE91': u'b',
    u'ت': u't', u'\uFE95': u't', u'\uFE96': u't', u'\uFE98': u't', u'\uFE97': u't',
    u'ث': u'th', u'\uFE99': u'th', u'\uFE9A': u'th', u'\uFE9C': u'th', u'\uFE9B': u'th',
    u'ج': u'j', u'\uFE9D': u'j', u'\uFE9E': u'j', u'\uFEA0': u'j', u'\uFE9F': u'j',
    u'ح': u'h', u'\uFEA1': u'h', u'\uFEA2': u'h', u'\uFEA4': u'h', u'\uFEA3': u'h',
    u'خ': u'x', u'\uFEA5': u'x', u'\uFEA6': u'x', u'\uFEA8': u'x', u'\uFEA7': u'x',
    u'د': u'd', u'\uFEA9': u'd', u'\uFEAA': u'd',
    u'ذ': u'd', u'\uFEAB': u'd', u'\uFEAC': u'd',
    u'ر': u'r', u'\uFEAD': u'r', u'\uFEAE': u'r',
    u'ز': u'z', u'\uFEAF': u'z', u'\uFEB0': u'z',
    u'س': u's', u'\uFEB1': u's', u'\uFEB2': u's', u'\uFEB4': u's', u'\uFEB3 ': u's',
    u'ش': u'sh', u'\uFEB5': u'sh', u'\uFEB6': u'sh', u'\uFEB8': u'sh', u'\uFEB7': u'sh',
    u'ص': u's', u'\uFEB9': u's', u'\uFEBA': u's', u'\uFEBC': u's', u'\uFEBB': u's',
    u'ض': u'd', u'\uFEBD': u'd', u'\uFEBE': u'd', u'\uFEC0': u'd', u'\uFEBF': u'd',
    u'ط': u't', u'\uFEC1': u't', u'\uFEC2': u't', u'\uFEC4': u't', u'\uFEC3': u't',
    u'ظ': u'z', u'\uFEC5': u'z', u'\uFEC6': u'z', u'\uFEC8': u'z', u'\uFEC7': u'z',
    u'ع': u'ao', u'\uFEC9': u'ao', u'\uFECA': u'ao', u'\uFECC': u'ao', u'\uFECB': u'ao',
    u'غ': u'za', u'\uFECD': u'za', u'\uFECE': u'za', u'\uFED0': u'za', u'\uFECF': u'za',
    u'ف': u'f', u'\uFED1': u'f', u'\uFED2': u'f', u'\uFED4': u'f', u'\uFED3': u'f',
    u'ق': u'q', u'\uFED5': u'q', u'\uFED6': u'q', u'\uFED8': u'q', u'\uFED7': u'q',
    u'ك': u'k', u'\uFED9': u'k', u'\uFEDA': u'k', u'\uFEDC': u'k', u'\uFEDB': u'k',
    u'ل': u'l', u'\uFEDD': u'l', u'\uFEDE': u'l', u'\uFEE0': u'l', u'\uFEDF': u'l',
    u'م': u'm', u'\uFEE1': u'm', u'\uFEE2': u'm', u'\uFEE4': u'm', u'\uFEE3': u'm',
    u'ن': u'n', u'\uFEE5': u'n', u'\uFEE6': u'n', u'\uFEE8': u'n', u'\uFEE7': u'n',
    u'ه': u'h', u'\uFEE9': u'h', u'\uFEEA': u'h', u'\uFEEC': u'h', u'\uFEEB': u'h',
    u'و': u'wa', u'\uFEED': u'wa', u'\uFEEE': u'wa',
    u'ي': u'ya', u'\uFEF1': u'ya', u'\uFEF2': u'ya', u'\uFEF4': u'ya', u'\uFEF3': u'ya',
    u'ة': u'at', u'\uFE93': u'at', u'\uFE94': u'at',
    u'ى': u'a', u'\uFEEF': u'a', u'\uFEF0': u'a',
    u'ی': u'ye', u'\uFBFC': u'ye', u'\uFBFD': u'ye', u'\uFBFE': u'ye', u'\uFBFF': u'ye',
    # Arabic Sukun
    u'\u064B': u'', u'\u064C': u'', u'\u064D': u'', u'\u064E': u'', u'\u064F': u'',
    u'\u0650': u'', u'\u0651': u'', u'\u0652': u'', u'\u0653': u'', u'\u0670': u'',
    # Arabic punctuation
    u'،': u',', u'؍': u'.', u'؟': u'?', u'٭': u'★', u'؞': u'...', u'٬': u'\'', u'\u200C': u'',
}

ascii_str = (u'_0123456789'
             u'abcdefghijklmnopqrstuvwxyz'
             u'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
             u'!"#$%&\'()*+,_-./:;<=>?@[\\]^`{|}~ \t\n\r\x0b\x0c')

ascii = ({}, dict(zip(ascii_str, ascii_str)))
for t in [latin, greek, turkish, russian, ukrainian, czech, polish, latvian, kazakh, farsi]:
    if isinstance(t, dict):
        t = ({}, t)

    ascii[0].update(t[0])
    ascii[1].update(t[1])

del t
ascii[1][None] = u'_'


slug = (ascii[0].copy(), ascii[1].copy())
for c in u'''!"#$%&'()*+,_-./:;<=>?@[\\]^`{|}~ \t\n\r\x0b\x0c''':
    del slug[1][c]

tables = {u'ascii': ascii, u'text': ascii, u'slug': slug, u'id': slug}

# Main Trans with default tales
# It uses for str.encode('trans')
trans = Trans(tables=tables, default_table='ascii')


# trans codec work only with python 2
if PY2:
    def encode(input, errors='strict', table_name='ascii'):
        try:
            table = trans.tables[table_name]
        except KeyError:
            raise ValueError("Table {0!r} not found in tables!".format(table_name))
        else:
            data = trans(input, table)
            return data, len(data)

    def no_decode(input, errors='strict'):
        raise TypeError("trans codec does not support decode.")

    def trans_codec(enc):
        if enc == 'trans':
            return codecs.CodecInfo(encode, no_decode)

        try:
            enc_name, table_name = enc.split(u'/', 1)
        except ValueError:
            return None

        if enc_name != 'trans':
            return None

        if table_name not in trans.tables:
            raise ValueError(u"Table {0!r} not found in tables!").format(table_name)

        return codecs.CodecInfo(lambda i, e='strict': encode(i, e, table_name), no_decode)

    codecs.register(trans_codec)
