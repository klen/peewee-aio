"""TODO: To implement."""

from __future__ import annotations

from typing import (Any, AsyncGenerator, Callable, Coroutine, Dict, Generator, Generic, Iterable,
                    List, Optional, Tuple, Union)

from peewee import (SQL, DeferredForeignKey, Field, ForeignKeyAccessor, ForeignKeyField, Model,
                    ModelBase)
from peewee import ModelCompoundSelectQuery as ModelCompoundSelectQuery_
from peewee import ModelDelete as ModelDelete_
from peewee import ModelInsert as ModelInsert_
from peewee import ModelRaw as ModelRaw_
from peewee import ModelSelect as ModelSelect_
from peewee import ModelUpdate as ModelUpdate_
from typing_extensions import Self  # py310,py39,py38,py37

from .types import TVAIOModel


class AIOForeignKeyAccessor(ForeignKeyAccessor):
    def get_rel_instance(
        self, instance: Model
    ) -> Union[Model, None, Coroutine[Any, Any, Model]]:

        # Get from cache
        name = self.name
        if name in instance.__rel__:
            return instance.__rel__[name]

        value = instance.__data__.get(name)

        # Lazy load
        field = self.field
        if field.lazy_load:
            if value is not None:
                return self.load_rel(instance, value)

            if not field.null:
                raise self.rel_model.DoesNotExist

        return value

    async def load_rel(self, instance: Model, value: Any) -> Model:
        obj = await self.rel_model.get(self.field.rel_field == value)
        instance.__rel__[self.name] = obj
        return obj


class AIOForeignKeyField(ForeignKeyField):

    accessor_class = AIOForeignKeyAccessor


class AIODeferredForeignKey(DeferredForeignKey):
    def set_model(self, rel_model):
        field = AIOForeignKeyField(rel_model, _deferred=True, **self.field_kwargs)
        self.model._meta.add_field(self.name, field)


class AIOModelBase(ModelBase):

    inheritable = ModelBase.inheritable & {"manager"}

    def __new__(cls, name, bases, attrs):
        # Replace fields to AIO fields
        for attr_name, attr in attrs.items():
            if not isinstance(attr, Field):
                continue

            if isinstance(attr, ForeignKeyField) and not isinstance(
                attr, AIOForeignKeyField
            ):
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

            elif isinstance(attr, DeferredForeignKey) and not isinstance(
                attr, AIODeferredForeignKey
            ):
                attrs[attr_name] = AIODeferredForeignKey(
                    attr.rel_model_name,
                    **attr.field_kwargs,
                )
                DeferredForeignKey._unresolved.discard(attr)

        cls = super(AIOModelBase, cls).__new__(cls, name, bases, attrs)
        meta = cls._meta
        if getattr(cls, "_manager", None) and not meta.database:
            meta.database = cls._manager.pw_database

        return cls


class AIOModel(Model, metaclass=AIOModelBase):

    _manager: Manager

    # Class methods
    # -------------

    @classmethod
    async def create_table(cls, safe=True, **kwargs):
        return await cls._manager.create_tables(cls, safe=safe, **kwargs)

    @classmethod
    async def drop_table(cls, safe=True, **kwargs):
        return await cls._manager.drop_tables(cls, safe=safe, **kwargs)

    @classmethod
    async def get_or_none(
        cls: type[TVAIOModel], *args, **kwargs
    ) -> Optional[TVAIOModel]:
        return await cls._manager.get_or_none(cls, *args, **kwargs)

    @classmethod
    async def get(cls: type[TVAIOModel], *args, **kwargs) -> TVAIOModel:
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
        cls: type[TVAIOModel], defaults: Optional[Dict] = None, **kwargs
    ) -> Tuple[TVAIOModel, bool]:
        async with cls._manager.aio_database.transaction():
            try:
                return (await cls.get(**kwargs), False)
            except cls.DoesNotExist:
                return (await cls.create(**dict(defaults or {}, **kwargs)), True)

    @classmethod
    async def create(cls: type[TVAIOModel], **kwargs) -> TVAIOModel:
        inst = cls(**kwargs)
        return await inst.save(force_insert=True)

    @classmethod
    async def bulk_create(cls, **_):
        # TODO: To implement
        raise NotImplementedError("AIOModel doesnt support `bulk_create`")

    @classmethod
    async def bulk_update(cls, **_):
        # TODO: To implement
        raise NotImplementedError("AIOModel doesnt support `bulk_update`")

    # Queryset methods
    # ----------------

    @classmethod
    def select(cls: type[TVAIOModel], *fields) -> ModelSelect[TVAIOModel]:
        return ModelSelect(
            cls, fields or cls._meta.sorted_fields, is_default=not fields
        )

    @classmethod
    def update(cls: type[TVAIOModel], __data=None, **update) -> ModelUpdate[TVAIOModel]:
        return ModelUpdate(cls, cls._normalize_data(__data, update))

    @classmethod
    def insert(cls: type[TVAIOModel], __data=None, **insert) -> ModelInsert[TVAIOModel]:
        return ModelInsert(cls, cls._normalize_data(__data, insert))

    @classmethod
    def insert_many(
        cls: type[TVAIOModel], rows: Iterable, fields=None
    ) -> ModelInsert[TVAIOModel]:
        rows = [row.__data__ if isinstance(row, Model) else row for row in rows]
        if not rows:
            raise ModelInsert.DefaultValuesException("Error: no rows to insert.")

        return ModelInsert(cls, insert=rows, columns=fields)

    @classmethod
    def insert_from(cls: type[TVAIOModel], query, fields) -> ModelInsert[TVAIOModel]:
        columns = [
            getattr(cls, field) if isinstance(field, str) else field for field in fields
        ]
        return ModelInsert(cls, insert=query, columns=columns)

    @classmethod
    def raw(cls: type[TVAIOModel], sql, *params) -> ModelRaw[TVAIOModel]:
        return ModelRaw(cls, sql, params)

    @classmethod
    def delete(cls: type[TVAIOModel]) -> ModelDelete[TVAIOModel]:
        return ModelDelete(cls)

    # Instance methods
    # ----------------

    async def save(self, **kwargs) -> Self:
        return await self._manager.save(self, **kwargs)

    async def delete_instance(self, **kwargs):
        return await self._manager.delete_instance(self, **kwargs)

    # Support await syntax
    # --------------------

    def __await__(self):
        return self.__anext__().__await__()

    async def __anext__(self):
        return self


