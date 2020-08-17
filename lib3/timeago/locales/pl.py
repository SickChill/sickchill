#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on 2018-11-11

@author: marcel-odya
'''

base = [
    ["właśnie teraz", "za chwilę"],
    ["%s sekund temu", "za %s sekund", "%s sekundy temu", "za %s sekundy"],
    ["minutę temu", "za minutę"],
    ["%s minut temu", "za %s minut", "%s minuty temu", "za %s minuty"],
    ["godzinę temu", "za godzinę"],
    ["%s godzin temu", "za %s godzin", "%s godziny temu", "za %s godziny"],
    ["1 dzień temu", "za 1 dzień"],
    ["%s dni temu", "za %s dni", "%s dni temu", "za %s dni"],
    ["tydzień temu", "za tydzień"],
    ["%s tygodni temu", "za %s tygodni", "%s tygodnie temu", "za %s tygodnie"],
    ["miesiąc temu", "za miesiąc"],
    ["%s miesięcy temu", "za %s miesięcy", "%s miesiące temu", "za %s miesiące"],
    ["rok temu", "za rok"],
    ["%s lat temu", "za %s lat", "%s lata temu", "za %s lata"]
]


def generate(row, y):
    def formatting(time):
        '''
        Uses the 3rd and 4th field of the list in every 2 entries -
        the ones containing %s, if the diff ends with 2, 3 or 4 but
        not with 12, 13 or 14.
        '''
        if row % 2 == 0:
            return base[row][y]
        last_number = time % 10
        last_two_numbers = time % 100
        if last_number in range(2, 5) and last_two_numbers not in range(12, 15):
            return base[row][y + 2]
        return base[row][y]

    return formatting


LOCALE = generate
