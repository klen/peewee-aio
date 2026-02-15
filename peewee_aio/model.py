"""TODO: To implement."""

from __future__ import annotations

from typing import (  # py39
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    Callable,
    Coroutine,
    Generator,
    Generic,
    Iterable,
    Literal,
    cast,
    overload,
)

from peewee import (
    SQL,
    Case,
    ColumnBase,
    CompositeKey,
    DeferredForeignKey,
    Expression,
    Field,
    ForeignKeyField,
    Metadata,
    Model,
    ModelAlias,
    ModelBase,
    ModelCompoundSelectQuery,
    ModelDelete,
    ModelInsert,
    ModelRaw,
    ModelSelect,
    ModelUpdate,
    Node,
    Query,
    Table,
    chunked,
)

from .fields import AIODeferredForeignKey, AIOForeignKeyField, FetchForeignKey
from .types import TV, TVAIOModel

if TYPE_CHECKING:
    from typing_extensions import Self  # py310,py39,py38,py37

    from .manager import Manager


class AIOModelBase(ModelBase):
    inheritable = ModelBase.inheritable & {"manager"}

    def __new__(cls, name, bases, attrs):
        # Replace fields to AIO fields
        for attr_name, attr in attrs.items():
            if not isinstance(attr, Field) or isinstance(
                attr, (AIOForeignKeyField, AIODeferredForeignKey, FetchForeignKey)
            ):
                continue

            if isinstance(attr, ForeignKeyField):
                attrs[attr_name] = AIOForeignKeyField(
                    attr.rel_model,
                    field=attr.rel_field,
                    backref=attr.declared_backref,
                    on_delete=attr.on_delete,
                    on_update=attr.on_update,
                    deferrable=attr.deferrable,
                    _deferred=attr.deferred,
                    object_id_name=attr.object_id_name,
                    lazy_load=attr.lazy_load,
                    constraint_name=attr.constraint_name,
                    null=attr.null,
                    index=attr.index,
                    unique=attr.unique,
                    default=attr.default,
                    primary_key=attr.primary_key,
                    constraints=attr.constraints,
                    sequence=attr.sequence,
                    collation=attr.collation,
                    unindexed=attr.unindexed,
                    choices=attr.choices,
                    help_text=attr.help_text,
                    verbose_name=attr.verbose_name,
                    index_type=attr.index_type,
                    _hidden=attr._hidden,
                )

            elif isinstance(attr, DeferredForeignKey):
                attrs[attr_name] = AIODeferredForeignKey(
                    attr.rel_model_name,
                    **attr.field_kwargs,
                )
                DeferredForeignKey._unresolved.discard(attr)  # type: ignore[]

        kls = super(AIOModelBase, cls).__new__(cls, name, bases, attrs)
        meta = kls._meta
        if getattr(kls, "_manager", None) and not meta.database:
            meta.database = kls._manager.pw_database

        return kls


class AIOModelAlias(ModelAlias, Generic[TVAIOModel]):
    def select(self, *selection) -> AIOModelSelect[TVAIOModel]:
        return AIOModelSelect(self, selection)


