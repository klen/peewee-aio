"""TODO: To implement."""

from __future__ import annotations

import typing as t

from peewee import (
    database_required,
    Model, ModelBase, SQL,
    ModelDelete as ModelDelete_,
    ModelInsert as ModelInsert_,
    ModelRaw as ModelRaw_,
    ModelSelect as ModelSelect_,
    ModelUpdate as ModelUpdate_,
    ForeignKeyAccessor,
    ForeignKeyField
)


class AIOForeignKeyAccessor(ForeignKeyAccessor):

    def get_rel_instance(self, instance: Model) -> t.Union[
            Model, None, t.Coroutine[t.Any, t.Any, Model]]:
        value = instance.__data__.get(self.name)
        if value is not None or self.name in instance.__rel__:
            if self.name not in instance.__rel__ and self.field.lazy_load:
                return self.load_rel(instance, value)
            return instance.__rel__.get(self.name, value)
        elif not self.field.null:
            raise self.rel_model.DoesNotExist
        return value

    async def load_rel(self, instance: Model, value: t.Any) -> Model:
        obj = await self.rel_model.get(self.field.rel_field == value)
        instance.__rel__[self.name] = obj
        return obj


class AIOForeignKeyField(ForeignKeyField):

    accessor_class = AIOForeignKeyAccessor


class AIOModelBase(ModelBase):

    inheritable = ModelBase.inheritable & {'manager'}

    def __new__(cls, name, bases, attrs):
        cls = super(AIOModelBase, cls).__new__(cls, name, bases, attrs)
        meta = cls._meta
        if getattr(meta, 'manager', None) and not meta.database:
            meta.database = meta.manager.pw_database

        # Patch foreign keys
        for value in meta.fields.values():
            if isinstance(value, ForeignKeyField):
                setattr(
                    value.model, value.name, AIOForeignKeyAccessor(value.model, value, value.name))

        return cls


class AIOModel(Model, metaclass=AIOModelBase):

    # Class methods
    # -------------

    @classmethod
    async def create_table(cls, safe=True, **kwargs):
        return await cls._meta.manager.create_tables(cls, safe=safe, **kwargs)

    @classmethod
    async def drop_table(cls, safe=True, **kwargs):
        return await cls._meta.manager.drop_tables(cls, safe=safe, **kwargs)

    @classmethod
    async def get_or_none(cls, *args, **kwargs) -> t.Optional[AIOModel]:
        return await cls._meta.manager.get_or_none(cls, *args, **kwargs)

    @classmethod
    async def get(cls, *args, **kwargs) -> AIOModel:
        return await cls._meta.manager.get(cls, *args, **kwargs)

    @classmethod
    async def get_by_id(cls, pk) -> AIOModel:
        return await cls._meta.manager.get_by_id(cls, pk)

    @classmethod
    async def set_by_id(cls, key, value):
        return await cls._meta.manager.set_by_id(cls, key, value)

    @classmethod
    async def delete_by_id(cls, pk):
        return await cls._meta.manager.delete_by_id(cls, pk)

    @classmethod
    async def get_or_create(cls, defaults: t.Dict = None, **kwargs) -> t.Tuple[AIOModel, bool]:
        async with cls._meta.manager.aio_database.transaction():
            try:
                return (await cls.get(**kwargs), False)
            except cls.DoesNotExist:
                return (await cls.create(**dict(defaults or {}, **kwargs)), True)

    @classmethod
    async def create(cls, **kwargs) -> AIOModel:
        inst = cls(**kwargs)
        return await inst.save(force_insert=True)

    # Queryset methods
    # ----------------

    @classmethod
    def select(cls, *fields) -> ModelSelect:
        return ModelSelect(cls, fields or cls._meta.sorted_fields, is_default=not fields)

    @classmethod
    def update(cls, __data=None, **update) -> ModelUpdate:
        return ModelUpdate(cls, cls._normalize_data(__data, update))

    @classmethod
    def insert(cls, __data=None, **insert) -> ModelInsert:
        return ModelInsert(cls, cls._normalize_data(__data, insert))

    @classmethod
    def insert_many(cls, rows, fields=None) -> ModelInsert:
        rows = [row.__data__ if isinstance(row, Model) else row for row in rows]
        return ModelInsert(cls, insert=rows, columns=fields)

    @classmethod
    def insert_from(cls, query, fields) -> ModelInsert:
        columns = [getattr(cls, field) if isinstance(field, str) else field for field in fields]
        return ModelInsert(cls, insert=query, columns=columns)

    @classmethod
    def raw(cls, sql, *params) -> ModelRaw:
        return ModelRaw(cls, sql, params)

    @classmethod
    def delete(cls) -> ModelDelete:
        return ModelDelete(cls)

    # Instance methods
    # ----------------

    async def save(self, **kwargs):
        return await self._meta.manager.save(self, **kwargs)

    async def delete_instance(self, **kwargs):
        return await self._meta.manager.delete_instance(self, **kwargs)

    # Support await syntax
    # --------------------

    def __await__(self):
        return self.__anext__().__await__()

    async def __anext__(self):
        return self


class AIOQuery:

    def __init__(self, *args, **kwargs):
        super(AIOQuery, self).__init__(*args, **kwargs)
        self.manager = self.model._meta.manager

    def __await__(self):
        return self.manager.run(self).__await__()


class ModelSelect(AIOQuery, ModelSelect_):

    def __aiter__(self):
        return self.manager.run(self).__aiter__()

    @database_required
    async def scalar(self, database, as_tuple=False):
        row = await self.tuples().peek(database)
        return row[0] if row and not as_tuple else row

    @database_required
    async def exists(self, database):
        clone = self.columns(SQL('1'))
        clone._limit = 1
        clone._offset = None
        return bool(await clone.scalar())

    @database_required
    async def peek(self, database, n=1):
        if n == 1:
            return await self.manager.fetchone(self)
        return await self.manager.fetchmany(n, self)

    async def count(self):
        return await self.manager.count(self)

    async def get(self):
        return await self.first()

    async def prefetch(self, *subqueries):
        return await self.manager.prefetch(self, *subqueries)


class ModelUpdate(AIOQuery, ModelUpdate_):
    pass


class ModelInsert(AIOQuery, ModelInsert_):
    pass


class ModelDelete(AIOQuery, ModelDelete_):
    pass


class ModelRaw(AIOQuery, ModelRaw_):
    pass
