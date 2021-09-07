from __future__ import annotations

import typing as t

from contextlib import asynccontextmanager, contextmanager

from aio_databases import Database
from peewee import (
    BaseQuery,
    Context,
    Database as PWDatabase,
    Delete,
    Model as PWModel,
    ModelRaw,
    Query,
    SQL,
    SchemaManager,
    Select,
    __exception_wrapper__,
    fn,
    logger,
    sort_models,
)

from .databases import get_db


TMODEL = t.TypeVar('TMODEL', bound=PWModel)


class Manager:
    """Manage database and models."""

    aio_database: Database
    pw_database: PWDatabase
    models: t.Set[PWModel]

    def __init__(self, database: t.Union[Database, str], **backend_options):
        """Initialize dialect and database."""
        if not isinstance(database, Database):
            database = Database(database, logger=logger, **backend_options)

        self.aio_database = database
        self.pw_database = get_db(database)
        self.models = set()

    def register(self, Model: PWModel):
        """Register a model with the manager."""
        Model._meta.database = self.pw_database
        self.models.add(Model)
        return Model

    def __iter__(self):
        """Iterate through registered models."""
        return iter(sort_models(self.models))

    # Working with AIO-Databases
    # --------------------------

    async def connect(self):
        await self.aio_database.connect()
        return self

    __aenter__ = connect

    async def disconnect(self, *args):
        await self.aio_database.disconnect()

    __aexit__ = disconnect

    async def execute(self, sql: t.Any, *params, **opts) -> t.Any:
        async with process(sql, params, True) as (sql, params, _):
            return await self.aio_database.execute(sql, *params, **opts)

    async def fetchval(self, sql: t.Any, *params, **opts) -> t.Any:
        async with process(sql, params, True) as (sql, params, _):
            return await self.aio_database.fetchval(sql, *params, **opts)

    async def fetchall(self, sql: t.Any, *params, raw: bool = False, **opts) -> t.Any:
        async with process(sql, params, raw) as (sql, params, constructor):
            res = await self.aio_database.fetchall(sql, *params, **opts)
            return constructor(res)

    async def fetchmany(self, size: int, sql: t.Any, *params, raw: bool = False, **opts) -> t.Any:
        async with process(sql, params, raw) as (sql, params, constructor):
            res = await self.aio_database.fetchmany(size, sql, *params, **opts)
            return constructor(res)

    async def fetchone(self, sql: t.Any, *params, raw: bool = False, **opts) -> t.Any:
        async with process(sql, params, raw) as (sql, params, constructor):
            res = await self.aio_database.fetchone(sql, *params, **opts)
            return constructor(res)

    async def iterate(self, sql: t.Any, *params, raw: bool = False, **opts) -> t.AsyncIterator:
        async with process(sql, params, raw) as (sql, params, constructor):
            async for res in self.aio_database.iterate(sql, *params, **opts):
                yield constructor(res)

    def connection(self, *params, **opts):
        return self.aio_database.connection(*params, **opts)

    def transaction(self, *params, **opts):
        return self.aio_database.transaction(*params, **opts)

    # Working with Peewee
    # -------------------

    @contextmanager
    def allow_sync(self):
        db = self.pw_database
        db.enabled = True

        try:
            yield self
        finally:
            if not db.is_closed():
                db.close()

            db.enabled = False

    def run(self, query: Query, *, iterate: bool = False) -> t.Any:
        if isinstance(query, (Select, ModelRaw)):
            return RunWrapper(self, query)

        return self.execute(query)

    async def create_tables(self, *Models: t.Type[PWModel], safe=True, **opts):
        for Model in sort_models(Models):
            schema: SchemaManager = Model._schema

            # Create sequences
            if schema.database.sequences:
                for field in Model._meta.sorted_fields:
                    if field.sequence:
                        ctx = schema._create_sequence(field)
                        if ctx:
                            await self.execute(ctx)

            # Create table
            ctx = schema._create_table(safe=safe, **opts)
            await self.execute(ctx)

            # Create indexes
            for query in schema._create_indexes(safe=safe):
                await self.execute(query)

    async def drop_tables(self, *Models: t.Type[PWModel], **opts):
        for Model in reversed(sort_models(Models)):
            schema: SchemaManager = Model._schema
            ctx = schema._drop_table(**opts)
            await self.execute(ctx)

    async def get(self, source: t.Union[t.Type[TMODEL], Query], *args, **kwargs) -> TMODEL:
        query, model = ((source, source.model) if isinstance(source, Query)
                        else (source.select(), source))

        query = query.where(*args) if args else query
        query = query.filter(**kwargs) if kwargs else query

        res = await self.fetchone(query)
        if res is None:
            raise model.DoesNotExist

        return res

    async def get_or_create(self, Model: t.Type[TMODEL],
                            defaults: t.Dict = None, **kwargs) -> t.Tuple[TMODEL, bool]:
        async with self.aio_database.transaction():
            try:
                return (await self.get(Model, **kwargs), False)
            except Model.DoesNotExist:
                return (await self.create(Model, **dict(defaults or {}, **kwargs)), True)

    async def save(self, inst: TMODEL,  # noqa
                   force_insert: bool = False, only: t.Sequence = None) -> TMODEL:
        field_dict = inst.__data__.copy()
        pk_field = pk_value = None
        if inst._meta.primary_key is not False:
            pk_field = inst._meta.primary_key
            pk_value = inst._pk

        if only is not None:
            field_dict = inst._prune_fields(field_dict, only)

        elif inst._meta.only_save_dirty and not force_insert:
            field_dict = inst._prune_fields(field_dict, inst.dirty_fields)
            if not field_dict:
                inst._dirty.clear()
                return inst

        inst._populate_unsaved_relations(field_dict)
        if inst._meta.auto_increment and pk_field and pk_value is None:
            field_dict.pop(pk_field.name, None)

        if pk_field is None:
            await self.execute(inst.insert(**field_dict))

        else:
            # Update
            if pk_value is not None and not force_insert:
                if inst._meta.composite_key:
                    for pk_part_name in pk_field.field_names:
                        field_dict.pop(pk_part_name, None)
                else:
                    field_dict.pop(pk_field.name, None)
                if not field_dict:
                    raise ValueError('no data to save!')

                await self.execute(inst.update(**field_dict).where(inst._pk_expr()))

            # Insert
            else:
                query = inst.insert(**field_dict)
                if query._returning:
                    pk = await self.fetchval(query)
                else:
                    pk = await self.execute(query)

                if pk is not None and (inst._meta.auto_increment or pk_value is None):
                    inst._pk = pk

        inst._dirty.clear()
        return inst

    async def create(self, Model: t.Type[TMODEL], **values) -> TMODEL:
        inst = Model(**values)
        inst = await self.save(inst, force_insert=True)
        return inst

    async def delete(self, source: t.Union[Delete, PWModel],
                     recursive: bool = True, delete_nullable: bool = False):

        if isinstance(source, PWModel):
            if recursive:
                for query, fk in reversed(list(source.dependencies(delete_nullable))):
                    if fk.null and not delete_nullable:
                        await self.execute(fk.model.update(**{fk.name: None}).where(query))

                    else:
                        await self.execute(fk.model.delete().where(query))

                await self.execute(source.delete().where(source._pk_expr()))

        else:
            await self.execute(source)

    async def count(self, query: Query, clear_limit: bool = False):
        query = query.order_by()
        if clear_limit:
            query._limit = query._offset = None

        try:
            if query._having is None and query._group_by is None and \
               query._windows is None and query._distinct is None and \
               query._simple_distinct is not True:
                query = query.select(SQL('1'))
        except AttributeError:
            pass

        query = Select([query], [fn.COUNT(SQL('1'))])
        query._database = self.pw_database
        return await self.fetchval(query)


