# -*- coding: utf-8 -*-

"""
This module implements the keys class of tvdbsimple.
"""

import os
class keys():
    """
    The class is needed to hold the api key value and the token value.
    """
    API_KEY = os.environ.get('TVDB_API_KEY', None)
    """
    It's the TheTVDb api key needed for the api access. The developer must fill it.
    """
    API_TOKEN = os.environ.get('TVDB_API_TOKEN', None)
    """
    Contains the TheTVDb token used for authenticating api requests. The developer might provide a valid one.
    
    If a request fails the module will get a new token automatically upating it.
    """