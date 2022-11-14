from __future__ import annotations

from contextlib import contextmanager
from typing import (Any, AsyncIterator, Callable, Dict, Generator, Iterator, List, Mapping,
                    Optional, Sequence, Tuple, Type, TypeVar, Union)
from weakref import WeakSet

from aio_databases.backends import ABCConnection
from aio_databases.database import ConnectionContext, Database, TransactionContext
from peewee import (EXCEPTIONS, PREFETCH_TYPE, SQL, BaseQuery, Context, Insert, IntegrityError,
                    InternalError)
from peewee import Model as PWModel
from peewee import (ModelRaw, OperationalError, Query, SchemaManager, Select, __exception_wrapper__,
                    fn, logger, prefetch_add_subquery, sort_models)

from .databases import Database as PWDatabase
from .databases import get_db
from .model import AIOModel

TMODEL = TypeVar("TMODEL", bound=PWModel)
TMANAGER = TypeVar("TMANAGER", bound="Manager")


class Manager:
    """Manage database and models."""

    aio_database: Database
    pw_database: PWDatabase
    models: "WeakSet[type[PWModel]]"

    def __init__(
        self, database: Union[Database, str], convert_params=True, **backend_options
    ):
        """Initialize dialect and database."""
        if not isinstance(database, Database):
            database = Database(
                database,
                logger=logger,
                convert_params=convert_params,
                **backend_options,
            )

        self.models = WeakSet()
        self.aio_database = database
        self.pw_database = get_db(database)

        class Model(AIOModel):
            _manager = self

        self.Model = Model

    def register(self, Model: type[TMODEL]) -> type[TMODEL]:
        """Register a model with the manager."""
        Model._manager = self  # type: ignore
        Model._meta.database = self.pw_database
        self.models.add(Model)
        return Model

    def __iter__(self) -> Iterator:
        """Iterate through registered models."""
        return iter(sort_models(self.models))

    # Working with AIO-Databases
    # --------------------------

    @property
    def current_conn(self) -> Optional[ABCConnection]:
        return self.aio_database.current_conn

    async def connect(self: TMANAGER) -> TMANAGER:
        """Connect to the database (initialize the database's pool)"""
        await self.aio_database.connect()
        return self

    __aenter__ = connect

    async def disconnect(self, *_):
        """Disconnect from the database (close a pool, connections)"""
        await self.aio_database.disconnect()

    __aexit__ = disconnect

    async def execute(self, query: Any, *params, **opts) -> Any:
        """Execute a given query with the given params."""
        with process(query, params, True) as (sql, params, _):
            res = await self.aio_database.execute(sql, *params, **opts)
            if res is None:
                return res

            if isinstance(query, Insert) and query._query_type == Insert.SIMPLE:
                return res[1]

            return res[0]

    async def fetchval(self, sql: Any, *params, **opts) -> Any:
        """Execute the given SQL and fetch a value."""
        with process(sql, params, True) as (sql, params, _):
            return await self.aio_database.fetchval(sql, *params, **opts)

    async def fetchall(self, sql: Any, *params, raw: bool = False, **opts) -> Any:
        """Execute the given SQL and fetch all."""
        with process(sql, params, raw) as (sql, params, constructor):
            res = await self.aio_database.fetchall(sql, *params, **opts)
            return constructor(res)

    async def fetchmany(
        self, size: int, sql: Any, *params, raw: bool = False, **opts
    ) -> Any:
        """Execute the given SQL and fetch many of the size."""
        with process(sql, params, raw) as (sql, params, constructor):
            res = await self.aio_database.fetchmany(size, sql, *params, **opts)
            return constructor(res)

    async def fetchone(self, sql: Any, *params, raw: bool = False, **opts) -> Any:
        """Execute the given SQL and fetch one."""
        with process(sql, params, raw) as (sql, params, constructor):
            res = await self.aio_database.fetchone(sql, *params, **opts)
            return constructor(res)

    async def iterate(
        self, sql: Any, *params, raw: bool = False, **opts
    ) -> AsyncIterator:
        """Execute the given SQL and iterate through results."""
        with process(sql, params, raw) as (sql, params, constructor):
            async for res in self.aio_database.iterate(sql, *params, **opts):
                yield constructor(res)

    def connection(self, *params, **opts) -> ConnectionContext:
        """Initialize a connection to the database.."""
        return self.aio_database.connection(*params, **opts)

    def transaction(self, *params, **opts) -> TransactionContext:
        """Initialize a transaction to the database.."""
        return self.aio_database.transaction(*params, **opts)

    # Working with Peewee
    # -------------------

    @contextmanager
    def allow_sync(self):
        """Enable sync operations for Peewee ORM."""
        db = self.pw_database
        db.enabled = True

        try:
            yield self
        finally:
            if not db.is_closed():
                db.close()

            db.enabled = False

    # Query methods
    # -------------

    def run(self, query: Query) -> Any:
        """Run the given Peewee ORM Query."""
        if isinstance(query, (Select, ModelRaw)) or getattr(query, "_returning", None):
            return RunWrapper(self, query)

        return self.execute(query)

    async def count(self, query: Select, clear_limit: bool = False) -> Any:
        """Execute the given Peewee ORM Query and get a count of rows."""
        query = query.order_by()  # type: ignore
        if clear_limit:
            query._limit = query._offset = None

        try:
            if (
                query._having is None
                and query._group_by is None
                and query._windows is None
                and query._distinct is None
                and query._simple_distinct is not True
            ):
                query = query.select(SQL("1"))
        except AttributeError:
            pass

        query = Select([query], [fn.COUNT(SQL("1"))])
        query._database = self.pw_database
        return await self.fetchval(query)

    async def prefetch(self, sq: Query, *subqueries, **kwargs) -> Any:
        """Prefetch results for the given query and subqueries.."""
        if not subqueries:
            return await self.run(sq)

        result = None
        prefetch_type = kwargs.pop("prefetch_type", PREFETCH_TYPE.WHERE)
        fixed_queries = prefetch_add_subquery(sq, subqueries, prefetch_type)
        deps: Dict[PWModel, Dict] = {}
        rel_map: Dict[PWModel, List] = {}
        for pq in reversed(fixed_queries):
            query_model = pq.model
            if pq.fields:
                for rel_model in pq.rel_models:
                    rel_map.setdefault(rel_model, [])
                    rel_map[rel_model].append(pq)

            deps.setdefault(query_model, {})
            id_map = deps[query_model]
            has_relations = bool(rel_map.get(query_model))
            result = await self.run(pq.query)
            for instance in result:
                if pq.fields:
                    pq.store_instance(instance, id_map)
                if has_relations:
                    for rel in rel_map[query_model]:
                        rel.populate_instance(instance, deps[rel.model])

        return result

    # Model methods
    # -------------

    async def create_tables(self, *Models: type[PWModel], safe=True, **opts):
        """Create tables for the given models or all registered with the manager."""
        Models = Models or tuple(self.models)
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
                try:
                    await self.execute(query)
                except OperationalError:
                    if not safe:
                        raise

    async def drop_tables(self, *Models: type[PWModel], **opts):
        """Drop tables for the given models or all registered with the manager."""
        Models = Models or tuple(self.models)
        for Model in reversed(sort_models(Models)):
            schema: SchemaManager = Model._schema
            ctx = schema._drop_table(**opts)
            await self.execute(ctx)

    async def get_or_none(
        self, Model: type[TMODEL], *args, **kwargs
    ) -> Optional[TMODEL]:
        query = Model.select()
        if kwargs:
            query = query.filter(**kwargs)

        if args:
            query = query.where(*args)

        return await self.fetchone(query)

    async def get(self, Model: type[TMODEL], *args, **kwargs) -> TMODEL:
        res = await self.get_or_none(Model, *args, **kwargs)
        if res is None:
            raise Model.DoesNotExist
        return res

    async def get_by_id(self, Model: type[TMODEL], pk) -> TMODEL:
        return await self.get(Model, Model._meta.primary_key == pk)

    async def set_by_id(self, Model: type[PWModel], key, value) -> Any:
        qs = (
            Model.insert(value)
            if key is None
            else Model.update(value).where(Model._meta.primary_key == key)
        )
        return await self.execute(qs)

    async def delete_by_id(self, Model: type[PWModel], pk):
        return await self.execute(Model.delete().where(Model._meta.primary_key == pk))

    async def get_or_create(
        self, Model: Type[TMODEL], defaults: Optional[Dict] = None, **kwargs
    ) -> Tuple[TMODEL, bool]:
        async with self.aio_database.transaction():
            try:
                return (await self.get(Model, **kwargs), False)
            except Model.DoesNotExist:
                return (
                    await self.create(Model, **dict(defaults or {}, **kwargs)),
                    True,
                )

    async def create(self, Model: type[TMODEL], **values) -> TMODEL:
        inst = Model(**values)
        inst = await self.save(inst, force_insert=True)
        return inst

    # Instance methods
    # ----------------

    async def save(  # noqa
        self,
        inst: TMODEL,
        force_insert: bool = False,
        only: Optional[Sequence] = None,
        on_conflict_ignore: bool = False,
    ) -> TMODEL:
        field_dict = inst.__data__.copy()
        pk_field = pk_value = None
        meta = inst._meta  # type: ignore
        if meta.primary_key is not False:
            pk_field = meta.primary_key
            pk_value = inst._pk

        if only is not None:
            field_dict = inst._prune_fields(field_dict, only)

        elif meta.only_save_dirty and not force_insert:
            field_dict = inst._prune_fields(field_dict, inst.dirty_fields)
            if not field_dict:
                inst._dirty.clear()
                return inst

        inst._populate_unsaved_relations(field_dict)
        if meta.auto_increment and pk_field and pk_value is None:
            field_dict.pop(pk_field.name, None)

        if pk_field is None:
            await self.execute(
                inst.insert(**field_dict).on_confict_ignore(on_conflict_ignore)
            )

        else:
            # Update
            if pk_value is not None and not force_insert:
                if meta.composite_key:
                    for pk_part_name in pk_field.field_names:
                        field_dict.pop(pk_part_name, None)
                else:
                    field_dict.pop(pk_field.name, None)
                if not field_dict:
                    raise ValueError("no data to save!")

                await self.execute(inst.update(**field_dict).where(inst._pk_expr()))

            # Insert
            else:
                query = inst.insert(**field_dict).on_conflict_ignore(on_conflict_ignore)
                if query._returning:
                    pk = await self.fetchval(query)
                else:
                    pk = await self.execute(query)

                if pk is not None and (meta.auto_increment or pk_value is None):
                    inst._pk = pk

        inst._dirty.clear()
        return inst

    async def delete_instance(
        self, inst: PWModel, recursive: bool = False, delete_nullable: bool = False
    ):
        if recursive:
            for query, fk in reversed(list(inst.dependencies(delete_nullable))):
                if fk.null and not delete_nullable:
                    await self.execute(fk.model.update(**{fk.name: None}).where(query))

                else:
                    await self.execute(fk.model.delete().where(query))

        return await self.execute(inst.delete().where(inst._pk_expr()))