DEFAULT_CONSTRUCTOR = lambda r: r  # noqa


@asynccontextmanager
async def process(query: t.Any, params: t.Sequence, raw: bool) -> t.AsyncGenerator:
    constructor = DEFAULT_CONSTRUCTOR

    if isinstance(query, BaseQuery):
        if not raw:
            constructor = Constructor(query)
        query, params = query.sql()

    if isinstance(query, Context):
        query, params = query.query()

    with __exception_wrapper__:
        yield query, params, constructor


class RunWrapper:

    __slots__ = 'manager', 'query', 'gen'

    def __init__(self, manager: Manager, query: BaseQuery):
        self.query = query
        self.manager = manager
        self.gen: t.Optional[t.AsyncIterator] = None

    def __aiter__(self) -> RunWrapper:
        self.gen = self.manager.iterate(self.query)
        return self

    def __await__(self):
        return self.manager.fetchall(self.query).__await__()

    def __anext__(self):
        return self.gen.__anext__()


class FakeCursor:

    __slots__ = 'description',

    def __init__(self, res: t.Mapping):
        self.description = [[k] for k in res.keys()]


class Constructor:
    """Process results."""

    __slots__ = 'query', 'processor'

    def __init__(self, query: Query):
        self.query = query
        self.processor: t.Optional[t.Callable] = None

    def __call__(self, res: t.Union[
            t.Mapping, t.Sequence[t.Mapping]]) -> t.Union[t.Any, t.Sequence[t.Any]]:
        """Process rows."""
        if not res:  # None or empty sequence
            return res

        if isinstance(res, t.Sequence):
            processor = self.get_processor(res[0])
            return [processor(r) for r in res]

        processor = self.get_processor(res)
        return processor(res)

    def get_processor(self, rec: t.Mapping) -> t.Callable:
        """Get and cache a rows processor."""
        if self.processor is None:
            cursor = FakeCursor(rec)
            wrapper = self.query._get_cursor_wrapper(cursor)
            wrapper.initialize()
            self.processor = wrapper.process_row

        return self.processor
