"""TODO: To implement."""

from __future__ import annotations

import typing as t

from peewee import (
    Model, ModelBase,
    ModelDelete as ModelDelete_,
    ModelInsert as ModelInsert_,
    ModelRaw as ModelRaw_,
    ModelSelect as ModelSelect_,
    ModelUpdate as ModelUpdate_,
)


class AIOModelBase(ModelBase):

    inheritable = ModelBase.inheritable & {'manager'}

    def __new__(cls, name, bases, attrs):
        cls = super(AIOModelBase, cls).__new__(cls, name, bases, attrs)
        meta = cls._meta
        if getattr(meta, 'manager', None) and not meta.database:
            meta.database = meta.manager.pw_database

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
    async def get_or_create(cls, **kwargs) -> t.Tuple[AIOModel, bool]:
        return await cls._meta.manager.get_or_create(cls, **kwargs)

    @classmethod
    async def create(cls, **kwargs) -> AIOModel:
        return await cls._meta.manager.create(cls, **kwargs)

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
    def insert_from(cls, query, fields) -> ModelInsert:
        columns = [getattr(cls, field) if isinstance(field, str) else field for field in fields]
        return ModelInsert(cls, insert=query, columns=columns)

    @classmethod
    def replace(cls, __data=None, **insert) -> ModelInsert:
        return cls.insert(__data, **insert).on_conflict('REPLACE')

    @classmethod
    def replace_many(cls, rows, fields=None) -> ModelInsert:
        return (cls.insert_many(rows=rows, fields=fields).on_conflict('REPLACE'))

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


class AIOQuery:

    def __await__(self):
        return self.model._meta.manager.run(self).__await__()


class ModelSelect(AIOQuery, ModelSelect_):

    async def count(self):
        return await self.model._meta.manager.count(self)

    def __aiter__(self):
        return self.model._meta.manager.run(self).__aiter__()


class ModelUpdate(AIOQuery, ModelUpdate_):
    pass


class ModelInsert(AIOQuery, ModelInsert_):
    pass


class ModelDelete(AIOQuery, ModelDelete_):
    pass


class ModelRaw(AIOQuery, ModelRaw_):
    pass