class AIOQuery(Generic[TVAIOModel]):

    model: type[TVAIOModel]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.manager = self.model._manager

    def __await__(self) -> Generator[Any, None, List[TVAIOModel]]:
        return self.manager.run(self).__await__()  # type: ignore


class BaseModelSelect(AIOQuery[TVAIOModel]):
    def union_all(self, rhs):
        return ModelCompoundSelectQuery(self.model, self, "UNION ALL", rhs)

    __add__ = union_all

    def union(self, rhs):
        return ModelCompoundSelectQuery(self.model, self, "UNION", rhs)

    __or__ = union

    def intersect(self, rhs):
        return ModelCompoundSelectQuery(self.model, self, "INTERSECT", rhs)

    __and__ = intersect

    def except_(self, rhs):
        return ModelCompoundSelectQuery(self.model, self, "EXCEPT", rhs)

    __sub__ = except_

    async def prefetch(self, *subqueries) -> List[TVAIOModel]:
        return await self.manager.prefetch(self, *subqueries)


class ModelSelect(BaseModelSelect[TVAIOModel], ModelSelect_):
    _limit: int

    def __aiter__(self) -> AsyncGenerator[TVAIOModel, None]:
        return self.manager.run(self).__aiter__()

    def __getitem__(
        self, value
    ) -> Union[ModelSelect[TVAIOModel], Coroutine[Any, Any, TVAIOModel]]:
        limit, offset = 1, value
        if isinstance(value, slice):
            limit, offset = value.stop - value.start, value.start

        query = self.limit(limit).offset(offset)  # type: ignore
        if limit == 1:
            return query.get()
        return query

    async def peek(self, n=1) -> TVAIOModel:
        if n == 1:
            return await self.manager.fetchone(self)
        return await self.manager.fetchmany(n, self)

    def first(self, n=1) -> Coroutine[Any, Any, TVAIOModel]:
        query = self
        if self._limit != n:
            query = self.limit(n)
        return query.peek(n)

    async def scalar(self, as_tuple=False, as_dict=False):
        if as_dict:
            return await self.dicts().peek()
        row = await self.tuples().peek()
        return row[0] if row and not as_tuple else row

    async def scalars(self) -> List[Any]:
        return [row[0] for row in await self.tuples()]

    async def count(self) -> int:
        return await self.manager.count(self)

    async def exists(self) -> bool:
        clone: ModelSelect = self.columns(SQL("1"))
        clone._limit = 1
        clone._offset = None
        return bool(await clone.scalar())

    async def get(self, **kwargs) -> TVAIOModel:
        if kwargs:
            return await self.filter(**kwargs).first()

        return await self.first()

    # Type helpers
    with_cte: Callable[..., ModelSelect[TVAIOModel]]
    where: Callable[..., ModelSelect[TVAIOModel]]
    orwhere: Callable[..., ModelSelect[TVAIOModel]]
    order_by: Callable[..., ModelSelect[TVAIOModel]]
    order_by_extend: Callable[..., ModelSelect[TVAIOModel]]
    limit: Callable[[Union[int, None]], ModelSelect[TVAIOModel]]
    offset: Callable[[int], ModelSelect[TVAIOModel]]
    paginate: Callable[..., ModelSelect[TVAIOModel]]

    columns: Callable[..., ModelSelect[TVAIOModel]]
    select_extend: Callable[..., ModelSelect[TVAIOModel]]
    from_: Callable[..., ModelSelect[TVAIOModel]]
    join: Callable[..., ModelSelect[TVAIOModel]]
    group_by: Callable[..., ModelSelect[TVAIOModel]]
    having: Callable[..., ModelSelect[TVAIOModel]]
    distinct: Callable[..., ModelSelect[TVAIOModel]]
    window: Callable[..., ModelSelect[TVAIOModel]]
    for_update: Callable[..., ModelSelect[TVAIOModel]]
    lateral: Callable[..., ModelSelect[TVAIOModel]]


class ModelCompoundSelectQuery(BaseModelSelect[TVAIOModel], ModelCompoundSelectQuery_):
    pass


class ModelUpdate(AIOQuery[TVAIOModel], ModelUpdate_):
    pass


class ModelInsert(AIOQuery[TVAIOModel], ModelInsert_):
    pass


class ModelDelete(AIOQuery[TVAIOModel], ModelDelete_):
    pass


class ModelRaw(AIOQuery[TVAIOModel], ModelRaw_):
    pass


from .manager import Manager  # noqa
