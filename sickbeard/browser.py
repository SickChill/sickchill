# coding=utf-8
# Author: Nic Wolfe <nic@wolfeden.ca>
#
# URL: https://sickrage.github.io
#
# This file is part of SickRage.
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage. If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import os
import string

from sickbeard import logger
from sickrage.helper.encoding import ek


# adapted from http://stackoverflow.com/questions/827371/is-there-a-way-to-list-all-the-available-drive-letters-in-python/827490
def getWinDrives():
    """ Return list of detected drives """
    assert os.name == 'nt'
    from ctypes import windll

    drives = []
    bitmask = windll.kernel32.GetLogicalDrives()  # @UndefinedVariable
    for letter in string.uppercase:
        if bitmask & 1:
            drives.append(letter)
        bitmask >>= 1

    return drives


def getFileList(path, includeFiles, fileTypes):
    # prune out directories to protect the user from doing stupid things (already lower case the dir to reduce calls)
    hide_list = ['boot', 'bootmgr', 'cache', 'config.msi', 'msocache', 'recovery', '$recycle.bin',
                 'recycler', 'system volume information', 'temporary internet files']  # windows specific
    hide_list += ['.fseventd', '.spotlight', '.trashes', '.vol', 'cachedmessages', 'caches', 'trash']  # osx specific
    hide_list += ['.git']

    file_list = []
    for filename in ek(os.listdir, path):
        if filename.lower() in hide_list:
            continue

        full_filename = ek(os.path.join, path, filename)
        is_file = ek(os.path.isfile, full_filename)

        if not includeFiles and is_file:
            continue

        is_image = False
        allowed_type = True
        if is_file and fileTypes:
            allowed_type = False
            if 'images' in fileTypes:
                allowed_type = is_image = filename.endswith(('jpg', 'jpeg', 'png', 'tiff', 'gif'))
            else:
                allowed_type = filename.endswith(tuple(fileTypes))

            if not allowed_type:
                continue

        file_list.append({
            'name': filename,
            'path': full_filename,
            'isFile': is_file,
            'isImage': is_image,
            'isAllowed': allowed_type
        })

    return file_list


def foldersAtPath(path, includeParent=False, includeFiles=False, fileTypes=[]):
    """
    Returns a list of dictionaries with the folders contained at the given path.

    Give the empty string as the path to list the contents of the root path
    (under Unix this means "/", on Windows this will be a list of drive letters)

    :param path: to list contents
    :param includeParent: boolean, include parent dir in list as well
    :param includeFiles: boolean, include files or only directories
    :param fileTypes: list, file extensions to include, 'images' is an alias for image types
    :return: list of folders/files
    """

    # walk up the tree until we find a valid path
    while path and not ek(os.path.isdir, path):
        if path == ek(os.path.dirname, path):
            path = ''
            break
        else:
            path = ek(os.path.dirname, path)

    if path == '':
        if os.name == 'nt':
            entries = [{'currentPath': 'Root'}]
            for letter in getWinDrives():
                letter_path = letter + ':\\'
                entries.append({'name': letter_path, 'path': letter_path})
            return entries
        else:
            path = '/'

    # fix up the path and find the parent
    path = ek(os.path.abspath, ek(os.path.normpath, path))
    parent_path = ek(os.path.dirname, path)

    # if we're at the root then the next step is the meta-node showing our drive letters
    if path == parent_path and os.name == 'nt':
        parent_path = ''

    try:
        file_list = getFileList(path, includeFiles, fileTypes)
    except OSError as e:
        logger.log('Unable to open {0}: {1} / {2}'.format(path, repr(e), str(e)), logger.WARNING)
        file_list = getFileList(parent_path, includeFiles, fileTypes)

    file_list = sorted(file_list,
                       lambda x, y: ek(os.path.basename, x['name']).lower() < ek(os.path.basename, y['path']).lower())
    file_list = [x for x in file_list if not x['isFile']] + [x for x in file_list if x['isFile']]  # folders first

    entries = [{'currentPath': path}]
    if includeParent and parent_path != path:
        entries.append({'name': '..', 'path': parent_path})
    entries.extend(file_list)

    return entries