class AIOModel(Model, metaclass=AIOModelBase):
    if TYPE_CHECKING:
        _manager: Manager
        _meta: Metadata

        DoesNotExist: type[Exception]

        # Support for dynamic attributes like `model.name_id`, `model.name_set`, etc
        def __getattr__(self, name: str) -> Any: ...

        def __setattr__(self, name: str, value: Any) -> None: ...

    # Class methods
    # -------------

    @classmethod
    async def create_table(cls, *, safe=True, **kwargs):  # type: ignore[bad-override]
        await cls._manager.create_tables(cls, safe=safe, **kwargs)

    @classmethod
    async def drop_table(cls, *, safe=True, **kwargs):  # type: ignore[bad-override]
        return await cls._manager.drop_tables(cls, safe=safe, **kwargs)

    @classmethod
    async def get_or_none(cls: type[TVAIOModel], *args: Node, **kwargs) -> TVAIOModel | None:
        return await cls._manager.get_or_none(cls, *args, **kwargs)

    @classmethod
    async def get(cls: type[TVAIOModel], *args: Node, **kwargs) -> TVAIOModel:
        return await cls._manager.get(cls, *args, **kwargs)

    @classmethod
    async def get_by_id(cls: type[TVAIOModel], pk) -> TVAIOModel:
        return await cls._manager.get_by_id(cls, pk)

    @classmethod
    async def set_by_id(cls, key, value):
        return await cls._manager.set_by_id(cls, key, value)

    @classmethod
    async def delete_by_id(cls, pk):
        return await cls._manager.delete_by_id(cls, pk)

    @classmethod
    async def get_or_create(
        cls: type[TVAIOModel], defaults: dict[str, Any] | None = None, **kwargs
    ) -> tuple[TVAIOModel, bool]:
        async with cls._manager.transaction():
            try:
                return (await cls.get(**kwargs), False)
            except cls.DoesNotExist:
                return (await cls.create(**dict(defaults or {}, **kwargs)), True)

    @classmethod
    async def create(cls: type[TVAIOModel], **kwargs) -> TVAIOModel:
        inst = cls(**kwargs)
        return await inst.save(force_insert=True)

    @classmethod
    async def bulk_create(  # type: ignore[bad-override]
        cls: type[TVAIOModel], model_list: Iterable[TVAIOModel], batch_size: int | None = None
    ):
        meta = cls._meta

        field_names = list(meta.sorted_field_names)
        if meta.auto_increment:
            pk_name = meta.primary_key.name
            field_names.remove(pk_name)

        fields = [cls._meta.fields[field_name] for field_name in field_names]
        attrs = [
            field.object_id_name if isinstance(field, ForeignKeyField) else field.name
            for field in fields
        ]

        if meta.database.returning_clause and meta.primary_key is not False:
            pk_fields = meta.get_primary_keys()
        else:
            pk_fields = None

        batches = chunked(model_list, batch_size) if batch_size is not None else [model_list]
        for batch in batches:
            accum = ([getattr(model, f) for f in attrs] for model in batch)

            res = await cls.insert_many(accum, fields=fields)
            if pk_fields and res is not None:
                for row, model in zip(res, batch, strict=False):
                    for pk_field, obj_id in zip(pk_fields, row, strict=False):
                        setattr(model, pk_field.name, obj_id)

    @classmethod
    async def bulk_update(
        cls: type[TVAIOModel],
        model_list: Iterable[TVAIOModel],
        fields: Iterable[str | Field],
        batch_size: int | None = None,
    ) -> int:
        meta = cls._meta
        if isinstance(meta.primary_key, CompositeKey):
            raise TypeError(
                "bulk_update() is not supported for models with a composite primary key."
            )

        # First normalize list of fields so all are field instances.
        model_fields = [cast("Field", meta.fields[f]) if isinstance(f, str) else f for f in fields]

        # Now collect list of attribute names to use for values.
        attrs = [
            field.object_id_name if isinstance(field, ForeignKeyField) else field.name
            for field in model_fields
        ]

        n = 0
        pk = meta.primary_key
        batches = chunked(model_list, batch_size) if batch_size is not None else [model_list]
        for batch in batches:
            id_list = [model._pk for model in batch]
            update = {}
            for field, attr in zip(model_fields, attrs, strict=False):
                accum = []
                for model in batch:
                    value = getattr(model, attr)
                    if not isinstance(value, Node):
                        value = field.to_value(value)
                    accum.append((pk.to_value(model._pk), value))
                update[field] = Case(pk, accum)

            n += cast("int", await cls.update(update).where(cls._meta.primary_key.in_(id_list)))

        return n

    # Queryset methods
    # ----------------

    @classmethod
    def alias(cls: type[TVAIOModel], alias: str | None = None) -> AIOModelAlias[TVAIOModel]:
        return AIOModelAlias(cls, alias)

    @classmethod
    def select(
        cls: type[TVAIOModel], *select: type[Model] | ColumnBase | Table | ModelAlias
    ) -> AIOModelSelect[TVAIOModel]:
        return AIOModelSelect(
            cls,
            select or cls._meta.sorted_fields,
            is_default=not select,
        )

    @classmethod
    def update(cls: type[TVAIOModel], __data=None, **update) -> AIOModelUpdate[TVAIOModel]:  # noqa: PYI063
        return AIOModelUpdate(cls, cls._normalize_data(__data, update))  # type: ignore[]

    @classmethod
    def insert(cls: type[TVAIOModel], __data=None, **insert) -> AIOModelInsert[TVAIOModel]:  # noqa: PYI063
        return AIOModelInsert(cls, cls._normalize_data(__data, insert))  # type: ignore[]

    @classmethod
    def insert_many(
        cls: type[TVAIOModel], rows: Iterable, fields=None
    ) -> AIOModelInsert[TVAIOModel]:
        if not rows:
            raise AIOModelInsert.DefaultValuesException("Error: no rows to insert.")

        rows = [row.__data__ if isinstance(row, Model) else row for row in rows]
        return AIOModelInsert(cls, insert=rows, columns=fields)

    @classmethod
    def insert_from(
        cls: type[TVAIOModel], query: ModelSelect, fields
    ) -> AIOModelInsert[TVAIOModel]:
        columns = [getattr(cls, field) if isinstance(field, str) else field for field in fields]
        return AIOModelInsert(cls, insert=query, columns=columns)

    @classmethod
    def raw(cls: type[TVAIOModel], sql, *params) -> AIOModelRaw[TVAIOModel]:
        return AIOModelRaw(cls, sql, params)

    @classmethod
    def delete(cls: type[TVAIOModel]) -> AIOModelDelete[TVAIOModel]:
        return AIOModelDelete(cls)

    # Instance methods
    # ----------------

    async def save(self, **kwargs) -> Self:  # type: ignore[bad-override]
        return await self._manager.save(self, **kwargs)

    async def delete_instance(self, **kwargs):  # type: ignore[bad-override]
        return await self._manager.delete_instance(self, **kwargs)

    @overload
    def fetch(self, fk: AIOForeignKeyField[Coroutine[None, None, TV]]) -> TV: ...

    @overload
    def fetch(self, fk: AIODeferredForeignKey[Coroutine[None, None, TV]]) -> TV: ...

    def fetch(self, fk):
        """Get fk relation from the given instance cache. Raise ValueError if not loaded."""

        attr = fk.name
        relations = self.__rel__
        if attr in relations:
            return relations[attr]

        value = self.__data__.get(attr)
        if value is None:
            return None

        raise ValueError(f"Relation {attr} is not loaded into {self!r}") from None

    # Support await syntax
    # --------------------

    def __await__(self):
        return self.__anext__().__await__()

    async def __anext__(self):
        return self


