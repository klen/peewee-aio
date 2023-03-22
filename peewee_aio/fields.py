""" Generic fields for peewee."""

from __future__ import annotations

from typing import (  # py38, py39
    TYPE_CHECKING,
    Coroutine,
    Generic,
    Literal,
    Optional,
    Type,
    Union,
    overload,
)

import peewee as pw

if TYPE_CHECKING:
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
    def __get__(self: GenericField[TV], instance: object, owner) -> TV:
        ...

    def __get__(  # type: ignore[empty-body]
        self, instance: Optional[object], owner
    ) -> Union[Self, TV]:
        ...

    def __set__(self, instance: object, value: TV) -> None:
        ...


class IntegerField(pw.IntegerField, GenericField[TV]):
    if TYPE_CHECKING:

        @overload
        def __new__(cls, *args, null: Literal[False] = ..., **kwargs) -> IntegerField[int]:
            ...

        @overload
        def __new__(cls, *args, null: Literal[True] = ..., **kwargs) -> IntegerField[Optional[int]]:
            ...

        def __new__(cls, *args, **kwargs) -> Union[IntegerField[int], IntegerField[Optional[int]]]:
            ...


class BigIntegerField(pw.BigIntegerField, GenericField[TV]):
    if TYPE_CHECKING:

        @overload
        def __new__(cls, *args, null: Literal[False] = ..., **kwargs) -> BigIntegerField[int]:
            ...

        @overload
        def __new__(
            cls, *args, null: Literal[True] = ..., **kwargs
        ) -> BigIntegerField[Optional[int]]:
            ...

        def __new__(
            cls, *args, **kwargs
        ) -> Union[BigIntegerField[int], BigIntegerField[Optional[int]]]:
            ...


class SmallIntegerField(pw.SmallIntegerField, GenericField[TV]):
    if TYPE_CHECKING:

        @overload
        def __new__(cls, *args, null: Literal[False] = ..., **kwargs) -> SmallIntegerField[int]:
            ...

        @overload
        def __new__(
            cls, *args, null: Literal[True] = ..., **kwargs
        ) -> SmallIntegerField[Optional[int]]:
            ...

        def __new__(
            cls, *args, **kwargs
        ) -> Union[SmallIntegerField[int], SmallIntegerField[Optional[int]]]:
            ...


class AutoField(pw.AutoField, GenericField[TV]):
    if TYPE_CHECKING:

        @overload
        def __new__(cls, *args, null: Literal[False] = ..., **kwargs) -> AutoField[int]:
            ...

        @overload
        def __new__(cls, *args, null: Literal[True] = ..., **kwargs) -> AutoField[Optional[int]]:
            ...

        def __new__(cls, *args, **kwargs) -> Union[AutoField[int], AutoField[Optional[int]]]:
            ...


class BigAutoField(pw.BigAutoField, GenericField[TV]):
    if TYPE_CHECKING:

        @overload
        def __new__(cls, *args, null: Literal[False] = ..., **kwargs) -> BigAutoField[int]:
            ...

        @overload
        def __new__(cls, *args, null: Literal[True] = ..., **kwargs) -> BigAutoField[Optional[int]]:
            ...

        def __new__(cls, *args, **kwargs) -> Union[BigAutoField[int], BigAutoField[Optional[int]]]:
            ...


class IdentityField(pw.IdentityField, GenericField[TV]):
    if TYPE_CHECKING:

        @overload
        def __new__(cls, *args, null: Literal[False] = ..., **kwargs) -> IdentityField[int]:
            ...

        @overload
        def __new__(
            cls, *args, null: Literal[True] = ..., **kwargs
        ) -> IdentityField[Optional[int]]:
            ...

        def __new__(
            cls, *args, **kwargs
        ) -> Union[IdentityField[int], IdentityField[Optional[int]]]:
            ...


class FloatField(pw.FloatField, GenericField[TV]):
    if TYPE_CHECKING:

        @overload
        def __new__(cls, *args, null: Literal[False] = ..., **kwargs) -> FloatField[float]:
            ...

        @overload
        def __new__(cls, *args, null: Literal[True] = ..., **kwargs) -> FloatField[Optional[float]]:
            ...

        def __new__(cls, *args, **kwargs) -> Union[FloatField[float], FloatField[Optional[float]]]:
            ...


class DoubleField(pw.DoubleField, GenericField[TV]):
    if TYPE_CHECKING:

        @overload
        def __new__(cls, *args, null: Literal[False] = ..., **kwargs) -> DoubleField[float]:
            ...

        @overload
        def __new__(
            cls, *args, null: Literal[True] = ..., **kwargs
        ) -> DoubleField[Optional[float]]:
            ...

        def __new__(
            cls, *args, **kwargs
        ) -> Union[DoubleField[float], DoubleField[Optional[float]]]:
            ...


