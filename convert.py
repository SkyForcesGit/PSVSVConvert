"""
Plug.
"""

# TODO: Finish code documenting.

# Standard library
import struct
import functools
import pprint
import argparse
import os
import sys
import zlib
import re
import dataclasses as dat_cls
from typing import Any, Callable, BinaryIO
from tkinter import filedialog

# pylint: disable=import-error
# Custom modules
import map_classes
from consts import Consts, ColorsEnum, SizesEnum, PropertyEnum, FlagsEnum


# pylint: disable=too-few-public-methods
class Converter:
    """
    Plug.
    """

    # =============================== ExceptionsStart =========================

    class ArgumentError(Exception):
        """
        Plug.
        """

    class PropertyError(Exception):
        """
        Plug.
        """

    class TileError(Exception):
        """
        Plug.
        """

    class WriteError(Exception):
        """
        Plug.
        """

    # =============================== ExceptionsEnd ===========================

    @staticmethod
    def __print_info(string: str) -> None:
        """
        Plug.
        :param string:
        :return:
        """
        print(f"{ColorsEnum.OKBLUE}[INFO]{ColorsEnum.ENDC} {string} - "
              f"{ColorsEnum.OKGREEN}ok!{ColorsEnum.ENDC}")

    # pylint: disable=protected-access
    @staticmethod
    def __error_handler(subfunction: Callable[[Any, ...], Any]) \
            -> Callable[[Any, ...], Any]:
        """
        Plug.
        :param subfunction:
        :return:
        """

        @functools.wraps(subfunction)
        def inner_function(self, *args, **kwargs) -> Any | None:
            """
            Plug.
            :param self:
            :param args:
            :param kwargs:
            :return:
            """

            def print_error(exc_: Exception) -> None:
                """
                Plug.
                :param exc_:
                :return:
                """
                print(f"{ColorsEnum.FAIL}[{exc_.__class__.__name__}] {exc_}"
                      f"{ColorsEnum.ENDC}")

            try:
                result = subfunction(self, *args, **kwargs)
                return result
            except self.ArgumentError as exc:
                print_error(exc)
                sys.exit(0)
            except (self.PropertyError, self.TileError) as exc:
                read_pos = self.__binary_stream.tell()
                self.__binary_stream.seek(read_pos - Consts.BIN_DUMP_SIZE if
                                          read_pos - Consts.BIN_DUMP_SIZE > 0
                                          else 0)
                bin_dump = self.__binary_stream.read(Consts.BIN_DUMP_SIZE * 2)

                print_error(exc)
                self.__print_info("Creating binary dump (last 40 bytes)")
                print(bin_dump.hex(sep=" "))
                with open("map_listing_error.txt", mode="w", encoding="utf-8") as file:
                    pprint.pprint(self.__map, stream=file)
            except self.WriteError as exc:
                print_error(exc)
                with open("map_listing_error.txt", mode="w", encoding="utf-8") as file:
                    pprint.pprint(self.__map, stream=file)
            except Exception as exc:
                print_error(exc)
                raise

            sys.exit(1)

        return inner_function

    @__error_handler
    def __init__(self, source_file: str, conv_format: str) -> None:
        """
        Plug.
        :raises Converter.ArgumentError:
        :param source_file:
        :param conv_format:
        """
        self.__source_file: str = source_file
        self.__binary_stream: BinaryIO | None = None
        self.__mode: str | None = None
        match conv_format:
            case Consts.CONVERT_PSV | Consts.CONVERT_PC:
                self.__mode = conv_format
            case _:
                raise self.ArgumentError(f"Wrong format argument: '{conv_format}'. "
                                         "Must be 'psv' or 'pc'. Check --help.")

        if not source_file.endswith((".tbin", ".tbinpc", "tbinpsv")):
            raise self.ArgumentError(f"Wrong format argument: {source_file}. "
                                     "Must contain '.tbin[pc | psv]' extension. "
                                     "Check --help.")

        self.__map: map_classes.Map = map_classes.Map()
        self.__parse_file()

    # =============================== StructsStart ============================

    @staticmethod
    def __create_struct_float(data: float) -> bytes:
        """
        Packs data as a floating-point value.
        :return: floating-point value in bytes representation
        """
        return struct.pack("<f",  # Little-endian uint32 (uint)
                           data)

    @staticmethod
    def __create_struct_uint32(data: int) -> bytes:
        """
        Packs data as an 32-bit unsigned int.
        :return: 32-bit unsigned int in bytes representation
        """
        return struct.pack("<I",  # Little-endian uint32 (uint)
                           data)

    @staticmethod
    def __create_struct_uint16(data: int) -> bytes:
        """
        Packs data as an 16-bit unsigned int.
        :return: 16-bit unsigned int in bytes representation
        """
        return struct.pack("<H",  # Little-endian uint16 (ushort)
                           data)

    @staticmethod
    def __create_struct_uint8(data: int) -> bytes:
        """
        Packs data as an 8-bit unsigned int.
        :return: 8-bit unsigned int in bytes representation
        """
        return struct.pack("<B",  # Little-endian uint8 (uchar)
                           data)

    def __get_struct_float(self) -> float:
        """
        Unpacks read data from 'Converter.__binary_stream' as a
        floating-point value.
        :return: Floating-point value
        """
        return struct.unpack("<f",  # Little-endian uint32 (uint)
                             self.__binary_stream.read(SizesEnum.FLOAT))[0]

    def __get_struct_uint32(self) -> int:
        """
        Unpacks read data from 'Converter.__binary_stream' as an
        32-bit unsigned int.
        :return: Integer value
        """
        return struct.unpack("<I",  # Little-endian uint32 (uint)
                             self.__binary_stream.read(SizesEnum.UINT32))[0]

    def __get_struct_string(self) -> tuple[int, int | str]:
        """
        Unpacks read data from 'Converter.__binary_stream' as:

        * 16-bit unsigned int and marks it with flag as a pointer to string
          (if PS Vita -> PC)
        * ASCII-string with string flag, which also specially preprocessed if
          contains path (if PC -> PS Vita)
        :return: Tuple of 'consts.FlagsEnum.STRING_FLAG' or
                 'consts.FlagsEnum.POINTER_FLAG' and read value/string
        """
        match self.__mode:
            case Consts.CONVERT_PC:
                return (FlagsEnum.POINTER_FLAG,
                        struct.unpack("<H",  # Little-endian uint16 (ushort)
                                      self.__binary_stream.read(SizesEnum.UINT16))[0])
            case Consts.CONVERT_PSV:
                str_len: int = self.__get_struct_uint32()
                string: str = self.__binary_stream.read(str_len).decode(Consts.CODEC)

                # If string is a path-like, removing everything excluding filename
                pattern: re.Pattern = re.compile(
                    r"^(?:[A-Za-z.0-9_!\-]*[/\\])*[A-Za-z0-9!\-_]*\.[A-Za-z]*$"
                )
                if re.match(pattern, string):
                    string = string.split("/\\")[-1].split(".")[0]

                self.__map.map_strings.append(string)
                return FlagsEnum.STRING_FLAG, string

    def __get_struct_uint8(self) -> tuple[int, int]:
        """
        Unpacks read data from 'Converter.__binary_stream' as an
        8-bit unsigned int and marks it with flag as boolean data.
        :return: Tuple of 'consts.FlagsEnum.BOOL_FLAG' and read value
        """
        return (FlagsEnum.BOOL_FLAG,
                struct.unpack("<B",  # Little-endian uint8 (uchar)
                              self.__binary_stream.read(SizesEnum.UINT8))[0])

    # =============================== StructsEnd ==============================

    @__error_handler
    def __read_property_value(self) -> map_classes.Property:
        """
        Parse information about separate object property to the
        'map_classes.Property' instance, which after stores in
        object properties list.

        **Parsed information:**

        * Property key
        * Property type - members of 'consts.PropertyEnum'
        * Property value according to the type
        :raises Converter.PropertyError: Raises if read property type doesn't
               match any of 'consts.PropertyEnum' members
        :return: Instance of 'map_classes.Property'
        """
        temp_prop = map_classes.Property()
        temp_prop.property_key = self.__get_struct_string()
        temp_prop.property_type = self.__get_struct_uint8()

        match temp_prop.property_type[-1]:
            case PropertyEnum.PROPERTY_BOOL:
                temp_prop.property_value = self.__get_struct_uint8()
            case PropertyEnum.PROPERTY_INT:
                temp_prop.property_value = self.__get_struct_uint32()
            case PropertyEnum.PROPERTY_FLOAT:
                temp_prop.property_value = self.__get_struct_float()
            case PropertyEnum.PROPERTY_STRING:
                temp_prop.property_value = self.__get_struct_string()
            case _:
                raise self.PropertyError("Incorrect property type: "
                                         f"{temp_prop.property_type} at "
                                         f"{self.__binary_stream.tell():#X}")

        return temp_prop

    @__error_handler
    def __read_tilesheet(self) -> map_classes.TileSheet:
        """
        Parse information about separate map tilesheet to the
        'map_classes.Tilesheet' instance, which after stores in
        'map_classes.Map' tilesheets list.

         **Parsed information:**

         * Tilesheet id
         * Tilesheet description
         * Path to the tilesheet source image
         * Tilesheet sizes in tiles (tuple)
         * Tile sizes (tuple)
         * Tilesheet properties - list of 'map_classes.Property'
        :return: Instance of 'map_classes.Tilesheet'
        """
        temp_tilesheet: map_classes.TileSheet = map_classes.TileSheet()

        # Getting tilesheet id, description and source image
        for field in dat_cls.fields(temp_tilesheet)[:3]:
            setattr(temp_tilesheet, field.name, self.__get_struct_string())

        # Getting tilesheet sizes in tiles, getting tile sizes
        for field in dat_cls.fields(temp_tilesheet)[3:7]:
            setattr(temp_tilesheet, field.name,
                    tuple(self.__get_struct_uint32() for _ in range(2)))

        temp_tilesheet.sheet_properties_len = self.__get_struct_uint32()
        for _ in range(temp_tilesheet.sheet_properties_len):
            temp_tilesheet.sheet_properties.append(self.__read_property_value())

        return temp_tilesheet

    @__error_handler
    def __read_layer(self) -> map_classes.Layer:
        """
        Parse information about separate map layer to the
        'map_classes.Layer' instance, which after stores in
        'map_classes.Map' layers list.

        **Parsed information:**

        * Layer id
        * Layer visibility value
        * Layer description
        * Layer sizes in tiles (tuple)
        * Tile sizes (tuple)
        * Layer properties - list of 'map_classes.Property'
        * Layer tilemap - list of 'map_classes.Tile' subclasses

        :raises Converter.TileError: Raises if read tile type doesn't
                match any of valid values ('S', 'T', 'N', 'A')
        :return: Instance of 'map_classes.Layer'
        """
        temp_layer: map_classes.Layer = map_classes.Layer()

        temp_layer.id_ = self.__get_struct_string()
        temp_layer.visible = self.__get_struct_uint8()
        temp_layer.description = self.__get_struct_string()

        # Getting layer sizes in tiles, getting tile sizes
        for field in dat_cls.fields(temp_layer)[3:5]:
            setattr(temp_layer, field.name,
                    tuple(self.__get_struct_uint32() for _ in range(2)))
        temp_layer.len_layer_properties = self.__get_struct_uint32()
        for _ in range(temp_layer.len_layer_properties):
            temp_layer.layer_properties.append(self.__read_property_value())

        count: int = 0
        while count < functools.reduce(lambda x, y: x * y,
                                       temp_layer.layer_size):
            match symbol_ := chr(self.__get_struct_uint8()[-1]):
                case "N":
                    tile, tile_skip = self.__skip_tile(symbol_)
                    temp_layer.tilemap.append(tile)
                    count += tile_skip
                case "T":
                    tile = self.__tilesheet_tile(symbol_)
                    temp_layer.tilemap.append(tile)
                    # count += 1
                case "S":
                    tile = self.__static_tile(symbol_)
                    temp_layer.tilemap.append(tile)
                    count += 1
                case "A":
                    tile = self.__animated_tile(symbol_)
                    temp_layer.tilemap.append(tile)
                    count += 1
                case _:
                    raise self.TileError(f"Unrecognised tile type: {symbol_}"
                                         f" at {self.__binary_stream.tell():#X}.")

        return temp_layer

    # =============================== TilesStart ==============================

    @__error_handler
    def __skip_tile(self, symbol_: str) -> tuple[map_classes.TileSkip, int]:
        """
        Parse information about skip tile (describes
        quantity of empty tiles) to the layer ('map_classes.Layer') tilemap.

        **Parsed information:**

        * Tile type ('N')
        * Quantity of skip tiles
        :param symbol_: Tile type ('N' in that case)
        :return: Tuple with instance of 'map_classes.TileTilesheet'
                 and quantity of skip tiles, which use in the external method
        """
        tile: map_classes.TileSkip = map_classes.TileSkip()
        tile.type_id = symbol_
        tile.skip_size = self.__get_struct_uint32()

        return tile, tile.skip_size

    @__error_handler
    def __tilesheet_tile(self, symbol_: str) -> map_classes.TileTilesheet:
        """
        Parse information about tilesheet tile (selects the
        active tilesheet) to the layer ('map_classes.Layer') tilemap.

        **Parsed information:**

        * Tile type ('T')
        * Selected tilesheet id
        :param symbol_: Tile type ('T' in that case)
        :return: Instance of 'map_classes.TileTilesheet'
        """
        tile: map_classes.TileTilesheet = map_classes.TileTilesheet()
        tile.type_id = symbol_
        tile.tilesheet_id = self.__get_struct_string()

        return tile

    @__error_handler
    def __static_tile(self, symbol_: str) -> map_classes.TileStatic:
        """
        Parse information about static tile (without animation)
        to the layer ('map_classes.Layer') tilemap.

        **Parsed information:**

        * Tile type ('S')
        * Tile blend value
        * Frame count
        * Animated tile properties - list of 'map_classes.Property'
        :param symbol_: Tile type ('S' in that case)
        :return: Instance of 'map_classes.TileStatic'
        """
        tile: map_classes.TileStatic = map_classes.TileStatic()
        tile.type_id = symbol_
        tile.tile_id = self.__get_struct_uint32()
        tile.blend_value = self.__get_struct_uint8()

        tile.tile_properties_len = self.__get_struct_uint32()
        for _ in range(tile.tile_properties_len):
            tile.tile_properties.append(self.__read_property_value())

        return tile

    @__error_handler
    def __animated_tile(self, symbol_: str) -> map_classes.TileAnimated:
        """
        Parse information about animated tile to the layer
        ('map_classes.Layer') tilemap.

        **Parsed information:**

        * Tile type ('A')
        * Frame interval time
        * Frame count
        * Animated tile tilemap - list of 'map_classes.TileStatic' or
          'map_classes.TileTilesheet'
        * Animated tile properties - list of 'map_classes.Property'
        :raises Converter.TileError: Raises if read tile type doesn't
                match any of valid values ('S', 'T')
        :param symbol_: Tile type ('A' in that case)
        :return: Instance of 'map_classes.TileAnimated'
        """
        tile: map_classes.TileAnimated = map_classes.TileAnimated()
        tile.type_id = symbol_
        tile.frame_interval = self.__get_struct_uint32()
        tile.frame_count = self.__get_struct_uint32()

        count: int = 0
        while count <= tile.frame_count:
            match symbol_ := chr(self.__get_struct_uint8()[-1]):
                case "S":
                    tile_ = self.__static_tile(symbol_)
                case "T":
                    tile_ = self.__tilesheet_tile(symbol_)
                case _:
                    raise self.TileError(f"Unrecognised tile type: {symbol_}"
                                         f" at {self.__binary_stream.tell():#X}.")

            tile.tilemap.append(tile_)
            count += 1

        tile.tile_properties_len = self.__get_struct_uint32()
        for _ in range(tile.tile_properties_len):
            tile.tile_properties.append(self.__read_property_value())

        return tile

    # =============================== TilesEnd ================================

    @__error_handler
    def __parse_file(self) -> None:
        """
        Parsing '*.tbin' file in PS Vita tBIN11/PC tBIN10 binary
        format to the 'map_classes.Map' class instance.

        After that method starts conversion into the selected via
        argument ('Mode' - 'pc'/'psv') format.

        **Parsed information:**

        * Map id
        * Map description
        * Map properties - list of 'map_classes.Property'
        * Map tilesheets information - list of 'map_classes.Tilesheet'
        * Map layers information - list of 'map_classes.Layer'
        :raises Converter.ArgumentError: raises if file format doesn't match
                selected conversion mode
        :return: None
        """
        self.__map: map_classes.Map = map_classes.Map()
        with open(self.__source_file, mode="rb") as binary_stream:
            self.__binary_stream = binary_stream

            print(f"{ColorsEnum.HEADER}File: {self.__source_file}\n"
                  f"Mode: to {self.__mode.upper()}{ColorsEnum.ENDC}")

            # Getting basic header information
            format_id: bytes = self.__binary_stream.read(SizesEnum.HEADER)
            match self.__mode:
                case Consts.CONVERT_PSV:
                    if format_id != Consts.HEADER_PC:
                        raise self.ArgumentError("Selected wrong mode for conversion")
                case Consts.CONVERT_PC:
                    if format_id != Consts.HEADER_PSV:
                        raise self.ArgumentError("Selected wrong mode for conversion")

            self.__map.id_ = self.__get_struct_string()
            self.__map.description = self.__get_struct_string()
            self.__print_info("Reading map ID and description")

            # Getting map properties
            self.__map.map_properties_len = self.__get_struct_uint32()
            for _ in range(self.__map.map_properties_len):
                self.__map.map_properties.append(self.__read_property_value())
            self.__print_info("Reading map properties")

            # Getting map tilesheets
            self.__map.map_tilesheets_len = self.__get_struct_uint32()
            for _ in range(self.__map.map_tilesheets_len):
                self.__map.map_tilesheets.append(self.__read_tilesheet())
            self.__print_info("Reading map tilesheets")

            # Getting map layers
            self.__map.map_layers_len = self.__get_struct_uint32()
            for _ in range(self.__map.map_layers_len):
                self.__map.map_layers.append(self.__read_layer())
            self.__print_info("Reading map layers")

            match self.__mode:
                case Consts.CONVERT_PC:
                    # Getting strings segment
                    self.__get_struct_uint32()  # Start of string segment
                    # -> 1A 1A 1A 00
                    string_block_len: int = self.__get_struct_uint32()
                    for _ in range(string_block_len):
                        str_len: int = self.__get_struct_uint32()
                        self.__map.map_strings.append(self.__binary_stream.
                                                      read(str_len).decode(Consts.CODEC))
                    self.__get_struct_uint32()  # Bytes quantity in the main segment
                    self.__get_struct_uint32()  # End of string segment -> 37 37 37 00

                    self.__convert_to_pc()

                case Consts.CONVERT_PSV:
                    self.__map.map_strings = list(dict.fromkeys(self.__map.map_strings))
                    self.__map.map_strings.insert(0, FlagsEnum.STR_SEG_FLAG)

                    self.__convert_to_psv()

            self.__print_info("Converting map")
            self.__binary_stream.seek(0)
            self.__print_info(f"Original file CRC32: {zlib.crc32(
                self.__binary_stream.read()):08X}")

    def __convert_to_psv(self) -> None:
        """
        Packs previously read 'map_classes.Map' class instance
        as '*.tbin' file in PS Vita tBIN11 binary format.
        :raises Converter.WriteError: Raises if script cannot pack and
                write to file some information
        :return: None
        """
        written_bytes: int = 0
        # Converting map to PSV format and writing to the file
        with open(f"{self.__source_file}psv".replace("pc", ""),
                  mode="wb+") as output:
            written_bytes += output.write(Consts.HEADER_PSV)
            for item in map_classes.map_iter(self.__map):
                try:
                    match item:
                        case tuple((FlagsEnum.STRING_FLAG, point_index)):
                            written_bytes += output.write(
                                self.__create_struct_uint16(
                                    self.__map.map_strings.index(point_index) - 1
                                )
                            )
                        case tuple((FlagsEnum.BOOL_FLAG, value)):
                            written_bytes += output.write(
                                self.__create_struct_uint8(value))
                        case float(value):
                            written_bytes += output.write(
                                self.__create_struct_float(value))
                        case str(value) if len(value) == 1:
                            written_bytes += output.write(ord(value).to_bytes())
                        case FlagsEnum.STR_SEG_FLAG:
                            break
                        case int(value):
                            written_bytes += output.write(
                                self.__create_struct_uint32(value))
                        case _:
                            raise self.WriteError(f"Following element ({item})"
                                                  f"doesn't match any pattern")
                except (struct.error, IOError) as exc:
                    raise self.WriteError(f"Write error ({exc}) on following "
                                          f"element: {item}")

            output.write(Consts.SEG_STR_START)
            output.write(self.__create_struct_uint32(len(self.__map.map_strings)
                                                     - 1))
            for str_ in self.__map.map_strings[1::]:
                output.write(self.__create_struct_uint32(len(str_)))
                output.write(str_.encode(Consts.CODEC))
            output.write(self.__create_struct_uint32(written_bytes))
            output.write(Consts.SEG_STR_END)

            output.seek(0)
            self.__print_info(f"Converted file CRC32: {zlib.crc32(
                output.read()):08X}")

    def __convert_to_pc(self) -> None:
        """
        Packs previously read 'map_classes.Map' class instance
        as '*.tbin' file in PC tBIN10 binary format.
        :raises Converter.WriteError: Raises if script cannot pack and
                write to file some information
        :return: None
        """
        # Converting map to PC format and writing to the file
        with open(f"{self.__source_file}pc".replace("psv", ""),
                  mode="wb+") as output:
            output.write(Consts.HEADER_PC)
            for item in map_classes.map_iter(self.__map):
                try:
                    match item:
                        case tuple((FlagsEnum.POINTER_FLAG, point_index)):
                            item_: str = self.__map.map_strings[point_index]
                            output.write(self.__create_struct_uint32(len(item_)))
                            output.write(item_.encode(Consts.CODEC))
                        case tuple((FlagsEnum.BOOL_FLAG, value)):
                            output.write(self.__create_struct_uint8(value))
                        case float(value):
                            output.write(self.__create_struct_float(value))
                        case str(value) if len(value) == 1:
                            output.write(ord(value).to_bytes())
                        case int(value):
                            output.write(self.__create_struct_uint32(value))
                        case _:
                            raise self.WriteError(f"Following element ({item})"
                                                  f"doesn't match any pattern")
                except (struct.error, IOError) as exc:
                    raise self.WriteError(f"Write error ({exc}) on following "
                                          f"element: {item}")

            output.seek(0)
            self.__print_info(f"Converted file CRC32: {zlib.crc32(
                output.read()):08X}")


def converter(data_path: str, mode: str) -> None:
    """
    Plug.
    :param data_path:
    :param mode:
    :return:
    """
    if not os.path.exists(data_path) or not os.path.isfile(data_path):
        data_path = filedialog.askopenfilename()
        if data_path == '':
            return None

    Converter(data_path, mode.lower())
    return None


if __name__ == "__main__":
    # Setting up script arguments and description
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Converts Stardew Valley map files from PS Vita format to "
                    "PC one and back.")
    parser.add_argument("data_path", metavar="Path", type=str,
                        help="Path to file ('.tbin[pc | psv]' extension) which "
                             "needs to be converted.")
    parser.add_argument("mode", metavar="Mode", type=str,
                        help="Mode to convert the file to: "
                             "'psv' - PC to PS Vita format,"
                             "'pc' - PS Vita to PC format.")

    arguments = parser.parse_args()
    converter(arguments.data_path, arguments.mode)