class AIOQuery(Query, Generic[TVAIOModel]):
    model: type[TVAIOModel]

    if TYPE_CHECKING:
        _order_by: tuple | None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.manager = self.model._manager

    def __await__(self) -> Generator[Any, None, Any]:
        return self.manager.run(self).__await__()


class BaseModelSelect(AIOQuery[TVAIOModel]):
    def union_all(self, rhs):
        return AIOModelCompoundSelectQuery(self.model, self, "UNION ALL", rhs)

    __add__ = union_all

    def union(self, rhs):
        return AIOModelCompoundSelectQuery(self.model, self, "UNION", rhs)

    __or__ = union

    def intersect(self, rhs):
        return AIOModelCompoundSelectQuery(self.model, self, "INTERSECT", rhs)

    __and__ = intersect

    def except_(self, rhs):
        return AIOModelCompoundSelectQuery(self.model, self, "EXCEPT", rhs)

    __sub__ = except_

    async def prefetch(self, *subqueries) -> list[TVAIOModel]:
        return await self.manager.prefetch(self, *subqueries)


class TQuery:
    if TYPE_CHECKING:
        _limit: int | None
        _offset: int | None
        _where: Expression | None
        _order_by: tuple | None
        _cte_list = tuple | None

        def select(self, *select: type[Model] | Node) -> Self: ...  # type: ignore[bad-override]
        def with_cte(self, *cte) -> Self: ...  # type: ignore[bad-override]
        def where(self, *expressions) -> Self: ...  # type: ignore[bad-override]
        def orwhere(self, *expressions) -> Self: ...  # type: ignore[bad-override]
        def order_by(self, *ordering) -> Self: ...  # type: ignore[bad-override]
        def order_by_extend(self, *ordering) -> Self: ...  # type: ignore[bad-override]
        def limit(self, value: int | None) -> Self: ...  # type: ignore[bad-override]
        def offset(self, value: int | None) -> Self: ...  # type: ignore[bad-override]
        def paginate(self, page: int, paginate_by: int = 20) -> Self: ...  # type: ignore[bad-override]


