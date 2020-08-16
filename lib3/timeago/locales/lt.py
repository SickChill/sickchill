#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on 2020-04-17

@author: naglis
'''

base = [
    ["ką tik", "po akimirkos"],
    ["prieš %s sekundę", "po %s sekundės", "prieš %s sekundes", "po %s sekundžių", "prieš %s sekundžių", "po %s sekundžių"],
    ["prieš 1 minutę", "po 1 minutės"],
    ["prieš %s minutę", "po %s minutės", "prieš %s minutes", "po %s minučių", "prieš %s minučių", "po %s minučių"],
    ["prieš 1 valandą", "po 1 valandos"],
    ["prieš %s valandą", "po %s valandos", "prieš %s valandas", "po %s valandų", "prieš %s valandų", "po %s valandų"],
    ["prieš 1 dieną", "po 1 dienos"],
    ["prieš %s dieną", "po %s dienos", "prieš %s dienas", "po %s dienų", "prieš %s dienų", "po %s dienų"],
    ["prieš 1 savaitę", "po 1 savaitės"],
    ["prieš %s savaitę", "po %s savaitės", "prieš %s savaites", "po %s savaičių", "prieš %s savaičių", "po %s savaičių"],
    ["prieš 1 mėnesį", "po 1 mėnesio"],
    ["prieš %s mėnesį", "po %s mėnesio", "prieš %s mėnesius", "po %s mėnesių", "prieš %s mėnesių", "po %s mėnesių"],
    ["prieš 1 metus", "po 1 metų"],
    ["prieš %s metus", "po %s metų", "prieš %s metus", "po %s metų", "prieš %s metų", "po %s metų"],
]


def generate(row, y):
    def formatting(time):
        if row % 2 == 0:
            return base[row][y]

        r_10, r_100 = time % 10, time % 100
        if 10 < r_100 < 20 or r_10 == 0:
            return base[row][y + 4]
        elif r_10 != 1:
            return base[row][y + 2]
        else:
            return base[row][y]

    return formatting


LOCALE = generate
