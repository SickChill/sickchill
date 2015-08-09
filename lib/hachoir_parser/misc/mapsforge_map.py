"""
Mapsforge map file parser (for version 3 files).

Author: Oliver Gerlich

References:
- http://code.google.com/p/mapsforge/wiki/SpecificationBinaryMapFile
- http://mapsforge.org/
"""

from hachoir_parser import Parser
from hachoir_core.field import (ParserError,
    Bit, Bits, UInt8, UInt16, UInt32, UInt64, String, RawBytes,
    PaddingBits, PaddingBytes,
    Enum, Field, FieldSet, SeekableFieldSet, RootSeekableFieldSet)
from hachoir_core.endian import LITTLE_ENDIAN, BIG_ENDIAN


# micro-degrees factor:
UDEG = float(1000*1000)


CoordinateEncoding = {
    0: "single delta encoding",
    1: "double delta encoding",
}


class UIntVbe(Field):
    def __init__(self, parent, name, description=None):
        Field.__init__(self, parent, name, description=description)

        value = 0
        size = 0
        while True:
            byteValue = ord( self._parent.stream.readBytes(self.absolute_address + (size*8), 1) )

            haveMoreData = (byteValue & 0x80)
            value = value | ((byteValue & 0x7f) << (size*7))
            size += 1
            assert size < 100, "UIntVBE is too large"

            if not(haveMoreData):
                break

        self._size = size*8
        self.createValue = lambda: value


class IntVbe(Field):
    def __init__(self, parent, name, description=None):
        Field.__init__(self, parent, name, description=description)

        value = 0
        size = 0
        shift = 0
        while True:
            byteValue = ord( self._parent.stream.readBytes(self.absolute_address + (size*8), 1) )

            haveMoreData = (byteValue & 0x80)
            if size == 0:
                isNegative = (byteValue & 0x40)
                value = (byteValue & 0x3f)
                shift += 6
            else:
                value = value | ((byteValue & 0x7f) << shift)
                shift += 7
            size += 1
            assert size < 100, "IntVBE is too large"

            if not(haveMoreData):
                break

        if isNegative:
            value *= -1

        self._size = size*8
        self.createValue = lambda: value


class VbeString(FieldSet):
    def createFields(self):
        yield UIntVbe(self, "length")
        yield String(self, "chars", self["length"].value, charset="UTF-8")

    def createDescription (self):
        return '(%d B) "%s"' % (self["length"].value, self["chars"].value)


class TagStringList(FieldSet):
    def createFields(self):
        yield UInt16(self, "num_tags")
        for i in range(self["num_tags"].value):
            yield VbeString(self, "tag[]")

    def createDescription (self):
        return "%d tag strings" % self["num_tags"].value


class ZoomIntervalCfg(FieldSet):
    def createFields(self):
        yield UInt8(self, "base_zoom_level")
        yield UInt8(self, "min_zoom_level")
        yield UInt8(self, "max_zoom_level")
        yield UInt64(self, "subfile_start")
        yield UInt64(self, "subfile_size")

    def createDescription (self):
        return "zoom level around %d (%d - %d)" % (self["base_zoom_level"].value,
            self["min_zoom_level"].value, self["max_zoom_level"].value)


class TileIndexEntry(FieldSet):
    def createFields(self):
        yield Bit(self, "is_water_tile")
        yield Bits(self, "offset", 39)


class TileZoomTable(FieldSet):
    def createFields(self):
        yield UIntVbe(self, "num_pois")
        yield UIntVbe(self, "num_ways")

    def createDescription (self):
        return "%d POIs, %d ways" % (self["num_pois"].value, self["num_ways"].value)


class TileHeader(FieldSet):
    def __init__ (self, parent, name, zoomIntervalCfg, **kw):
        FieldSet.__init__(self, parent, name, **kw)
        self.zoomIntervalCfg = zoomIntervalCfg

    def createFields(self):
        numLevels = int(self.zoomIntervalCfg["max_zoom_level"].value - self.zoomIntervalCfg["min_zoom_level"].value) +1
        assert(numLevels < 50)
        for i in range(numLevels):
            yield TileZoomTable(self, "zoom_table_entry[]")
        yield UIntVbe(self, "first_way_offset")


