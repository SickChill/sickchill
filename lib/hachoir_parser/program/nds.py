"""
Nintendo DS .nds game file parser

File format references:
- http://www.bottledlight.com/ds/index.php/FileFormats/NDSFormat
- http://imrannazar.com/The-Smallest-NDS-File
- http://darkfader.net/ds/files/ndstool.cpp
- http://crackerscrap.com/docs/dsromstructure.html
- http://nocash.emubase.de/gbatek.htm
"""

from hachoir_parser import Parser
from hachoir_core.field import (ParserError,
    UInt8, UInt16, UInt32, UInt64, String, RawBytes, SubFile, FieldSet, NullBits, Bit, Bits, Bytes,
    SeekableFieldSet, RootSeekableFieldSet)
from hachoir_core.text_handler import textHandler, hexadecimal
from hachoir_core.endian import LITTLE_ENDIAN, BIG_ENDIAN


"""
CRC16 Calculation

Modified from:
http://www.mail-archive.com/python-list@python.org/msg47844.html

Original License:
crc16.py by Bryan G. Olson, 2005
This module is free software and may be used and
distributed under the same terms as Python itself.
"""
class CRC16:
    _table = None

    def _initTable (self):
        from array import array

        # CRC-16 poly: p(x) = x**16 + x**15 + x**2 + 1
        # top bit implicit, reflected
        poly = 0xa001
        CRC16._table = array('H')
        for byte in range(256):
             crc = 0
             for bit in range(8):
                 if (byte ^ crc) & 1:
                     crc = (crc >> 1) ^ poly
                 else:
                     crc >>= 1
                 byte >>= 1
             CRC16._table.append(crc)

    def checksum (self, string, value):
        if CRC16._table is None:
            self._initTable()

        for ch in string:
            value = self._table[ord(ch) ^ (value & 0xff)] ^ (value >> 8)
        return value


class Crc16(UInt16):
    "16 bit field for calculating and comparing CRC-16 of specified string"
    def __init__(self, parent, name, targetBytes):
        UInt16.__init__(self, parent, name)
        self.targetBytes = targetBytes

    def createDescription(self):
        crc = CRC16().checksum(self.targetBytes, 0xffff)
        if crc == self.value:
            return "matches CRC of %d bytes" % len(self.targetBytes)
        else:
            return "mismatch (calculated CRC %d for %d bytes)" % (crc, len(self.targetBytes))


class FileNameDirTable(FieldSet):
    static_size = (4+2+2)*8
    def createFields(self):
        yield UInt32(self, "entry_start")
        yield UInt16(self, "entry_file_id")
        yield UInt16(self, "parent_id")

    def createDescription(self):
        return "first file id: %d; parent directory id: %d (%d)" % (self["entry_file_id"].value, self["parent_id"].value, self["parent_id"].value & 0xFFF)

class FileNameEntry(FieldSet):
    def createFields(self):
        yield Bits(self, "name_len", 7)
        yield Bit(self, "is_directory")
        yield String(self, "name", self["name_len"].value)
        if self["is_directory"].value:
            yield UInt16(self, "dir_id")

    def createDescription(self):
        s = ""
        if self["is_directory"].value:
            s = "[D] "
        return s + self["name"].value

class Directory(FieldSet):
    def createFields(self):
        while True:
            fne = FileNameEntry(self, "entry[]")
            if fne["name_len"].value == 0:
                yield UInt8(self, "end_marker")
                break
            yield fne


class FileNameTable(SeekableFieldSet):
    def createFields(self):
        self.startOffset = self.absolute_address / 8

        # parent_id of first FileNameDirTable contains number of directories:
        dt = FileNameDirTable(self, "dir_table[]")
        numDirs = dt["parent_id"].value
        yield dt

        for i in range(1, numDirs):
            yield FileNameDirTable(self, "dir_table[]")

        for i in range(0, numDirs):
            dt = self["dir_table[%d]" % i]
            offset = self.startOffset + dt["entry_start"].value
            self.seekByte(offset, relative=False)
            yield Directory(self, "directory[]")


class FATFileEntry(FieldSet):
    static_size = 2*4*8
    def createFields(self):
        yield UInt32(self, "start")
        yield UInt32(self, "end")

    def createDescription(self):
        return "start: %d; size: %d" % (self["start"].value, self["end"].value - self["start"].value)

class FATContent(FieldSet):
    def createFields(self):
        num_entries = self.parent["header"]["fat_size"].value / 8
        for i in range(0, num_entries):
            yield FATFileEntry(self, "entry[]")



class BannerTile(FieldSet):
    static_size = 32*8
    def createFields(self):
        for y in range(8):
            for x in range(8):
                yield Bits(self, "pixel[%d,%d]" % (x,y), 4)