class AIOModelSelect(BaseModelSelect[TVAIOModel], TQuery, ModelSelect):
    def __aiter__(self) -> AsyncIterator[TVAIOModel]:
        return self.manager.run(self).__aiter__()  # type: ignore[return-value]

    @overload
    def __getitem__(self, value: int) -> Coroutine[None, None, TVAIOModel]: ...

    @overload
    def __getitem__(self, value: slice) -> Coroutine[None, None, list[TVAIOModel]]: ...

    def __getitem__(self, value) -> Any:
        limit, offset = 1, value
        if isinstance(value, slice):
            limit, offset = value.stop - value.start, value.start

        query = self.limit(limit).offset(offset)
        if limit == 1:
            return query.get()
        return query

    @overload
    async def peek(self, n: Literal[1] = 1) -> TVAIOModel | None: ...  # type: ignore[bad-override]

    @overload
    async def peek(self, n: int) -> list[TVAIOModel]: ...

    async def peek(self, n: int = 1) -> Any:
        if n == 1:
            return await self.manager.fetchone(self)
        return await self.manager.fetchmany(n, self)

    @overload
    async def first(self, n: Literal[1] = 1) -> TVAIOModel | None: ...  # type: ignore[bad-override]

    @overload
    async def first(self, n: int) -> list[TVAIOModel]: ...

    def first(self, n: int = 1):
        return self.peek(n)

    async def scalar(self, *, as_dict=False, as_tuple=False) -> Any:  # type: ignore[bad-override]
        if as_dict:
            return await self.dicts().peek()

        row = await self.tuples().peek()
        if as_tuple:
            return row

        return row[0] if row else None

    async def scalars(self) -> list[Any]:  # type: ignore[bad-override]
        return [row[0] for row in await self.tuples()]

    async def count(self) -> int:  # type: ignore[bad-override]
        return await self.manager.count(self)

    async def exists(self) -> bool:  # type: ignore[bad-override]
        clone: AIOModelSelect = self.columns(SQL("1"))
        clone._limit = 1
        clone._offset = None
        return bool(await clone.scalar())

    async def get(self, *expressions, **filters) -> TVAIOModel:
        qs = self

        if expressions:
            qs = qs.where(*expressions)

        if filters:
            qs = qs.filter(**filters)

        res = await qs.peek()
        if res is None:
            sql, params = qs.sql()
            raise self.model.DoesNotExist(
                "%s matching query does not exist:\n SQL: %s\n Params: %s"
                % (self.model, sql, params)
            )
        return res

    if TYPE_CHECKING:
        _returning: tuple[ColumnBase, ...] | None

        def dicts(self) -> AIOModelSelect[dict[str, Any]]: ...  # type: ignore[bad-override]
        def tuples(self) -> AIOModelSelect[tuple]: ...  # type: ignore[bad-override]
        def namedtuples(self, *field_names) -> AIOModelSelect[tuple]: ...  # type: ignore[bad-override]
        def objects(self) -> AIOModelSelect[TVAIOModel]: ...  # type: ignore[bad-override]

        columns: Callable[..., Self]
        distinct: Callable[..., Self]
        filter: Callable[..., Self]
        for_update: Callable[..., Self]
        from_: Callable[..., Self]
        group_by: Callable[..., Self]
        having: Callable[..., Self]
        join: Callable[..., Self]
        join_from: Callable[..., Self]
        lateral: Callable[..., Self]
        objects: Callable[..., Self]
        select_extend: Callable[..., Self]
        switch: Callable[..., Self]
        window: Callable[..., Self]

        def __await__(self) -> Generator[Any, None, list[TVAIOModel]]:
            return self.manager.run(self).__await__()


class AIOModelCompoundSelectQuery(BaseModelSelect[TVAIOModel], TQuery, ModelCompoundSelectQuery):
    if TYPE_CHECKING:
        filter: Callable[..., Self]

        def dicts(self) -> AIOModelSelect[dict[str, Any]]: ...  # type: ignore[bad-override]
        def tuples(self) -> AIOModelSelect[tuple]: ...  # type: ignore[bad-override]
        def namedtuples(self, *field_names) -> AIOModelSelect[tuple]: ...  # type: ignore[bad-override]
        def objects(self) -> AIOModelSelect[TVAIOModel]: ...  # type: ignore[bad-override]

        columns: Callable[..., Self]
        select_extend: Callable[..., Self]
        from_: Callable[..., Self]
        join: Callable[..., Self]
        join_from: Callable[..., Self]
        group_by: Callable[..., Self]
        having: Callable[..., Self]
        distinct: Callable[..., Self]
        window: Callable[..., Self]
        for_update: Callable[..., Self]
        lateral: Callable[..., Self]


class AIOModelUpdate(AIOQuery[TVAIOModel], TQuery, ModelUpdate):
    if TYPE_CHECKING:
        from_: Callable[..., AIOModelUpdate[TVAIOModel]]
        returning: Callable[..., AIOModelUpdate[TVAIOModel]]


class AIOModelInsert(AIOQuery[TVAIOModel], TQuery, ModelInsert):
    if TYPE_CHECKING:
        returning: Callable[..., AIOModelInsert[TVAIOModel]]
        on_conflict: Callable[..., AIOModelInsert[TVAIOModel]]
        on_conflict_ignore: Callable[..., AIOModelInsert[TVAIOModel]]
        on_conflict_replace: Callable[..., AIOModelInsert[TVAIOModel]]


class AIOModelDelete(AIOQuery[TVAIOModel], TQuery, ModelDelete):
    pass


class AIOModelRaw(AIOQuery[TVAIOModel], ModelRaw):
    pass
