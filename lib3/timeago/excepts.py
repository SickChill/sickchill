#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on 2016-5-26

@author: hustcc
'''


# parameter not valid
class ParameterUnvalid(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)
