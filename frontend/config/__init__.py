"""
This module implements the web interface for the sickchill configurationt
"""

from frontend.utils import build_blueprint

config_blueprint = build_blueprint(__file__, __name__)