class POIData(FieldSet):
    def createFields(self):
        yield IntVbe(self, "lat_diff")
        yield IntVbe(self, "lon_diff")
        yield Bits(self, "layer", 4)
        yield Bits(self, "num_tags", 4)

        for i in range(self["num_tags"].value):
            yield UIntVbe(self, "tag_id[]")

        yield Bit(self, "have_name")
        yield Bit(self, "have_house_number")
        yield Bit(self, "have_ele")
        yield PaddingBits(self, "pad[]", 5)

        if self["have_name"].value:
            yield VbeString(self, "name")
        if self["have_house_number"].value:
            yield VbeString(self, "house_number")
        if self["have_ele"].value:
            yield IntVbe(self, "ele")

    def createDescription (self):
        s = "POI"
        if self["have_name"].value:
            s += ' "%s"' % self["name"]["chars"].value
        s += " @ %f/%f" % (self["lat_diff"].value / UDEG, self["lon_diff"].value / UDEG)
        return s



class SubTileBitmap(FieldSet):
    static_size = 2*8
    def createFields(self):
        for y in range(4):
            for x in range(4):
                yield Bit(self, "is_used[%d,%d]" % (x,y))


class WayProperties(FieldSet):
    def createFields(self):
        yield UIntVbe(self, "way_data_size")

        # WayProperties is split into an outer and an inner field, to allow specifying data size for inner part:
        yield WayPropertiesInner(self, "inner", size=self["way_data_size"].value * 8)


class WayPropertiesInner(FieldSet):
    def createFields(self):
        yield SubTileBitmap(self, "sub_tile_bitmap")
        #yield Bits(self, "sub_tile_bitmap", 16)

        yield Bits(self, "layer", 4)
        yield Bits(self, "num_tags", 4)

        for i in range(self["num_tags"].value):
            yield UIntVbe(self, "tag_id[]")

        yield Bit(self, "have_name")
        yield Bit(self, "have_house_number")
        yield Bit(self, "have_ref")
        yield Bit(self, "have_label_position")
        yield Bit(self, "have_num_way_blocks")
        yield Enum(Bit(self, "coord_encoding"), CoordinateEncoding)
        yield PaddingBits(self, "pad[]", 2)

        if self["have_name"].value:
            yield VbeString(self, "name")
        if self["have_house_number"].value:
            yield VbeString(self, "house_number")
        if self["have_ref"].value:
            yield VbeString(self, "ref")
        if self["have_label_position"].value:
            yield IntVbe(self, "label_lat_diff")
            yield IntVbe(self, "label_lon_diff")
        numWayDataBlocks = 1
        if self["have_num_way_blocks"].value:
            yield UIntVbe(self, "num_way_blocks")
            numWayDataBlocks = self["num_way_blocks"].value

        for i in range(numWayDataBlocks):
            yield WayData(self, "way_data[]")

    def createDescription (self):
        s = "way"
        if self["have_name"].value:
            s += ' "%s"' % self["name"]["chars"].value
        return s


class WayData(FieldSet):
    def createFields(self):
        yield UIntVbe(self, "num_coord_blocks")
        for i in range(self["num_coord_blocks"].value):
            yield WayCoordBlock(self, "way_coord_block[]")

class WayCoordBlock(FieldSet):
    def createFields(self):
        yield UIntVbe(self, "num_way_nodes")
        yield IntVbe(self, "first_lat_diff")
        yield IntVbe(self, "first_lon_diff")

        for i in range(self["num_way_nodes"].value-1):
            yield IntVbe(self, "lat_diff[]")
            yield IntVbe(self, "lon_diff[]")


