"""
Plug.
"""

# TODO: Finish code documenting.

# Standard library
import enum


# pylint: disable=too-few-public-methods
# Constants
class Consts:
    """
    Plug.
    """
    CODEC: str = "ASCII"
    CONVERT_PSV: str = "psv"
    CONVERT_PC: str = "pc"
    BIN_DUMP_SIZE: int = 20
    HEADER_PSV: bytes = "tBIN11".encode(CODEC)
    HEADER_PC: bytes = "tBIN10".encode(CODEC)
    SEG_STR_START: bytes = b"\x1A\x1A\x1A\x00"
    SEG_STR_END: bytes = b"\x37\x37\x37\x00"


class FlagsEnum(enum.IntEnum):
    """
    Plug.
    """
    STR_SEG_FLAG: int = 0x1A1A1A00
    POINTER_FLAG: int = 0x706F696E746572
    BOOL_FLAG: int = 0x626F6F6C
    STRING_FLAG: int = 0x737472696E67


class ColorsEnum(enum.StrEnum):
    """
    Plug.
    """
    HEADER: str = '\033[95m'
    OKBLUE: str = '\033[94m'
    OKCYAN: str = '\033[96m'
    OKGREEN: str = '\033[92m'
    WARNING: str = '\033[93m'
    FAIL: str = '\033[91m'
    ENDC: str = '\033[0m'


class SizesEnum(enum.IntEnum):
    """
    Plug.
    """
    HEADER: int = 0x06
    FLOAT: int = 0x04
    UINT32: int = 0x04
    UINT16: int = 0x02
    UINT8: int = 0x01


class PropertyEnum(enum.IntEnum):
    """
    Plug.
    """
    PROPERTY_BOOL: int = 0x00
    PROPERTY_INT: int = 0x01
    PROPERTY_FLOAT: int = 0x02
    PROPERTY_STRING: int = 0x03