class DecimalField(pw.DecimalField, GenericField[TV]):
    if TYPE_CHECKING:

        @overload
        def __new__(cls, *args, null: Literal[False] = ..., **kwargs) -> DecimalField[float]:
            ...

        @overload
        def __new__(
            cls, *args, null: Literal[True] = ..., **kwargs
        ) -> DecimalField[Optional[float]]:
            ...

        def __new__(
            cls, *args, **kwargs
        ) -> Union[DecimalField[float], DecimalField[Optional[float]]]:
            ...


class CharField(pw.CharField, GenericField[TV]):
    if TYPE_CHECKING:

        @overload
        def __new__(cls, *args, null: Literal[False] = ..., **kwargs) -> CharField[str]:
            ...

        @overload
        def __new__(cls, *args, null: Literal[True] = ..., **kwargs) -> CharField[Optional[str]]:
            ...

        def __new__(cls, *args, **kwargs) -> Union[CharField[str], CharField[Optional[str]]]:
            ...


class FixedCharField(pw.FixedCharField, GenericField[TV]):
    if TYPE_CHECKING:

        @overload
        def __new__(cls, *args, null: Literal[False] = ..., **kwargs) -> FixedCharField[str]:
            ...

        @overload
        def __new__(
            cls, *args, null: Literal[True] = ..., **kwargs
        ) -> FixedCharField[Optional[str]]:
            ...

        def __new__(
            cls, *args, **kwargs
        ) -> Union[FixedCharField[str], FixedCharField[Optional[str]]]:
            ...


class TextField(pw.TextField, GenericField[TV]):
    if TYPE_CHECKING:

        @overload
        def __new__(cls, *args, null: Literal[False] = ..., **kwargs) -> TextField[str]:
            ...

        @overload
        def __new__(cls, *args, null: Literal[True] = ..., **kwargs) -> TextField[Optional[str]]:
            ...

        def __new__(cls, *args, **kwargs) -> Union[TextField[str], TextField[Optional[str]]]:
            ...


class BlobField(pw.BlobField, GenericField[TV]):
    if TYPE_CHECKING:

        @overload
        def __new__(cls, *args, null: Literal[False] = ..., **kwargs) -> BlobField[bytes]:
            ...

        @overload
        def __new__(cls, *args, null: Literal[True] = ..., **kwargs) -> BlobField[Optional[bytes]]:
            ...

        def __new__(cls, *args, **kwargs) -> Union[BlobField[bytes], BlobField[Optional[bytes]]]:
            ...


class BitField(pw.BitField, GenericField[TV]):
    if TYPE_CHECKING:

        @overload
        def __new__(cls, *args, null: Literal[False] = ..., **kwargs) -> BitField[int]:
            ...

        @overload
        def __new__(cls, *args, null: Literal[True] = ..., **kwargs) -> BitField[Optional[int]]:
            ...

        def __new__(cls, *args, **kwargs) -> Union[BitField[int], BitField[Optional[int]]]:
            ...


class BigBitField(pw.BigBitField, GenericField[TV]):
    if TYPE_CHECKING:

        @overload
        def __new__(cls, *args, null: Literal[False] = ..., **kwargs) -> BigBitField[bytes]:
            ...

        @overload
        def __new__(
            cls, *args, null: Literal[True] = ..., **kwargs
        ) -> BigBitField[Optional[bytes]]:
            ...

        def __new__(
            cls, *args, **kwargs
        ) -> Union[BigBitField[bytes], BigBitField[Optional[bytes]]]:
            ...


class UUIDField(pw.UUIDField, GenericField[TV]):
    if TYPE_CHECKING:

        @overload
        def __new__(cls, *args, null: Literal[False] = ..., **kwargs) -> UUIDField[UUID]:
            ...

        @overload
        def __new__(cls, *args, null: Literal[True] = ..., **kwargs) -> UUIDField[Optional[UUID]]:
            ...

        def __new__(cls, *args, **kwargs) -> Union[UUIDField[UUID], UUIDField[Optional[UUID]]]:
            ...


class BinaryUUIDField(pw.BinaryUUIDField, GenericField[TV]):
    if TYPE_CHECKING:

        @overload
        def __new__(cls, *args, null: Literal[False] = ..., **kwargs) -> BinaryUUIDField[UUID]:
            ...

        @overload
        def __new__(
            cls, *args, null: Literal[True] = ..., **kwargs
        ) -> BinaryUUIDField[Optional[UUID]]:
            ...

        def __new__(
            cls, *args, **kwargs
        ) -> Union[BinaryUUIDField[UUID], BinaryUUIDField[Optional[UUID]]]:
            ...