class BannerIcon(FieldSet):
    static_size = 16*32*8
    def createFields(self):
        for y in range(4):
            for x in range(4):
                yield BannerTile(self, "tile[%d,%d]" % (x,y))

class NdsColor(FieldSet):
    static_size = 16
    def createFields(self):
        yield Bits(self, "red", 5)
        yield Bits(self, "green", 5)
        yield Bits(self, "blue", 5)
        yield NullBits(self, "pad", 1)

    def createDescription(self):
        return "#%02x%02x%02x" % (self["red"].value << 3, self["green"].value << 3, self["blue"].value << 3)

class Banner(FieldSet):
    static_size = 2112*8
    def createFields(self):
        yield UInt16(self, "version")
        # CRC of this structure, excluding first 32 bytes:
        yield Crc16(self, "crc", self.stream.readBytes(self.absolute_address+(32*8), (2112-32)))
        yield RawBytes(self, "reserved", 28)
        yield BannerIcon(self, "icon_data")
        for i in range(0, 16):
            yield NdsColor(self, "palette_color[]")
        yield String(self, "title_jp", 256, charset="UTF-16-LE", truncate="\0")
        yield String(self, "title_en", 256, charset="UTF-16-LE", truncate="\0")
        yield String(self, "title_fr", 256, charset="UTF-16-LE", truncate="\0")
        yield String(self, "title_de", 256, charset="UTF-16-LE", truncate="\0")
        yield String(self, "title_it", 256, charset="UTF-16-LE", truncate="\0")
        yield String(self, "title_es", 256, charset="UTF-16-LE", truncate="\0")


class Overlay(FieldSet):
    static_size = 8*4*8
    def createFields(self):
        yield UInt32(self, "id")
        yield textHandler(UInt32(self, "ram_address"), hexadecimal)
        yield UInt32(self, "ram_size")
        yield UInt32(self, "bss_size")
        yield textHandler(UInt32(self, "init_start_address"), hexadecimal)
        yield textHandler(UInt32(self, "init_end_address"), hexadecimal)
        yield UInt32(self, "file_id")
        yield RawBytes(self, "reserved[]", 4)

    def createDescription(self):
        return "file #%d, %d (+%d) bytes to 0x%08x" % (
            self["file_id"].value, self["ram_size"].value, self["bss_size"].value, self["ram_address"].value)


class SecureArea(FieldSet):
    static_size=2048*8
    def createFields(self):
        yield textHandler(UInt64(self, "id"), hexadecimal)
        if self["id"].value == 0xe7ffdeffe7ffdeff: # indicates that secure area is decrypted
            yield Bytes(self, "fixed[]", 6) # always \xff\xde\xff\xe7\xff\xde
            yield Crc16(self, "header_crc16", self.stream.readBytes(self.absolute_address+(16*8), 2048-16))
            yield RawBytes(self, "unknown[]", 2048-16-2)
            yield Bytes(self, "fixed[]", 2) # always \0\0
        else:
            yield RawBytes(self, "encrypted[]", 2048-8)


class DeviceSize(UInt8):
    def createDescription(self):
        return "%d Mbit" % ((2**(20+self.value)) / (1024*1024))

class Header(FieldSet):
    def createFields(self):
        yield String(self, "game_title", 12, truncate="\0")
        yield String(self, "game_code", 4)
        yield String(self, "maker_code", 2)
        yield UInt8(self, "unit_code")
        yield UInt8(self, "device_code")

        yield DeviceSize(self, "card_size")
        yield String(self, "card_info", 9)
        yield UInt8(self, "rom_version")
        yield Bits(self, "unknown_flags[]", 2)
        yield Bit(self, "autostart_flag")
        yield Bits(self, "unknown_flags[]", 5)

        yield UInt32(self, "arm9_source", "ARM9 ROM offset")
        yield textHandler(UInt32(self, "arm9_execute_addr", "ARM9 entry address"), hexadecimal)
        yield textHandler(UInt32(self, "arm9_copy_to_addr", "ARM9 RAM address"), hexadecimal)
        yield UInt32(self, "arm9_bin_size", "ARM9 code size")

        yield UInt32(self, "arm7_source", "ARM7 ROM offset")
        yield textHandler(UInt32(self, "arm7_execute_addr", "ARM7 entry address"), hexadecimal)
        yield textHandler(UInt32(self, "arm7_copy_to_addr", "ARM7 RAM address"), hexadecimal)
        yield UInt32(self, "arm7_bin_size", "ARM7 code size")

        yield UInt32(self, "filename_table_offset")
        yield UInt32(self, "filename_table_size")
        yield UInt32(self, "fat_offset")
        yield UInt32(self, "fat_size")

        yield UInt32(self, "arm9_overlay_src")
        yield UInt32(self, "arm9_overlay_size")
        yield UInt32(self, "arm7_overlay_src")
        yield UInt32(self, "arm7_overlay_size")

        yield textHandler(UInt32(self, "ctl_read_flags"), hexadecimal)
        yield textHandler(UInt32(self, "ctl_init_flags"), hexadecimal)
        yield UInt32(self, "banner_offset")
        yield Crc16(self, "secure_crc16", self.stream.readBytes(0x4000*8, 0x4000))
        yield UInt16(self, "rom_timeout")

        yield UInt32(self, "arm9_unk_addr")
        yield UInt32(self, "arm7_unk_addr")
        yield UInt64(self, "unenc_mode_magic")

        yield UInt32(self, "rom_size")
        yield UInt32(self, "header_size")

        yield RawBytes(self, "unknown[]", 36)
        yield String(self, "passme_autoboot_detect", 4)
        yield RawBytes(self, "unknown[]", 16)

        yield RawBytes(self, "gba_logo", 156)
        yield Crc16(self, "logo_crc16", self.stream.readBytes(0xc0*8, 156))
        yield Crc16(self, "header_crc16", self.stream.readBytes(0, 350))

        yield UInt32(self, "debug_rom_offset")
        yield UInt32(self, "debug_size")
        yield textHandler(UInt32(self, "debug_ram_address"), hexadecimal)


