from hachoir_core.field import FieldSet, UserVector, UInt8

class RGB(FieldSet):
    color_name = {
        (  0,   0,   0): "Black",
        (255,   0,   0): "Red",
        (  0, 255,   0): "Green",
        (  0,   0, 255): "Blue",
        (255, 255, 255): "White",
    }
    static_size = 24

    def createFields(self):
        yield UInt8(self, "red", "Red")
        yield UInt8(self, "green", "Green")
        yield UInt8(self, "blue", "Blue")

    def createDescription(self):
        rgb = self["red"].value, self["green"].value, self["blue"].value
        name = self.color_name.get(rgb)
        if not name:
            name = "#{0:02X}{1:02X}{2:02X}".format(*rgb)
        return "RGB color: " + name

class RGBA(RGB):
    static_size = 32

    def createFields(self):
        yield UInt8(self, "red", "Red")
        yield UInt8(self, "green", "Green")
        yield UInt8(self, "blue", "Blue")
        yield UInt8(self, "alpha", "Alpha")

    def createDescription(self):
        description = RGB.createDescription(self)
        opacity = self["alpha"].value*100/255
        return "{0!s} (opacity: {1!s}%)".format(description, opacity)

class PaletteRGB(UserVector):
    item_class = RGB
    item_name = "color"
    def createDescription(self):
        return "Palette of {0:d} RGB colors".format(len(self))

class PaletteRGBA(PaletteRGB):
    item_class = RGBA
    def createDescription(self):
        return "Palette of {0:d} RGBA colors".format(len(self))