class DateTimeField(pw.DateTimeField, GenericField[TV]):
    if TYPE_CHECKING:

        @overload
        def __new__(cls, *args, null: Literal[False] = ..., **kwargs) -> DateTimeField[datetime]:
            ...

        @overload
        def __new__(
            cls, *args, null: Literal[True] = ..., **kwargs
        ) -> DateTimeField[Optional[datetime]]:
            ...

        def __new__(
            cls, *args, **kwargs
        ) -> Union[DateTimeField[datetime], DateTimeField[Optional[datetime]]]:
            ...


class DateField(pw.DateField, GenericField[TV]):
    if TYPE_CHECKING:

        @overload
        def __new__(cls, *args, null: Literal[False] = ..., **kwargs) -> DateField[date]:
            ...

        @overload
        def __new__(cls, *args, null: Literal[True] = ..., **kwargs) -> DateField[Optional[date]]:
            ...

        def __new__(cls, *args, **kwargs) -> Union[DateField[date], DateField[Optional[date]]]:
            ...


class TimeField(pw.TimeField, GenericField[TV]):
    if TYPE_CHECKING:

        @overload
        def __new__(cls, *args, null: Literal[False] = ..., **kwargs) -> TimeField[time]:
            ...

        @overload
        def __new__(cls, *args, null: Literal[True] = ..., **kwargs) -> TimeField[Optional[time]]:
            ...

        def __new__(cls, *args, **kwargs) -> Union[TimeField[time], TimeField[Optional[time]]]:
            ...


class TimestampField(pw.TimestampField, GenericField[TV]):
    if TYPE_CHECKING:

        @overload
        def __new__(cls, *args, null: Literal[False] = ..., **kwargs) -> TimestampField[int]:
            ...

        @overload
        def __new__(
            cls, *args, null: Literal[True] = ..., **kwargs
        ) -> TimestampField[Optional[int]]:
            ...

        def __new__(
            cls, *args, **kwargs
        ) -> Union[TimestampField[int], TimestampField[Optional[int]]]:
            ...


class IPField(pw.IPField, GenericField[TV]):
    if TYPE_CHECKING:

        @overload
        def __new__(cls, *args, null: Literal[False] = ..., **kwargs) -> IPField[str]:
            ...

        @overload
        def __new__(cls, *args, null: Literal[True] = ..., **kwargs) -> IPField[Optional[str]]:
            ...

        def __new__(cls, *args, **kwargs) -> Union[IPField[str], IPField[Optional[str]]]:
            ...


class BooleanField(pw.BooleanField, GenericField[TV]):
    if TYPE_CHECKING:

        @overload
        def __new__(cls, *args, null: Literal[False] = ..., **kwargs) -> BooleanField[bool]:
            ...

        @overload
        def __new__(
            cls, *args, null: Literal[True] = ..., **kwargs
        ) -> BooleanField[Optional[bool]]:
            ...

        def __new__(
            cls, *args, **kwargs
        ) -> Union[BooleanField[bool], BooleanField[Optional[bool]]]:
            ...


class ForeignKeyField(pw.ForeignKeyField, GenericField[TV]):
    if TYPE_CHECKING:

        @overload
        def __new__(
            cls, model: Type[TV], *, null: Literal[False] = ..., **kwargs
        ) -> ForeignKeyField[Coroutine[None, None, TV]]:
            ...

        @overload
        def __new__(
            cls, model: Type[TV], *, null: Literal[True] = ..., **kwargs
        ) -> ForeignKeyField[Coroutine[None, None, Optional[TV]]]:
            ...

        def __new__(
            cls, *args, **kwargs
        ) -> Union[
            ForeignKeyField[Coroutine[None, None, TV]],
            ForeignKeyField[Coroutine[None, None, Optional[TV]]],
        ]:
            ...

        def __set__(  # type: ignore[override]
            self, instance: AIOModel, value: Union[AIOModel, str, int, None]
        ) -> None:
            ...


class DeferredForeignKey(pw.DeferredForeignKey, GenericField[TV]):
    if TYPE_CHECKING:

        @overload
        def __new__(
            cls, rel_model_name: str, *, null: Literal[False] = ..., **kwargs
        ) -> DeferredForeignKey[Coroutine[None, None, AIOModel]]:
            ...

        @overload
        def __new__(
            cls, rel_model_name: str, *, null: Literal[True] = ..., **kwargs
        ) -> DeferredForeignKey[Coroutine[None, None, Optional[AIOModel]]]:
            ...

        def __new__(
            cls, *args, **kwargs
        ) -> Union[
            DeferredForeignKey[Coroutine[None, None, AIOModel]],
            DeferredForeignKey[Coroutine[None, None, Optional[AIOModel]]],
        ]:
            ...

        def __set__(  # type: ignore[override]
            self, instance: AIOModel, value: Union[AIOModel, str, int, None]
        ) -> None:
            ...


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
