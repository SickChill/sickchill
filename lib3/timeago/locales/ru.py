#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on 2017-8-30

@author: avrong
'''

base = [
    ["только что", "через несколько секунд"],
    ["%s секунду назад", "через %s секунду", "%s секунды назад", "через %s секунды", "%s секунд назад", "через %s секунд"],
    ["минуту назад", "через минуту"],
    ["%s минуту назад", "через %s минуту", "%s минуты назад", "через %s минуты", "%s минут назад", "через %s минут"],
    ["час назад", "через час"],
    ["%s час назад", "через %s час", "%s часа назад", "через %s часа", "%s часов назад", "через %s часов"],
    ["вчера", "завтра"],
    ["%s день назад", "через %s день", "%s дня назад", "через %s дня", "%s дней назад", "через %s дней"],
    ["неделю назад", "через неделю"],
    ["%s неделю назад", "через %s неделю", "%s недели назад", "через %s недели", "%s недель назад", "через %s недель"],
    ["месяц назад", "через месяц"],
    ["%s месяц назад", "через %s месяц", "%s месяца назад", "через %s месяца", "%s месяцев назад", "через %s месяцев"],
    ["год назад", "через год"],
    ["%s год назад", "через %s год", "%s года назад", "через %s года", "%s лет назад", "через %s лет"],
]


def generate(row, y):
    def formatting(time):
        '''Uses the first and second fields for (2,3,4) cases and 3rd and 4th for the rest.'''
        multiple_rows = [
            1,   # multiple seconds
            3,   # multiple minutes
            5,   # multiple hours
            7,   # multiple days
            9,   # multiple weeks
            11,  # multiple months
            13,  # multiple years
        ]
        if row in multiple_rows:
            if time > 20:
                time = time % 10
            if time == 1:
                return base[row][y]
            elif time in (2, 3, 4):
                return base[row][y + 2]
            else:
                return base[row][y + 4]
        return base[row][y]

    return formatting


LOCALE = generate
