"""
parser package (imdb package).

This package provides various parsers to access IMDb data (e.g.: a
parser for the web/http interface, a parser for the SQL database
interface, etc.).
So far, the http/httpThin, mobile and sql parsers are implemented.

Copyright 2004-2009 Davide Alberani <da@erlug.linux.it>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1335, USA
"""

__all__ = ['http', 'mobile', 'sql']