class TileData(FieldSet):
    def __init__ (self, parent, name, zoomIntervalCfg, **kw):
        FieldSet.__init__(self, parent, name, **kw)
        self.zoomIntervalCfg = zoomIntervalCfg

    def createFields(self):
        yield TileHeader(self, "tile_header", self.zoomIntervalCfg)

        numLevels = int(self.zoomIntervalCfg["max_zoom_level"].value - self.zoomIntervalCfg["min_zoom_level"].value) +1
        for zoomLevel in range(numLevels):
            zoomTableEntry = self["tile_header"]["zoom_table_entry[%d]" % zoomLevel]
            for poiIndex in range(zoomTableEntry["num_pois"].value):
                yield POIData(self, "poi_data[%d,%d]" % (zoomLevel, poiIndex))

        for zoomLevel in range(numLevels):
            zoomTableEntry = self["tile_header"]["zoom_table_entry[%d]" % zoomLevel]
            for wayIndex in range(zoomTableEntry["num_ways"].value):
                yield WayProperties(self, "way_props[%d,%d]" % (zoomLevel, wayIndex))
        


class ZoomSubFile(SeekableFieldSet):
    def __init__ (self, parent, name, zoomIntervalCfg, **kw):
        SeekableFieldSet.__init__(self, parent, name, **kw)
        self.zoomIntervalCfg = zoomIntervalCfg

    def createFields(self):
        indexEntries = []
        numTiles = None
        i = 0
        while True:
            entry = TileIndexEntry(self, "tile_index_entry[]")
            indexEntries.append(entry)
            yield entry

            i+=1
            if numTiles is None:
                # calculate number of tiles (TODO: better calc this from map bounding box)
                firstOffset = self["tile_index_entry[0]"]["offset"].value
                numTiles = firstOffset / 5
            if i >= numTiles:
                break

        for indexEntry in indexEntries:
            self.seekByte(indexEntry["offset"].value, relative=True)
            yield TileData(self, "tile_data[]", zoomIntervalCfg=self.zoomIntervalCfg)



class MapsforgeMapFile(Parser, RootSeekableFieldSet):
    PARSER_TAGS = {
        "id": "mapsforge_map",
        "category": "misc",
        "file_ext": ("map",),
        "min_size": 62*8,
        "description": "Mapsforge map file",
    }

    endian = BIG_ENDIAN

    def validate(self):
        return self["file_magic"].value == "mapsforge binary OSM" and self["file_version"].value == 3

    def createFields(self):
        yield String(self, "file_magic", 20)
        yield UInt32(self, "header_size")
        yield UInt32(self, "file_version")
        yield UInt64(self, "file_size")
        yield UInt64(self, "creation_date")
        yield UInt32(self, "min_lat")
        yield UInt32(self, "min_lon")
        yield UInt32(self, "max_lat")
        yield UInt32(self, "max_lon")
        yield UInt16(self, "tile_size")
        yield VbeString(self, "projection")

        # flags
        yield Bit(self, "have_debug")
        yield Bit(self, "have_map_start")
        yield Bit(self, "have_start_zoom")
        yield Bit(self, "have_language_preference")
        yield Bit(self, "have_comment")
        yield Bit(self, "have_created_by")
        yield Bits(self, "reserved[]", 2)

        if self["have_map_start"].value:
            yield UInt32(self, "start_lat")
            yield UInt32(self, "start_lon")
        if self["have_start_zoom"].value:
            yield UInt8(self, "start_zoom")
        if self["have_language_preference"].value:
            yield VbeString(self, "language_preference")
        if self["have_comment"].value:
            yield VbeString(self, "comment")
        if self["have_created_by"].value:
            yield VbeString(self, "created_by")

        yield TagStringList(self, "poi_tags")
        yield TagStringList(self, "way_tags")


        yield UInt8(self, "num_zoom_intervals")
        for i in range(self["num_zoom_intervals"].value):
            yield ZoomIntervalCfg(self, "zoom_interval_cfg[]")

        for i in range(self["num_zoom_intervals"].value):
            zoomIntervalCfg = self["zoom_interval_cfg[%d]" % i]
            self.seekByte(zoomIntervalCfg["subfile_start"].value, relative=False)
            yield ZoomSubFile(self, "subfile[]", size=zoomIntervalCfg["subfile_size"].value * 8, zoomIntervalCfg=zoomIntervalCfg)

