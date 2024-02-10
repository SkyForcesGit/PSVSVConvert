"""
Plug.
"""

# TODO: Finish code documenting.

# Standard library
import dataclasses as dat_cls
from typing import Any

# pylint: disable=import-error
# Custom modules
from consts import FlagsEnum, PropertyEnum


# pylint: disable=too-few-public-methods
@dat_cls.dataclass(slots=True)
class Property:
    """
    Plug.
    """
    property_key: int | str = dat_cls.field(default_factory=int)
    property_type: PropertyEnum = PropertyEnum.PROPERTY_INT
    property_value: bool | int | float | str = dat_cls.field(default_factory=int)


# =============================== TilesStart ================================


@dat_cls.dataclass(slots=True)
class Tile:
    """
    Plug.
    """
    type_id: str = dat_cls.field(default_factory=str)


@dat_cls.dataclass(slots=True)
class TileSkip(Tile):
    """
    Plug.
    """
    skip_size: int = dat_cls.field(default_factory=int)


@dat_cls.dataclass(slots=True)
class TileStatic(Tile):
    """
    Plug.
    """
    tile_id: int = dat_cls.field(default_factory=int)
    blend_value: int = dat_cls.field(default_factory=int)

    tile_properties_len: int = dat_cls.field(default_factory=int)
    tile_properties: list[Property] = dat_cls.field(default_factory=list)


@dat_cls.dataclass(slots=True)
class TileTilesheet(Tile):
    """
    Plug.
    """
    tilesheet_id: int | str = dat_cls.field(default_factory=int)


@dat_cls.dataclass(slots=True)
class TileAnimated(Tile):
    """
    Plug.
    """
    frame_interval: int = dat_cls.field(default_factory=int)
    frame_count: int = dat_cls.field(default_factory=int)

    tilemap: list[Tile] = dat_cls.field(default_factory=list)
    tile_properties_len: int = dat_cls.field(default_factory=int)
    tile_properties: list[Property] = dat_cls.field(default_factory=list)


# =============================== TilesEnd ================================


# pylint: disable=too-many-instance-attributes
@dat_cls.dataclass(slots=True)
class TileSheet:
    """
    Plug.
    """
    id_: int | str = dat_cls.field(default_factory=int)
    description: int | str = dat_cls.field(default_factory=int)
    source_image: int | str = dat_cls.field(default_factory=int)

    sheet_size: tuple[int, int] = dat_cls.field(default_factory=tuple[int, int])
    tile_size: tuple[int, int] = dat_cls.field(default_factory=tuple[int, int])
    margin: tuple[int, int] = dat_cls.field(default_factory=tuple[int, int])
    spacing: tuple[int, int] = dat_cls.field(default_factory=tuple[int, int])

    sheet_properties_len: int = dat_cls.field(default_factory=int)
    sheet_properties: list[Property] = dat_cls.field(default_factory=list)


@dat_cls.dataclass(slots=True)
class Layer:
    """
    Plug.
    """
    id_: int | str = dat_cls.field(default_factory=int)
    visible: bool = dat_cls.field(default_factory=bool)
    description: int | str = dat_cls.field(default_factory=int)

    layer_size: tuple[int, int] = dat_cls.field(default_factory=tuple[int, int])
    tile_size: tuple[int, int] = dat_cls.field(default_factory=tuple[int, int])

    len_layer_properties: int = dat_cls.field(default_factory=int)
    layer_properties: list[Property] = dat_cls.field(default_factory=list)
    tilemap: list[Tile] = dat_cls.field(default_factory=list)


@dat_cls.dataclass(slots=True)
class Map:
    """
    Plug.
    """
    id_: int | str = dat_cls.field(default_factory=int)
    description: int | str = dat_cls.field(default_factory=int)

    map_properties_len: int = dat_cls.field(default_factory=int)
    map_properties: list[Property] = dat_cls.field(default_factory=list)
    map_tilesheets_len: int = dat_cls.field(default_factory=int)
    map_tilesheets: list[TileSheet] = dat_cls.field(default_factory=list)
    map_layers_len: int = dat_cls.field(default_factory=int)
    map_layers: list[Layer] = dat_cls.field(default_factory=list)
    map_strings: list[str] = dat_cls.field(default_factory=list)


flags: list = [getattr(FlagsEnum, attr) for attr in
               list(filter(lambda y: not y.startswith('__'), dir(FlagsEnum)))[:-1:]]


# noinspection PyDataclass, PyTypeChecker
def map_iter(obj: object) -> Any:
    """
    Plug.
    :param obj:
    :return:
    """
    match obj:
        case tuple((flag, _)) if flag in flags:
            yield obj
        case tuple() | list():
            for item in obj:
                yield from map_iter(item)
        case Map() | Property() | TileSheet() | Layer() | Tile():
            for field in dat_cls.fields(obj):
                if field.name == "map_strings":
                    continue
                yield from map_iter(getattr(obj, field.name))
        case _:
            yield obj