DEFAULT_CONSTRUCTOR = lambda r: r  # noqa
EXCEPTIONS["UniqueViolationError"] = IntegrityError
EXCEPTIONS["NotNullViolationError"] = InternalError
EXCEPTIONS["DuplicateTableError"] = OperationalError


@contextmanager
def process(query: Any, params: Sequence, raw: bool) -> Generator:
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

    __slots__ = "manager", "query", "gen"

    def __init__(self, manager: Manager, query: BaseQuery):
        self.query = query
        self.manager = manager
        self.gen = self.manager.iterate(self.query)

    def __aiter__(self) -> RunWrapper:
        return self

    def __await__(self):
        return self.manager.fetchall(self.query).__await__()

    def __anext__(self):
        return self.gen.__anext__()


class FakeCursor:

    __slots__ = ("description",)

    def __init__(self, res: Mapping):
        self.description = [[k] for k in res.keys()]


class Constructor:
    """Process results."""

    __slots__ = "query", "processor"

    def __init__(self, query: BaseQuery):
        self.query = query
        self.processor: Optional[Callable] = None

    def __call__(
        self, res: Union[Mapping, Sequence[Mapping]]
    ) -> Union[Any, Sequence[Any]]:
        """Process rows."""
        if not res:  # None or empty sequence
            return res

        if isinstance(res, Sequence):
            processor = self.get_processor(res[0])
            return [processor(r) for r in res]

        processor = self.get_processor(res)
        return processor(res)

    def get_processor(self, rec: Mapping) -> Callable:
        """Get and cache a rows processor."""
        if self.processor is None:
            cursor = FakeCursor(rec)
            wrapper = self.query._get_cursor_wrapper(cursor)
            wrapper.initialize()
            self.processor = wrapper.process_row

        return self.processor
