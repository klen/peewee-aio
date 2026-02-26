"""Generic fields for peewee."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Coroutine, Generic, Literal, overload  # py39

import peewee as pw

if TYPE_CHECKING:
    from datetime import date, datetime, time
    from uuid import UUID

    from typing_extensions import Self  # py310

    from .model import AIOModel

from .types import TV, TVAIOModel


class TPWNode:  # noqa: PLW1641
    if TYPE_CHECKING:
        # Operations that return expressions
        # ----------------------------------
        def __and__(self, rhs) -> pw.Expression: ...

        def __or__(self, rhs) -> pw.Expression: ...

        def __add__(self, rhs) -> pw.Expression: ...

        def __sub__(self, rhs) -> pw.Expression: ...

        def __mul__(self, rhs) -> pw.Expression: ...

        def __div__(self, rhs) -> pw.Expression: ...

        def __xor__(self, rhs) -> pw.Expression: ...

        def __radd__(self, lhs) -> pw.Expression: ...

        def __rsub__(self, lhs) -> pw.Expression: ...

        def __rmul__(self, lhs) -> pw.Expression: ...

        def __rdiv__(self, lhs) -> pw.Expression: ...

        def __rand__(self, lhs) -> pw.Expression: ...

        def __ror__(self, lhs) -> pw.Expression: ...

        def __rxor__(self, lhs) -> pw.Expression: ...

        def __eq__(self, rhs) -> pw.Expression: ...  # type: ignore[override]

        def __ne__(self, rhs) -> pw.Expression: ...  # type: ignore[override]

        def __lt__(self, rhs) -> pw.Expression: ...

        def __le__(self, rhs) -> pw.Expression: ...

        def __gt__(self, rhs) -> pw.Expression: ...

        def __ge__(self, rhs) -> pw.Expression: ...

        def __lshift__(self, rhs: Any) -> pw.Expression: ...

        def __rshift__(self, rhs) -> pw.Expression: ...

        def __mod__(self, rhs) -> pw.Expression: ...

        def __pow__(self, rhs) -> pw.Expression: ...

        def like(self, rhs) -> pw.Expression: ...

        def ilike(self, rhs) -> pw.Expression: ...

        def in_(self, rhs) -> pw.Expression: ...

        def not_in(self, rhs) -> pw.Expression: ...

        def regexp(self, rhs) -> pw.Expression: ...

        def iregexp(self, rhs) -> pw.Expression: ...


class GenericField(TPWNode, Generic[TV]):
    if TYPE_CHECKING:
        # Descriptor methods
        # ------------------
        @overload
        def __get__(self, instance: None, owner) -> Self: ...

        @overload
        def __get__(self: GenericField[TV], instance: pw.Model, owner) -> TV: ...

        def __get__(self, instance: pw.Model | None, owner) -> Self | TV: ...

        def __set__(self, instance: pw.Model, value: Any) -> None: ...


class JSONGenericField(GenericField[TV]):
    if TYPE_CHECKING:

        @overload
        def __new__(cls, *args, null: Literal[True], **kwargs) -> JSONGenericField[TV | None]: ...

        @overload
        def __new__(cls, *args, null: Literal[False] = False, **kwargs) -> JSONGenericField[TV]: ...

        def __new__(cls, *args, **kwargs) -> Any: ...

        def __getitem__(self, key: Any) -> pw.Expression: ...


class IntegerField(GenericField[TV], pw.IntegerField):
    if TYPE_CHECKING:

        @overload
        def __new__(cls, *args, null: Literal[True], **kwargs) -> IntegerField[int | None]: ...

        @overload
        def __new__(cls, *args, null: Literal[False] = False, **kwargs) -> IntegerField[int]: ...

        def __new__(cls, *args, **kwargs) -> Any: ...


class BigIntegerField(GenericField[TV], pw.BigIntegerField):
    if TYPE_CHECKING:

        @overload
        def __new__(cls, *args, null: Literal[True], **kwargs) -> BigIntegerField[int | None]: ...

        @overload
        def __new__(cls, *args, null: Literal[False] = False, **kwargs) -> BigIntegerField[int]: ...

        def __new__(cls, *args, **kwargs) -> Any: ...


class SmallIntegerField(GenericField[TV], pw.SmallIntegerField):
    if TYPE_CHECKING:

        @overload
        def __new__(cls, *args, null: Literal[True], **kwargs) -> SmallIntegerField[int | None]: ...

        @overload
        def __new__(
            cls, *args, null: Literal[False] = False, **kwargs
        ) -> SmallIntegerField[int]: ...

        def __new__(cls, *args, **kwargs) -> Any: ...


class AutoField(GenericField[TV], pw.AutoField):
    if TYPE_CHECKING:

        def __new__(cls, *args, **kwargs) -> AutoField[int]: ...


class BigAutoField(GenericField[TV], pw.BigAutoField):
    if TYPE_CHECKING:

        def __new__(cls, *args, **kwargs) -> BigAutoField[int]: ...


class IdentityField(GenericField[TV], pw.IdentityField):
    if TYPE_CHECKING:

        def __new__(cls, *args, **kwargs) -> IdentityField[int]: ...


class FloatField(GenericField[TV], pw.FloatField):
    if TYPE_CHECKING:

        @overload
        def __new__(cls, *args, null: Literal[True], **kwargs) -> FloatField[float | None]: ...

        @overload
        def __new__(cls, *args, null: Literal[False] = False, **kwargs) -> FloatField[float]: ...

        def __new__(cls, *args, **kwargs) -> Any: ...


class DoubleField(GenericField[TV], pw.DoubleField):
    if TYPE_CHECKING:

        @overload
        def __new__(cls, *args, null: Literal[True], **kwargs) -> DoubleField[float | None]: ...

        @overload
        def __new__(cls, *args, null: Literal[False] = False, **kwargs) -> DoubleField[float]: ...

        def __new__(cls, *args, **kwargs) -> Any: ...


class DecimalField(GenericField[TV], pw.DecimalField):
    if TYPE_CHECKING:

        @overload
        def __new__(cls, *args, null: Literal[True], **kwargs) -> DecimalField[float | None]: ...

        @overload
        def __new__(cls, *args, null: Literal[False] = False, **kwargs) -> DecimalField[float]: ...

        def __new__(cls, *args, **kwargs) -> Any: ...


class CharField(GenericField[TV], pw.CharField):
    if TYPE_CHECKING:

        @overload
        def __new__(cls, *args, null: Literal[True], **kwargs) -> CharField[str | None]: ...

        @overload
        def __new__(cls, *args, null: Literal[False] = False, **kwargs) -> CharField[str]: ...

        def __new__(cls, *args, **kwargs) -> Any: ...


class FixedCharField(pw.FixedCharField, GenericField[TV]):
    if TYPE_CHECKING:

        @overload
        def __new__(cls, *args, null: Literal[True], **kwargs) -> FixedCharField[str | None]: ...

        @overload
        def __new__(cls, *args, null: Literal[False] = False, **kwargs) -> FixedCharField[str]: ...

        def __new__(cls, *args, **kwargs) -> Any: ...


class TextField(GenericField[TV], pw.TextField):
    if TYPE_CHECKING:

        @overload
        def __new__(cls, *args, null: Literal[True], **kwargs) -> TextField[str | None]: ...

        @overload
        def __new__(cls, *args, null: Literal[False] = False, **kwargs) -> TextField[str]: ...

        def __new__(cls, *args, **kwargs) -> Any: ...


class BlobField(GenericField[TV], pw.BlobField):
    if TYPE_CHECKING:

        @overload
        def __new__(cls, *args, null: Literal[True], **kwargs) -> BlobField[bytes | None]: ...

        @overload
        def __new__(cls, *args, null: Literal[False] = False, **kwargs) -> BlobField[bytes]: ...

        def __new__(cls, *args, **kwargs) -> Any: ...


class BitField(GenericField[TV], pw.BitField):
    if TYPE_CHECKING:

        @overload
        def __new__(cls, *args, null: Literal[True], **kwargs) -> BitField[int | None]: ...

        @overload
        def __new__(cls, *args, null: Literal[False] = False, **kwargs) -> BitField[int]: ...

        def __new__(cls, *args, **kwargs) -> Any: ...


class BigBitField(GenericField[TV], pw.BigBitField):
    if TYPE_CHECKING:

        @overload
        def __new__(cls, *args, null: Literal[True], **kwargs) -> BigBitField[bytes | None]: ...

        @overload
        def __new__(cls, *args, null: Literal[False] = False, **kwargs) -> BigBitField[bytes]: ...

        def __new__(cls, *args, **kwargs) -> Any: ...


class UUIDField(GenericField[TV], pw.UUIDField):
    if TYPE_CHECKING:

        @overload
        def __new__(cls, *args, null: Literal[True], **kwargs) -> UUIDField[UUID | None]: ...

        @overload
        def __new__(cls, *args, null: Literal[False] = False, **kwargs) -> UUIDField[UUID]: ...

        def __new__(cls, *args, **kwargs) -> Any: ...


class BinaryUUIDField(GenericField[TV], pw.BinaryUUIDField):
    if TYPE_CHECKING:

        @overload
        def __new__(cls, *args, null: Literal[True], **kwargs) -> BinaryUUIDField[UUID | None]: ...

        @overload
        def __new__(
            cls, *args, null: Literal[False] = False, **kwargs
        ) -> BinaryUUIDField[UUID]: ...

        def __new__(cls, *args, **kwargs) -> Any: ...


class DateTimeField(GenericField[TV], pw.DateTimeField):
    if TYPE_CHECKING:

        @overload
        def __new__(
            cls, *args, null: Literal[True], **kwargs
        ) -> DateTimeField[datetime | None]: ...

        @overload
        def __new__(
            cls, *args, null: Literal[False] = False, **kwargs
        ) -> DateTimeField[datetime]: ...

        def __new__(cls, *args, **kwargs) -> Any: ...


class DateField(GenericField[TV], pw.DateField):
    if TYPE_CHECKING:

        @overload
        def __new__(cls, *args, null: Literal[True], **kwargs) -> DateField[date | None]: ...

        @overload
        def __new__(cls, *args, null: Literal[False] = False, **kwargs) -> DateField[date]: ...

        def __new__(cls, *args, **kwargs) -> Any: ...


class TimeField(GenericField[TV], pw.TimeField):
    if TYPE_CHECKING:

        @overload
        def __new__(cls, *args, null: Literal[True], **kwargs) -> TimeField[time | None]: ...

        @overload
        def __new__(cls, *args, null: Literal[False] = False, **kwargs) -> TimeField[time]: ...

        def __new__(cls, *args, **kwargs) -> Any: ...


class TimestampField(GenericField[TV], pw.TimestampField):
    if TYPE_CHECKING:

        @overload
        def __new__(cls, *args, null: Literal[True], **kwargs) -> TimestampField[int | None]: ...

        @overload
        def __new__(cls, *args, null: Literal[False] = False, **kwargs) -> TimestampField[int]: ...

        def __new__(cls, *args, **kwargs) -> Any: ...


class IPField(GenericField[TV], pw.IPField):
    if TYPE_CHECKING:

        @overload
        def __new__(cls, *args, null: Literal[True], **kwargs) -> IPField[str | None]: ...

        @overload
        def __new__(cls, *args, null: Literal[False] = False, **kwargs) -> IPField[str]: ...

        def __new__(cls, *args, **kwargs) -> Any: ...


class BooleanField(GenericField[TV], pw.BooleanField):
    if TYPE_CHECKING:

        @overload
        def __new__(cls, *args, null: Literal[True], **kwargs) -> BooleanField[bool | None]: ...

        @overload
        def __new__(cls, *args, null: Literal[False] = False, **kwargs) -> BooleanField[bool]: ...

        def __new__(cls, *args, **kwargs) -> Any: ...


class AIOForeignKeyAccessor(pw.ForeignKeyAccessor):
    async def get_rel_instance(self, instance: AIOModel) -> AIOModel | None:
        name = self.name
        relations = instance.__rel__
        if name in relations:
            return relations[name]

        value = instance.__data__.get(name)
        if value is None:
            if not self.field.null:
                raise self.rel_model.DoesNotExist
            return None

        field = self.field
        if field.lazy_load:
            rel_instance = await self.rel_model.get(field.rel_field == value)
            relations[name] = rel_instance
            return rel_instance

        return value


class AIOForeignKeyField(GenericField[TV], pw.ForeignKeyField):
    accessor_class = AIOForeignKeyAccessor

    if TYPE_CHECKING:

        @overload
        def __new__(
            cls, model: type[TVAIOModel] | Literal["self"], *, null: Literal[True], **kwargs
        ) -> AIOForeignKeyField[Coroutine[None, None, TVAIOModel | None]]: ...

        @overload
        def __new__(
            cls,
            model: type[TVAIOModel] | Literal["self"],
            *,
            null: Literal[False] = False,
            **kwargs,
        ) -> AIOForeignKeyField[Coroutine[None, None, TVAIOModel]]: ...

        def __new__(cls, *args, **kwargs) -> AIOForeignKeyField[Coroutine[None, None, Any]]: ...


class FetchForeignKeyAccessor(pw.ForeignKeyAccessor):
    def get_rel_instance(self, instance: AIOModel) -> AIOModel | None:
        name = self.name
        relations = instance.__rel__
        if name in relations:
            return relations[name]

        value = instance.__data__.get(name)
        if value is None:
            if not self.field.null:
                raise self.rel_model.DoesNotExist
            return None

        raise RuntimeError(f"{name} has to be prefetched")


class FetchForeignKeyField(GenericField[TV], pw.ForeignKeyField):
    """A foreign key field that only works with prefetching"""

    accessor_class = FetchForeignKeyAccessor

    def __init__(
        self: FetchForeignKeyField[TVAIOModel],
        model: type[TVAIOModel],
        *,
        lazy_load: bool = True,
        **kwargs,
    ):
        """Field has to be always prefetched."""
        super().__init__(model, lazy_load=False, **kwargs)

    if TYPE_CHECKING:

        @overload
        def __new__(
            cls, model: type[TVAIOModel], *, null: Literal[True], **kwargs
        ) -> FetchForeignKeyField[TVAIOModel | None]: ...

        @overload
        def __new__(
            cls, model: type[TVAIOModel], *, null: Literal[False] = False, **kwargs
        ) -> FetchForeignKeyField[TVAIOModel]: ...

        def __new__(cls, *args, **kwargs) -> FetchForeignKeyField[Any]: ...


class AIODeferredForeignKey(pw.DeferredForeignKey, GenericField[TV]):
    def set_model(self, rel_model: type[AIOModel]):
        field = AIOForeignKeyField(rel_model, _deferred=True, **self.field_kwargs)
        self.model._meta.add_field(self.name, field)

    if TYPE_CHECKING:

        @overload
        def __new__(
            cls, rel_model_name: str, *, null: Literal[True], **kwargs
        ) -> AIODeferredForeignKey[Coroutine[None, None, AIOModel | None]]: ...

        @overload
        def __new__(
            cls, rel_model_name: str, *, null: Literal[False] = False, **kwargs
        ) -> AIODeferredForeignKey[Coroutine[None, None, AIOModel]]: ...

        def __new__(cls, *args, **kwargs) -> AIODeferredForeignKey[Coroutine[None, None, Any]]: ...


# Aliases
ForeignKeyField = AIOForeignKeyField
DeferredForeignKey = AIODeferredForeignKey
FetchForeignKey = FetchForeignKeyField  # depricate me


__all__ = [
    "AIODeferredForeignKey",
    "AIOForeignKeyField",
    "AutoField",
    "BigAutoField",
    "BigBitField",
    "BigIntegerField",
    "BinaryUUIDField",
    "BitField",
    "BlobField",
    "BooleanField",
    "CharField",
    "DateField",
    "DateTimeField",
    "DecimalField",
    "DeferredForeignKey",
    "DoubleField",
    "FetchForeignKeyField",
    "FixedCharField",
    "FloatField",
    "ForeignKeyField",
    "GenericField",
    "IPField",
    "IdentityField",
    "IntegerField",
    "SmallIntegerField",
    "TextField",
    "TimeField",
    "TimestampField",
    "UUIDField",
]
