""" Generic fields for peewee."""

from __future__ import annotations

from datetime import date, datetime, time
from typing import TYPE_CHECKING, Any, Generic, overload
from uuid import UUID

import peewee as pw

if TYPE_CHECKING:
    from typing_extensions import Self  # py37, py38, py39, py310

from .types import TV


class GenericField(Generic[TV]):
    name: str

    @overload
    def __get__(self, instance: None, owner) -> Self:
        ...

    @overload
    def __get__(self, instance: pw.Model, owner) -> TV:
        ...

    def __get__(self, instance: pw.Model | None, owner):
        if instance is None:
            return self

        return instance.__data__[self.name]


class IntegerField(pw.IntegerField, GenericField[int]):
    pass


class BigIntegerField(pw.BigIntegerField, GenericField[int]):
    pass


class SmallIntegerField(pw.SmallIntegerField, GenericField[int]):
    pass


class AutoField(pw.AutoField, GenericField[int]):
    pass


class BigAutoField(pw.BigAutoField, GenericField[int]):
    pass


class IdentityField(pw.IdentityField, GenericField[int]):
    pass


class FloatField(pw.FloatField, GenericField[float]):
    pass


class DoubleField(pw.DoubleField, GenericField[float]):
    pass


class DecimalField(pw.DecimalField, GenericField[float]):
    pass


class CharField(pw.CharField, GenericField[str]):
    pass


class FixedCharField(pw.FixedCharField, GenericField[str]):
    pass


class TextField(pw.TextField, GenericField[str]):
    pass


class BlobField(pw.BlobField, GenericField[bytes]):
    pass


class BitField(pw.BitField, GenericField[int]):
    pass


class BigBitField(pw.BigBitField, GenericField[bytes]):
    pass


class UUIDField(pw.UUIDField, GenericField[UUID]):
    pass


class BinaryUUIDField(pw.BinaryUUIDField, GenericField[UUID]):
    pass


class DateTimeField(pw.DateTimeField, GenericField[datetime]):
    pass


class DateField(pw.DateField, GenericField[date]):
    pass


class TimeField(pw.TimeField, GenericField[time]):
    pass


class TimestampField(pw.TimestampField, GenericField[int]):
    pass


class IPField(pw.IPField, GenericField[str]):
    pass


class BooleanField(pw.BooleanField, GenericField[bool]):
    pass


class ForeignKeyField(pw.ForeignKeyField, GenericField[Any]):
    pass


class DeferredForeignKey(pw.DeferredForeignKey, GenericField[Any]):
    pass


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
