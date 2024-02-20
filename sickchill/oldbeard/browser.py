import os
import string
import sys
from pathlib import Path
from typing import List

try:
    import pythoncom
except (ModuleNotFoundError, ImportError):
    pythoncom = None

try:
    import win32api
    import win32com.client as win32com_client
except (ModuleNotFoundError, ImportError):
    win32api = None
    win32com_client = None

try:
    import win32net
except (ModuleNotFoundError, ImportError):
    win32net = None

from sickchill import logger, settings


def get_windows_drives_old() -> List[str]:
    if sys.version_info >= (3, 12) and os.name == "nt":
        return os.listdrives()

    if win32api:
        configure_com(True)
        drives = [drive for drive in win32api.GetLogicalDriveStrings().split("\000")][:-1]
        configure_com()
        if drives:
            return drives

    from ctypes import windll

    drives = []
    bitmask = windll.kernel32.GetLogicalDrives()
    for letter in string.ascii_uppercase:
        if bitmask & 1:
            drives.append(f"{letter}:{os.sep}")
        bitmask >>= 1

    return drives


def get_windows_drives() -> List[str]:
    """Return list of detected drives"""

    if win32api is None:
        if os.name == "nt":
            logger.info(_("Unable to get windows shares without pywin32 installed"))

        return get_windows_drives_old()

    configure_com(True)

    # Add Logical Drives
    drives = win32api.GetLogicalDriveStrings().split("\000")[:-1]

    if win32com_client:
        # Add Network Locations (not the same as network shares, these are shortcut files possibly to shares)
        net_shortcuts_location = Path(os.getenv("APPDATA"))
        net_shortcuts_location /= "Microsoft\\Windows\\Network Shortcuts"
        network_shortcuts = []
        for location in net_shortcuts_location.iterdir():
            if location.is_file() and location.suffix == ".lnk":
                network_shortcuts.append(location)
        shell = win32com_client.Dispatch("WScript.Shell")
        for network_shortcut in network_shortcuts:
            shortcut = shell.CreateShortCut(str(network_shortcut))
            drives.append(shortcut.Targetpath)

    configure_com()

    return drives


def get_network_shares():
    network_shares = []
    if win32net is None:
        if os.name == "nt":
            logger.info(_("Unable to get windows shares without pywin32 installed"))
        return network_shares

    configure_com(True)

    servers, count, unknown = win32net.NetServerEnum(None, 100)
    for server in servers:
        # noinspection PyBroadException
        try:
            shares, count, unknown2 = win32net.NetShareEnum(f"\\\\{server['name']}", 0)
            for share in shares:
                network_shares.append(f"\\\\{server['name']}\\{share['netname']}")
        except Exception:
            pass

    configure_com()

    return network_shares


def folders_at_path(path: Path, include_parent: bool = False, include_files: bool = False, file_types: List[str] = None) -> List[dict]:
    """
    Returns a list of dictionaries with the folders contained at the given path.

    Give the empty string as the path to list the contents of the root path
    (under Unix this means "/", on Windows this will be a list of drive letters)

    :param path: to list contents
    :param include_parent: boolean, include parent dir in list as well
    :param include_files: boolean, include files or only directories
    :param file_types: list, file extensions to include, 'images' is an alias for image types
    :return: list of dicts describing folders/files
    """

    # Resolve symlinks and return a sane path
    path = path.resolve()

    # Go up in the path to the containing dir if this is a file
    while not path.is_dir():
        path = path.parent

    if path.parent == path:
        entries = [{"currentPath": ("/", _("My Computer"))[os.name == "nt"]}]
        for name, share in settings.WINDOWS_SHARES.items():
            entries.append({"name": name, "path": f"\\\\{share['server']}\\{share['path']}"})

        if os.name == "nt":
            # noinspection PyBroadException
            try:
                for letter in get_windows_drives():
                    entries.append({"name": letter, "path": letter})

                # TODO: Add a thread to do this on startup and a button in the settings to "find shares", this takes way to long to run.
                # We can store them in WINDOWS_SHARES
                # for share in get_network_shares():
                #     entries.append({"name": share, "path": share})
            except Exception:
                logger.debug("Attempting to get windows drives and shares failed", exc_info=True, stack_info=True)

            return entries
    else:
        entries = [{"currentPath": str(path.resolve())}]
        if include_parent:
            entries.append({"name": "..", "path": str(path.parent.resolve())})

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

    try:
        for entry in path.iterdir():
            if entry.is_file() and not include_files:
                continue

            if str(entry).lower() in hide_list:
                continue

            is_image = False
            is_allowed_type = True

            if entry.is_file() and file_types:
                if "images" in file_types:
                    is_image = entry.suffix in (".jpg", ".jpeg", ".png", ".tiff", ".gif")

                is_allowed_type = entry.suffix in tuple(f".{file_type.strip('.')}" for file_type in file_types) or is_image
                if not is_allowed_type:
                    continue

            file_types = file_types or []

            item_to_add = {"name": entry.name, "path": str(entry.resolve()), "isFile": entry.is_file(), "isImage": is_image, "isAllowed": is_allowed_type}

            if entry.is_file():
                file_list.append(item_to_add)
            else:
                dir_list.append(item_to_add)
    except OSError as error:
        logger.warning(_("Unable to open {path}: {error}").format(path=path, error=error))
        logger.info(_("Unable to open {path}: trying parent directory").format(path=path))
        if path.parent != path:
            return folders_at_path(path.parent, include_parent, include_files, file_types)

    return entries + dir_list + file_list


def configure_com(start: bool = False) -> bool:
    if pythoncom:
        # noinspection PyBroadException
        try:
            if start:
                # noinspection PyUnresolvedReferences
                pythoncom.CoInitializeEx()
            else:
                # noinspection PyUnresolvedReferences
                pythoncom.CoUninitializeEx()

            return True
        except Exception:
            pass

    return False
