"""
This module implements the web interface for the sickchill movies media type
"""

from frontend.utils import build_blueprint

movies_blueprint = build_blueprint(__file__, __name__)