class NdsFile(Parser, RootSeekableFieldSet):
    PARSER_TAGS = {
        "id": "nds_file",
        "category": "program",
        "file_ext": ("nds",),
        "mime": (u"application/octet-stream",),
        "min_size": 352 * 8, # just a minimal header
        "description": "Nintendo DS game file",
    }

    endian = LITTLE_ENDIAN

    def validate(self):
        try:
            header = self["header"]
        except Exception, e:
            return False

        return (self.stream.readBytes(0, 1) != "\0"
            and (header["device_code"].value & 7) == 0
            and header["header_size"].value >= 352
            and header["card_size"].value < 15 # arbitrary limit at 32Gbit
            and header["arm9_bin_size"].value > 0 and header["arm9_bin_size"].value <= 0x3bfe00
            and header["arm7_bin_size"].value > 0 and header["arm7_bin_size"].value <= 0x3bfe00
            and header["arm9_source"].value + header["arm9_bin_size"].value < self._size
            and header["arm7_source"].value + header["arm7_bin_size"].value < self._size
            and header["arm9_execute_addr"].value >= 0x02000000 and header["arm9_execute_addr"].value <= 0x023bfe00
            and header["arm9_copy_to_addr"].value >= 0x02000000 and header["arm9_copy_to_addr"].value <= 0x023bfe00
            and header["arm7_execute_addr"].value >= 0x02000000 and header["arm7_execute_addr"].value <= 0x03807e00
            and header["arm7_copy_to_addr"].value >= 0x02000000 and header["arm7_copy_to_addr"].value <= 0x03807e00
            )

    def createFields(self):
        # Header
        yield Header(self, "header")

        # Secure Area
        if self["header"]["arm9_source"].value >= 0x4000 and self["header"]["arm9_source"].value < 0x8000:
            secStart = self["header"]["arm9_source"].value & 0xfffff000
            self.seekByte(secStart, relative=False)
            yield SecureArea(self, "secure_area", size=0x8000-secStart)

        # ARM9 binary
        self.seekByte(self["header"]["arm9_source"].value, relative=False)
        yield RawBytes(self, "arm9_bin", self["header"]["arm9_bin_size"].value)

        # ARM7 binary
        self.seekByte(self["header"]["arm7_source"].value, relative=False)
        yield RawBytes(self, "arm7_bin", self["header"]["arm7_bin_size"].value)

        # File Name Table
        if self["header"]["filename_table_size"].value > 0:
            self.seekByte(self["header"]["filename_table_offset"].value, relative=False)
            yield FileNameTable(self, "filename_table", size=self["header"]["filename_table_size"].value*8)

        # FAT
        if self["header"]["fat_size"].value > 0:
            self.seekByte(self["header"]["fat_offset"].value, relative=False)
            yield FATContent(self, "fat_content", size=self["header"]["fat_size"].value*8)

        # banner
        if self["header"]["banner_offset"].value > 0:
            self.seekByte(self["header"]["banner_offset"].value, relative=False)
            yield Banner(self, "banner")

        # ARM9 overlays
        if self["header"]["arm9_overlay_src"].value > 0:
            self.seekByte(self["header"]["arm9_overlay_src"].value, relative=False)
            numOvls = self["header"]["arm9_overlay_size"].value / (8*4)
            for i in range(numOvls):
                yield Overlay(self, "arm9_overlay[]")

        # files
        if self["header"]["fat_size"].value > 0:
            for field in self["fat_content"]:
                if field["end"].value > field["start"].value:
                    self.seekByte(field["start"].value, relative=False)
                    yield SubFile(self, "file[]", field["end"].value - field["start"].value)
