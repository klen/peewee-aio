""" Generic fields for peewee."""

from __future__ import annotations

from typing import (  # py38, py39
    TYPE_CHECKING,
    Generic,
    Literal,
    Optional,
    Type,
    overload,
)

import peewee as pw

if TYPE_CHECKING:
    from collections.abc import Awaitable
    from datetime import date, datetime, time
    from uuid import UUID

    from typing_extensions import Self  # py38, py39, py310

    from .model import AIOModel

from .types import TV


class GenericField(Generic[TV]):
    @overload
    def __get__(self, instance: None, owner) -> Self:
        ...

    @overload
    def __get__(self: GenericField[TV], instance: pw.Model, owner) -> TV:
        ...

    def __get__(self, instance: Optional[pw.Model], owner):
        ...


class IntegerField(pw.IntegerField, GenericField[TV]):
    @overload
    def __init__(self: IntegerField[int], *args, null: Literal[False] = ..., **kwargs):
        ...

    @overload
    def __init__(self: IntegerField[Optional[int]], *args, null: Literal[True] = ..., **kwargs):
        ...

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class BigIntegerField(pw.BigIntegerField, GenericField[TV]):
    @overload
    def __init__(self: BigIntegerField[int], *args, null: Literal[False] = ..., **kwargs):
        ...

    @overload
    def __init__(self: BigIntegerField[Optional[int]], *args, null: Literal[True] = ..., **kwargs):
        ...

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class SmallIntegerField(pw.SmallIntegerField, GenericField[TV]):
    @overload
    def __init__(self: SmallIntegerField[int], *args, null: Literal[False] = ..., **kwargs):
        ...

    @overload
    def __init__(
        self: SmallIntegerField[Optional[int]],
        *args,
        null: Literal[True] = ...,
        **kwargs,
    ):
        ...

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class AutoField(pw.AutoField, GenericField[TV]):
    @overload
    def __init__(self: AutoField[int], *args, null: Literal[False] = ..., **kwargs):
        ...

    @overload
    def __init__(self: AutoField[Optional[int]], *args, null: Literal[True] = ..., **kwargs):
        ...

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class BigAutoField(pw.BigAutoField, GenericField[TV]):
    @overload
    def __init__(self: BigAutoField[int], *args, null: Literal[False] = ..., **kwargs):
        ...

    @overload
    def __init__(self: BigAutoField[Optional[int]], *args, null: Literal[True] = ..., **kwargs):
        ...

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class IdentityField(pw.IdentityField, GenericField[TV]):
    @overload
    def __init__(self: IdentityField[int], *args, null: Literal[False] = ..., **kwargs):
        ...

    @overload
    def __init__(self: IdentityField[Optional[int]], *args, null: Literal[True] = ..., **kwargs):
        ...

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class FloatField(pw.FloatField, GenericField[TV]):
    @overload
    def __init__(self: FloatField[float], *args, null: Literal[False] = ..., **kwargs):
        ...

    @overload
    def __init__(self: FloatField[Optional[float]], *args, null: Literal[True] = ..., **kwargs):
        ...

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class DoubleField(pw.DoubleField, GenericField[TV]):
    @overload
    def __init__(self: DoubleField[float], *args, null: Literal[False] = ..., **kwargs):
        ...

    @overload
    def __init__(self: DoubleField[Optional[float]], *args, null: Literal[True] = ..., **kwargs):
        ...

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class DecimalField(pw.DecimalField, GenericField[TV]):
    @overload
    def __init__(self: DecimalField[float], *args, null: Literal[False] = ..., **kwargs):
        ...

    @overload
    def __init__(self: DecimalField[Optional[float]], *args, null: Literal[True] = ..., **kwargs):
        ...

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class CharField(pw.CharField, GenericField[TV]):
    @overload
    def __init__(self: CharField[str], *args, null: Literal[False] = ..., **kwargs):
        ...

    @overload
    def __init__(self: CharField[Optional[str]], *args, null: Literal[True] = ..., **kwargs):
        ...

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class FixedCharField(pw.FixedCharField, GenericField[TV]):
    @overload
    def __init__(self: FixedCharField[str], *args, null: Literal[False] = ..., **kwargs):
        ...

    @overload
    def __init__(self: FixedCharField[Optional[str]], *args, null: Literal[True] = ..., **kwargs):
        ...

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class TextField(pw.TextField, GenericField[TV]):
    @overload
    def __init__(self: TextField[str], *args, null: Literal[False] = ..., **kwargs):
        ...

    @overload
    def __init__(self: TextField[Optional[str]], *args, null: Literal[True] = ..., **kwargs):
        ...

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class BlobField(pw.BlobField, GenericField[TV]):
    @overload
    def __init__(self: BlobField[bytes], *args, null: Literal[False] = ..., **kwargs):
        ...

    @overload
    def __init__(self: BlobField[Optional[bytes]], *args, null: Literal[True] = ..., **kwargs):
        ...

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class BitField(pw.BitField, GenericField[TV]):
    @overload
    def __init__(self: BitField[int], *args, null: Literal[False] = ..., **kwargs):
        ...

    @overload
    def __init__(self: BitField[Optional[int]], *args, null: Literal[True] = ..., **kwargs):
        ...

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class BigBitField(pw.BigBitField, GenericField[TV]):
    @overload
    def __init__(self: BigBitField[bytes], *args, null: Literal[False] = ..., **kwargs):
        ...

    @overload
    def __init__(self: BigBitField[Optional[bytes]], *args, null: Literal[True] = ..., **kwargs):
        ...

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class UUIDField(pw.UUIDField, GenericField[TV]):
    @overload
    def __init__(self: UUIDField[UUID], *args, null: Literal[False] = ..., **kwargs):
        ...

    @overload
    def __init__(self: UUIDField[Optional[UUID]], *args, null: Literal[True] = ..., **kwargs):
        ...

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class BinaryUUIDField(pw.BinaryUUIDField, GenericField[TV]):
    @overload
    def __init__(self: BinaryUUIDField[UUID], *args, null: Literal[False] = ..., **kwargs):
        ...

    @overload
    def __init__(self: BinaryUUIDField[Optional[UUID]], *args, null: Literal[True] = ..., **kwargs):
        ...

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class DateTimeField(pw.DateTimeField, GenericField[TV]):
    @overload
    def __init__(self: DateTimeField[datetime], *args, null: Literal[False] = ..., **kwargs):
        ...

    @overload
    def __init__(
        self: DateTimeField[Optional[datetime]],
        *args,
        null: Literal[True] = ...,
        **kwargs,
    ):
        ...

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class DateField(pw.DateField, GenericField[TV]):
    @overload
    def __init__(self: DateField[date], *args, null: Literal[False] = ..., **kwargs):
        ...

    @overload
    def __init__(self: DateField[Optional[date]], *args, null: Literal[True] = ..., **kwargs):
        ...

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class TimeField(pw.TimeField, GenericField[TV]):
    @overload
    def __init__(self: TimeField[time], *args, null: Literal[False] = ..., **kwargs):
        ...

    @overload
    def __init__(self: TimeField[Optional[time]], *args, null: Literal[True] = ..., **kwargs):
        ...

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class TimestampField(pw.TimestampField, GenericField[TV]):
    @overload
    def __init__(self: TimestampField[int], *args, null: Literal[False] = ..., **kwargs):
        ...

    @overload
    def __init__(self: TimestampField[Optional[int]], *args, null: Literal[True] = ..., **kwargs):
        ...

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class IPField(pw.IPField, GenericField[TV]):
    @overload
    def __init__(self: IPField[str], *args, null: Literal[False] = ..., **kwargs):
        ...

    @overload
    def __init__(self: IPField[Optional[str]], *args, null: Literal[True] = ..., **kwargs):
        ...

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class BooleanField(pw.BooleanField, GenericField[TV]):
    @overload
    def __init__(self: BooleanField[bool], *args, null: Literal[False] = ..., **kwargs):
        ...

    @overload
    def __init__(self: BooleanField[Optional[bool]], *args, null: Literal[True] = ..., **kwargs):
        ...

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ForeignKeyField(pw.ForeignKeyField, GenericField[TV]):
    @overload
    def __init__(
        self: ForeignKeyField[Awaitable[TV]],
        model: Type[TV],
        *,
        null: Literal[False] = ...,
        **kwargs,
    ):
        ...

    @overload
    def __init__(
        self: ForeignKeyField[Awaitable[Optional[TV]]],
        model: Type[TV],
        *,
        null: Literal[True] = ...,
        **kwargs,
    ):
        ...

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class DeferredForeignKey(pw.DeferredForeignKey, GenericField[TV]):
    @overload
    def __init__(
        self: ForeignKeyField[Awaitable[AIOModel]],
        rel_model_name: str,
        *,
        null: Literal[False] = ...,
        **kwargs,
    ):
        ...

    @overload
    def __init__(
        self: ForeignKeyField[Awaitable[Optional[AIOModel]]],
        rel_model_name: str,
        *,
        null: Literal[True] = ...,
        **kwargs,
    ):
        ...

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


__all__ = [
    "GenericField",
    "IntegerField",
    "BigIntegerField",
    "SmallIntegerField",
    "AutoField",
    "BigAutoField",
    "IdentityField",
    "FloatField",
    "DoubleField",
    "DecimalField",
    "CharField",
    "FixedCharField",
    "TextField",
    "BlobField",
    "BitField",
    "BigBitField",
    "UUIDField",
    "BinaryUUIDField",
    "DateTimeField",
    "DateField",
    "TimeField",
    "TimestampField",
    "IPField",
    "BooleanField",
    "ForeignKeyField",
    "DeferredForeignKey",
]
