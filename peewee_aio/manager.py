from __future__ import annotations

from contextlib import contextmanager
from functools import cached_property
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    Callable,
    Coroutine,
    Dict,
    Generator,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Type,
    Union,
    overload,
)
from weakref import WeakSet

from aio_databases.database import Database
from peewee import (
    EXCEPTIONS,  # type: ignore[]
    PREFETCH_TYPE,
    SQL,
    BaseQuery,
    Context,
    Insert,
    IntegrityError,
    InternalError,
    ModelRaw,
    ModelSelect,
    Node,
    OperationalError,
    Query,
    SchemaManager,
    Select,
    __exception_wrapper__,  # type: ignore[]
    fn,
    logger,  # type: ignore[]
    prefetch_add_subquery,  # type: ignore[]
    sort_models,  # type: ignore[]
)
from peewee import Model as PWModel

from .databases import Database as PWDatabase
from .databases import get_db
from .model import AIOModel

if TYPE_CHECKING:
    from .types import TVModel


class Manager(Database):
    """Manage database and models."""

    pw_database: PWDatabase
    models: "WeakSet[Type[PWModel]]"

    def __init__(
        self,
        url: str,
        **backend_options,
    ):
        """Initialize dialect and database."""
        backend_options.setdefault("convert_params", True)
        super().__init__(url, logger=logger, **backend_options)

        self.models = WeakSet()
        self.pw_database = get_db(self)

    @cached_property
    def Model(self) -> Type[AIOModel]:  # noqa: N802
        """Get the default model class."""

        class Model(AIOModel):
            _manager = self

        return Model

    def register(self, model_cls: Type[TVModel]) -> Type[TVModel]:
        """Register a model with the manager."""
        model_cls._manager = self  # type: ignore[]
        model_cls._meta.database = self.pw_database  # type: ignore[]
        self.models.add(model_cls)
        return model_cls

    def __iter__(self) -> Iterator:
        """Iterate through registered models."""
        return iter(sort_models(self.models))

    # Working with AIO-Databases
    # --------------------------

    async def execute(self, query: Any, *params, **opts) -> Any:
        """Execute a given query with the given params."""
        with process(query, params, raw=True) as (sql, params, _):
            res = await super().execute(sql, *params, **opts)
            if res is None:
                return res

            if isinstance(query, Insert) and query._query_type == Insert.SIMPLE:  # type: ignore[]
                return res[1]

            return res[0]

    async def fetchval(self, query: Any, *params, **opts) -> Any:
        """Execute the given SQL and fetch a value."""
        with process(query, params, raw=True) as (query, params, _):
            return await super().fetchval(query, *params, **opts)

    async def fetchall(self, query: Any, *params, raw: bool = False, **opts) -> Any:
        """Execute the given SQL and fetch all."""
        with process(query, params, raw=raw) as (query, params, constructor):
            res = await super().fetchall(query, *params, **opts)
            return constructor(res)

    async def fetchmany(self, size: int, query: Any, *params, raw: bool = False, **opts) -> Any:
        """Execute the given SQL and fetch many of the size."""
        with process(query, params, raw=raw) as (query, params, constructor):
            res = await super().fetchmany(size, query, *params, **opts)
            return constructor(res)

    async def fetchone(self, query: Any, *params, raw: bool = False, **opts) -> Any:
        """Execute the given SQL and fetch one."""
        with process(query, params, raw=raw) as (query, params, constructor):
            res = await super().fetchone(query, *params, **opts)
            return constructor(res)

    async def iterate(self, query: Any, *params, raw: bool = False, **opts) -> AsyncIterator:
        """Execute the given SQL and iterate through results."""
        with process(query, params, raw=raw) as (query, params, constructor):
            async for res in super().iterate(query, *params, **opts):
                yield constructor(res)

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

    @overload
    def run(self, query: Union[Select, ModelRaw]) -> RunWrapper:
        ...

    @overload
    def run(self, query: Query) -> Coroutine[Any, None, Any]:  # type: ignore[misc]
        ...

    def run(self, query) -> Union[Coroutine[Any, None, Any], RunWrapper]:
        """Run the given Peewee ORM Query."""
        if isinstance(query, (Select, ModelRaw)) or getattr(query, "_returning", None):
            return RunWrapper(self, query)

        return self.execute(query)

    async def count(self, query: Select, *, clear_limit: bool = False) -> Any:
        """Execute the given Peewee ORM Query and get a count of rows."""
        query = query.order_by()  # type: ignore[]
        if clear_limit:
            query._limit = query._offset = None  # type: ignore[]

        try:
            if (
                query._having is None  # type: ignore[]
                and query._group_by is None  # type: ignore[]
                and query._windows is None  # type: ignore[]
                and query._distinct is None  # type: ignore[]
                and query._simple_distinct is not True  # type: ignore[]
            ):
                query = query.select(SQL("1"))
        except AttributeError:
            pass

        query = Select([query], [fn.COUNT(SQL("1"))])
        query._database = self.pw_database  # type: ignore[]
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

    async def create_tables(self, *models_cls: Type[PWModel], safe=True, **opts):
        """Create tables for the given models or all registered with the manager."""
        models_cls = models_cls or tuple(self.models)
        for model_cls in sort_models(models_cls):
            schema: SchemaManager = model_cls._schema

            # Create sequences
            if schema.database.sequences:
                for field in model_cls._meta.sorted_fields:
                    if field.sequence:
                        ctx = schema._create_sequence(field)  # type: ignore[]
                        if ctx:
                            await self.execute(ctx)

            # Create table
            ctx = schema._create_table(safe=safe, **opts)  # type: ignore[]
            await self.execute(ctx)

            # Create indexes
            for query in schema._create_indexes(safe=safe):  # type: ignore[]
                try:
                    await self.execute(query)
                except OperationalError:
                    if not safe:
                        raise

    async def drop_tables(self, *models_cls: Type[PWModel], **opts):
        """Drop tables for the given models or all registered with the manager."""
        models_cls = models_cls or tuple(self.models)
        for model_cls in reversed(sort_models(models_cls)):
            schema: SchemaManager = model_cls._schema
            ctx = schema._drop_table(**opts)  # type: ignore[]
            await self.execute(ctx)

    async def get_or_none(
        self,
        model_cls: Type[TVModel],
        *args: Node,
        **kwargs,
    ) -> Optional[TVModel]:
        query: ModelSelect = model_cls.select()
        if kwargs:
            query = query.filter(**kwargs)

        if args:
            query = query.where(*args)  # type: ignore[]

        return await self.fetchone(query)

    async def get(
        self,
        model_cls: Type[TVModel],
        *args: Node,
        **kwargs,
    ) -> TVModel:
        res = await self.get_or_none(model_cls, *args, **kwargs)
        if res is None:
            raise model_cls.DoesNotExist  # type: ignore[]
        return res

    async def get_by_id(self, model_cls: Type[TVModel], pk) -> TVModel:
        return await self.get(model_cls, model_cls._meta.primary_key == pk)  # type: ignore[]

    async def set_by_id(self, model_cls: Type[PWModel], key, value) -> Any:
        qs = (
            model_cls.insert(value)
            if key is None
            else model_cls.update(value).where(model_cls._meta.primary_key == key)  # type: ignore[]
        )
        return await self.execute(qs)

    async def delete_by_id(self, model_cls: Type[PWModel], pk):
        return await self.execute(
            model_cls.delete().where(model_cls._meta.primary_key == pk),  # type: ignore[]
        )

    async def get_or_create(
        self,
        model_cls: Type[TVModel],
        defaults: Optional[Dict] = None,
        **kwargs,
    ) -> Tuple[TVModel, bool]:
        async with self.transaction():
            try:
                return (await self.get(model_cls, **kwargs), False)
            except model_cls.DoesNotExist:  # type: ignore[]
                return (
                    await self.create(model_cls, **dict(defaults or {}, **kwargs)),
                    True,
                )

    async def create(self, model_cls: Type[TVModel], **values) -> TVModel:
        inst = model_cls(**values)
        return await self.save(inst, force_insert=True)

    # Instance methods
    # ----------------

    async def save(  # noqa: C901
        self,
        inst: TVModel,
        *,
        force_insert: bool = False,
        only: Optional[Sequence] = None,
        on_conflict_ignore: bool = False,
    ) -> TVModel:
        field_dict = inst.__data__.copy()
        pk_field = pk_value = None
        meta = inst._meta  # type: ignore[]
        if meta.primary_key is not False:
            pk_field = meta.primary_key
            pk_value = inst._pk  # type: ignore[]

        if only is not None:
            field_dict = inst._prune_fields(field_dict, only)  # type: ignore[]

        elif meta.only_save_dirty and not force_insert:
            field_dict = inst._prune_fields(field_dict, inst.dirty_fields)  # type: ignore[]
            if not field_dict:
                inst._dirty.clear()  # type: ignore[]
                return inst

        inst._populate_unsaved_relations(field_dict)  # type: ignore[]
        if meta.auto_increment and pk_field and pk_value is None:
            field_dict.pop(pk_field.name, None)

        if pk_field is None:
            await self.execute(
                inst.insert(**field_dict).on_confict_ignore(on_conflict_ignore),
            )

        # Update
        elif pk_value is not None and not force_insert:
            if meta.composite_key:
                for pk_part_name in pk_field.field_names:
                    field_dict.pop(pk_part_name, None)
            else:
                field_dict.pop(pk_field.name, None)
            if not field_dict:
                raise ValueError("no data to save!")

            await self.execute(inst.update(**field_dict).where(inst._pk_expr()))  # type: ignore[]

        # Insert
        else:
            query = inst.insert(**field_dict).on_conflict_ignore(on_conflict_ignore)
            if query._returning:
                pk = await self.fetchval(query)
            else:
                pk = await self.execute(query)

            if pk is not None and (meta.auto_increment or pk_value is None):
                inst._pk = pk  # type: ignore[]

        inst._dirty.clear()  # type: ignore[]
        return inst

    async def delete_instance(
        self,
        inst: PWModel,
        *,
        recursive: bool = False,
        delete_nullable: bool = False,
    ):
        if recursive:
            for query, fk in reversed(list(inst.dependencies(delete_nullable))):
                if fk.null and not delete_nullable:
                    await self.execute(fk.model.update(**{fk.name: None}).where(query))

                else:
                    await self.execute(fk.model.delete().where(query))

        return await self.execute(inst.delete().where(inst._pk_expr()))  # type: ignore[]


def identity(r):
    return r


EXCEPTIONS["UniqueViolationError"] = IntegrityError
EXCEPTIONS["NotNullViolationError"] = InternalError
EXCEPTIONS["DuplicateTableError"] = OperationalError


@contextmanager
def process(query: Any, params: Sequence, *, raw: bool) -> Generator:
    constructor = identity

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
        self.description = [[k] for k in res.keys()]  # noqa: SIM118


class Constructor:
    """Process results."""

    __slots__ = "query", "processor"

    def __init__(self, query: BaseQuery):
        self.query = query
        self.processor: Optional[Callable] = None

    def __call__(
        self,
        res: Union[Mapping, Sequence[Mapping]],
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
            wrapper = self.query._get_cursor_wrapper(cursor)  # type: ignore[]
            wrapper.initialize()
            self.processor = wrapper.process_row

        return self.processor
