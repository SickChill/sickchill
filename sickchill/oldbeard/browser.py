import os
import string

from sickchill import logger, settings


# adapted from http://stackoverflow.com/questions/827371/is-there-a-way-to-list-all-the-available-drive-letters-in-python/827490
def getWinDrives():
    """Return list of detected drives"""
    assert os.name == "nt"
    from ctypes import windll

    drives = []
    bitmask = windll.kernel32.GetLogicalDrives()  # @UndefinedVariable
    for letter in string.ascii_uppercase:
        if bitmask & 1:
            drives.append(letter)
        bitmask >>= 1

    return drives


def getFileList(path, includeFiles, fileTypes):
    # prune out directories to protect the user from doing stupid things (already lower case the dir to reduce calls)
    hide_list = [
        "boot",
        "bootmgr",
        "cache",
        "config.msi",
        "msocache",
        "recovery",
        "$recycle.bin",
        "recycler",
        "system volume information",
        "temporary internet files",
    ]  # windows specific
    hide_list += [".fseventd", ".spotlight", ".trashes", ".vol", "cachedmessages", "caches", "trash"]  # osx specific
    hide_list += [".git"]

    file_list, dir_list = [], []
    for filename in os.listdir(path):
        if filename.lower() in hide_list:
            continue

        full_filename = os.path.join(path, filename)
        is_file = os.path.isfile(full_filename)

        if not includeFiles and is_file:
            continue

        is_image = False
        allowed_type = True
        if is_file and fileTypes:
            if "images" in fileTypes:
                is_image = filename.endswith(("jpg", "jpeg", "png", "tiff", "gif"))
            allowed_type = filename.endswith(tuple(fileTypes)) or is_image

            if not allowed_type:
                continue

        item_to_add = {"name": filename, "path": full_filename, "isFile": is_file, "isImage": is_image, "isAllowed": allowed_type}

        if is_file:
            file_list.append(item_to_add)
        else:
            dir_list.append(item_to_add)

    # Sort folders first, alphabetically, case insensitive
    dir_list.sort(key=lambda mbr: mbr.get("name").lower())
    file_list.sort(key=lambda mbr: mbr.get("name").lower())
    return dir_list + file_list


def foldersAtPath(path, includeParent=False, includeFiles=False, fileTypes=None):
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

    # walk up the tree until we find a valid directory path
    while path and not os.path.isdir(path) and path != "/":
        if path == os.path.dirname(path):
            path = ""
        else:
            path = os.path.dirname(path)

    if path == "":
        if os.name != "nt":
            path = "/"
        else:
            entries = [{"currentPath": "Root"}]
            for letter in getWinDrives():
                letter_path = letter + ":\\"
                entries.append({"name": letter_path, "path": letter_path})

            for name, share in settings.WINDOWS_SHARES.items():
                entries.append({"name": name, "path": r"\\{server}\{path}".format(server=share["server"], path=share["path"])})

            return entries

    # fix up the path and find the parent
    path = os.path.abspath(os.path.normpath(path))
    parent_path = os.path.dirname(path)

    # if we're at the root then the next step is the meta-node showing our drive letters
    if path == parent_path and os.name == "nt":
        parent_path = ""

    fileTypes = fileTypes or []

    try:
        file_list = getFileList(path, includeFiles, fileTypes)
    except OSError as e:
        logger.warning("Unable to open {0}: {1} / {2}".format(path, repr(e), str(e)))
        file_list = getFileList(parent_path, includeFiles, fileTypes)

    entries = [{"currentPath": path}]
    if path == "/":
        for name, share in settings.WINDOWS_SHARES.items():
            entries.append({"name": name, "path": r"\\{server}\{path}".format(server=share["server"], path=share["path"])})

    if includeParent and parent_path != path:
        entries.append({"name": "..", "path": parent_path})
    entries.extend(file_list)

    return entries
