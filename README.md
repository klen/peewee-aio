# Peewee-AIO

Async support for [Peewee ORM](https://github.com/coleifer/peewee): keep your
peewee models and queries and run them from asyncio or trio.

[![Tests Status](https://github.com/klen/peewee-aio/workflows/tests/badge.svg)](https://github.com/klen/peewee-aio/actions)
[![PYPI Version](https://img.shields.io/pypi/v/peewee-aio)](https://pypi.org/project/peewee-aio/)
[![Python Versions](https://img.shields.io/pypi/pyversions/peewee-aio)](https://pypi.org/project/peewee-aio/)

## How it works

Peewee builds SQL synchronously and runs it through a DB-API connection.
Peewee-AIO keeps the models, fields and query builder, replaces the connection
layer with [aio-databases](https://github.com/klen/aio-databases), and sends
the generated SQL through an async driver.

This has two visible consequences. Queries are awaitable, so `await
User.select()` runs the query and returns the rows. Foreign keys are awaitable
too, so `await user.role` loads the related row when it is not already cached.

Peewee's synchronous methods are still there. They raise until you enable them
with `manager.allow_sync()`.

## Features

- Peewee models, fields and query builder executed through async drivers
- PostgreSQL, MySQL and SQLite
- asyncio and trio
- Typed fields and query API
- Async relations, prefetching and transactions
- Drivers supported:
  - [aiosqlite](https://github.com/omnilib/aiosqlite)
  - [aiomysql](https://github.com/aio-libs/aiomysql)
  - [aiopg](https://github.com/aio-libs/aiopg)
  - [asyncpg](https://github.com/MagicStack/asyncpg)
  - [trio_mysql](https://github.com/python-trio/trio-mysql)

## Requirements

- Python >= 3.10

## Installation

**peewee-aio** should be installed using pip:

```shell
pip install peewee-aio
```

You can install optional database drivers with:

```shell
pip install peewee-aio[aiosqlite]   # for SQLite (asyncio)
pip install peewee-aio[aiomysql]    # for MySQL (asyncio)
pip install peewee-aio[aiopg]       # for PostgreSQL (asyncio)
pip install peewee-aio[asyncpg]     # for PostgreSQL (asyncio)
pip install peewee-aio[trio_mysql]  # for MySQL (trio)
```

### Quickstart

```python
from peewee_aio import Manager, AIOModel, fields

manager = Manager("aiosqlite:///:memory:")


@manager.register
class Role(AIOModel):
    # Peewee-AIO fields carry type hints, see "Fields" below
    id = fields.AutoField()
    name = fields.CharField()


@manager.register
class User(AIOModel):
    id = fields.AutoField()
    name = fields.CharField()
    role = fields.ForeignKeyField(Role)


async def handler():

    # Initialize the database's pool (optional)
    async with manager:
        # Acquire a connection
        async with manager.connection():
            # Create the tables in database
            await Role.create_table()
            await User.create_table()

            # Create a record
            role = await Role.create(name="user")
            assert role
            assert role.id  # role.id is typed as int
            user = await User.create(name="Andrey", role=role)
            assert user
            assert user.id
            role = await user.role  # Load role from DB using the foreign key
            assert role  # role has a correct Role type

            # Iterate through records
            async for user in User.select(User, Role).join(Role):
                assert user  # user has a correct User type
                assert user.id
                role = await user.role  # No DB query here, because the fk is preloaded

            # Change records
            user.name = "Dmitry"
            await user.save()

            # Update records
            await User.update({"name": "Anonimous"}).where(User.id == user.id)

            # Delete records
            await User.delete().where(User.id == user.id)

            # Drop the tables in database
            await User.drop_table()
            await Role.drop_table()


# Run the handler with your async library
import asyncio

asyncio.run(handler())
```

`manager.connection()` pins one connection to the current context. It is
required for `:memory:` SQLite, where every connection gets its own database.
For file-backed SQLite and server databases you can omit it; each query then
opens or borrows a connection and releases it when the query finishes.
`manager.transaction()` pins a connection on its own, so a surrounding
`manager.connection()` is not required for transactions.

## Usage

### Supported drivers

- `aiosqlite`
- `aiomysql`, `aiomysql+pool`
- `aiopg`, `aiopg+pool`
- `asyncpg`, `asyncpg+pool`
- `trio-mysql`

The scheme picks the driver; everything after `://` is a regular database URL.
The `+pool` variants keep a pool of connections. The plain variants open a
connection per operation.

### Connecting

```python
from peewee_aio import Manager


manager = Manager("asyncpg://user:password@localhost/mydb")


async def main():
    async with manager:  # create the connection pool
        async with manager.connection():  # keep one connection for this block
            await manager.fetchval("SELECT 1")
```

Keyword arguments are forwarded to the driver or pool, so driver options such
as pool sizes and timeouts can be passed to `Manager` directly.

The manager closes its connections when the `async with manager` block exits,
or with `await manager.disconnect()`.

Read replicas are passed at construction:

```python
manager = Manager(url, replicas=["asyncpg://user:password@replica/mydb"])

async with manager:
    async with manager.replica():
        users = await User.select()
```

`manager.replica()` picks a replica connection and rejects writes.
`manager.connection(create=False)` reuses the connection already pinned to the
current context; the default `create=True` pins a new one for the block.

### Models

```python
from peewee_aio import AIOModel, fields


@manager.register
class Role(AIOModel):
    id = fields.AutoField()
    name = fields.CharField()


@manager.register
class User(AIOModel):
    id = fields.AutoField()
    name = fields.CharField()
    email = fields.CharField[str | None](null=True)
    role = fields.ForeignKeyField(Role, null=True)
```

`register()` sets `Model._manager` and the peewee database on the model, and
adds it to the registry used by `manager.create_tables()` and
`manager.drop_tables()`. Pass models explicitly if you don't want to register
them:

```python
await manager.create_tables(User, Role)
await manager.create_tables()  # every registered model
```

`create_table()` defaults to `safe=True`, which uses `IF NOT EXISTS`.

Fields from `peewee_aio.fields` accept a type argument and return it from the
descriptor, so `user.name` is typed as `str`. Plain peewee fields work too, but
carry no type hints. `class Base(manager.Model)` gives you a base class already
bound to the manager; models derived from it are not added to the registry
automatically.

Use `fields.DeferredForeignKey` for forward references:

```python
class Node(AIOModel):
    name = fields.CharField()
    parent = fields.DeferredForeignKey("Node", null=True)
```

The reference resolves when the other model class is created. For a
self-reference use `fields.ForeignKeyField("self")`:

```python
class Node(AIOModel):
    name = fields.CharField()
    parent = fields.ForeignKeyField("self", null=True)
```

`fields.ForeignKeyField` is an alias for `fields.AIOForeignKeyField`.

### CRUD

```python
role = await Role.create(name="admin")
user = await User.create(name="Andrey", role=role)

user.name = "Dmitry"
await user.save()
await user.save(only=[User.name])  # save just the given fields

user = await User.get(User.name == "Dmitry")  # raises User.DoesNotExist
user = await User.get_by_id(1)
user = await User.get_or_none(User.name == "nobody")
user, created = await User.get_or_create(name="Dmitry", defaults={"role": role})

await User.set_by_id(1, {"name": "Andrew"})
await User.delete_by_id(1)
await user.delete_instance()

await User.bulk_create([User(name="a"), User(name="b")], batch_size=100)
users = await User.select()
await User.bulk_update(users, fields=[User.name], batch_size=100)
```

The class methods are thin wrappers over `Manager`, and the manager works with
plain peewee models too:

```python
user = await manager.create(User, name="Andrey")
user = await manager.get(User, User.name == "Andrey")
user = await manager.get_or_none(User, User.name == "nobody")
```

Insert queries can be waited on directly:

```python
await User.insert(name="Andrey")
await User.insert_many([{"name": "a"}, {"name": "b"}])

# Copy names from one query into the table
await User.insert_from(User.select(User.name), [User.name])

# Skip rows that violate a unique constraint
await User.insert(name="Andrey").on_conflict_ignore()
```

A single-row insert returns the last inserted id when the driver reports one
(SQLite and MySQL do; PostgreSQL does not) and `None` otherwise. A multi-row
insert returns the affected row count. `returning()` returns model instances
on backends that support `RETURNING`:

```python
[user] = await User.insert(name="Andrey").returning(User)
```

`bulk_update()` does not support models with a composite primary key.

### Queries

```python
users = await User.select()  # list of models
async for user in User.select().where(User.name == "Dmitry"):
    assert user.id

users = await User.select().order_by(User.id).limit(10).offset(20)
users = await User.select()[20:30]
user = await User.select()[0]
user = await User.select().first()
users = await User.select().first(10)
count = await User.select().count()
count = await User.select().limit(10).count(clear_limit=True)
exists = await User.select().where(User.name == "Dmitry").exists()
names = await User.select(User.name).scalars()
rows = await User.select(User.name).dicts()
users = await User.select(User, Role).join(Role)
```

Awaiting a query executes it and returns all rows. `first()`, `peek()`,
`count()`, `exists()` and `scalar()` execute directly and return a single
value; `async for` streams rows without loading them all.

`first(n)` and `peek(n)` return a list of up to `n` rows. `scalar()` returns
the first column of the first row; `scalar(as_tuple=True)` and
`scalar(as_dict=True)` return the whole row:

```python
name = await User.select(User.name).scalar()
row = await User.select(User.name).scalar(as_tuple=True)
row = await User.select(User.name).scalar(as_dict=True)
names = await User.select(User.name).scalars()
```

`dicts()`, `tuples()` and `namedtuples()` change the row shape:

```python
rows = await User.select(User.name).dicts()
rows = await User.select(User.name).tuples()
rows = await User.select(User.name).namedtuples()
```

Queries compose with the usual peewee operators: `|` is `UNION`, `&` is
`INTERSECT`, `-` is `EXCEPT` and `+` is `UNION ALL`:

```python
users = await (User.select().where(User.name == "a") | User.select().where(User.name == "b"))
common = await (active_users & admin_users)
others = await (all_users - admin_users)
```

Slices support only non-negative indexes and a step of 1. `User.select()[-1]`
and `User.select()[::2]` raise `IndexError`; use
`order_by(User.id.desc()).first()` for the last row.

### Relations

```python
role = await user.role  # queried on first access, cached on the instance
```

If the foreign key is already present as a model instance (for example after
`User.create(..., role=role)` or a join), the accessor returns it without a
query. A nullable foreign key that is `NULL` returns `None`; otherwise a
missing related row raises `Role.DoesNotExist`.

`fetch()` reads only joined or prefetched relations and raises `ValueError`
otherwise. Pass `silent=True` to get `None` instead:

```python
role = user.fetch(User.role, silent=True)  # None when not loaded
```

If a model must never query a relation on its own, use
`fields.FetchForeignKeyField`: it reads only prefetched data and raises
`RuntimeError` otherwise.

```python
class Comment(AIOModel):
    user = fields.FetchForeignKeyField(User)
    body = fields.CharField()
```

Backrefs are async query objects too:

```python
comments = await user.comment_set
```

### Prefetching

A lazy relation costs one query per instance. Prefetch the whole result set in
one additional query per relation instead:

```python
users = await User.select(User).prefetch(Role)
for user in users:
    role = user.fetch(User.role)  # from the prefetch cache
```

`manager.prefetch()` does the same and accepts prefetch options:

```python
users = await manager.prefetch(User.select(), Role)
```

The subquery can be a model class or a select query. A filtered select
prefetches only the matching rows:

```python
users = await User.select().prefetch(Role.select().where(Role.name == "admin"))
```

Prefetch works for forward foreign keys and backrefs. A prefetched backref is
a list on the instance instead of an async query object:

```python
users = await User.select().prefetch(Comment)
for user in users:
    comments = user.comment_set  # list, already loaded
```

Pass several subqueries to walk a chain. They are matched in order: `Reaction`
is prefetched for `Comment`, then `Comment` for `User`.

```python
class Reaction(AIOModel):
    comment = fields.ForeignKeyField(Comment)


users = await User.select().prefetch(Comment, Reaction)
for user in users:
    for comment in user.comment_set:
        reactions = comment.reaction_set  # list, already loaded
```

Prefetch runs the base query plus one query per subquery, independent of the
number of rows. The nested example runs 3 queries: users, comments and
reactions.

The default strategy is `PREFETCH_TYPE.WHERE`, which fetches each relation with
an `IN` filter. `manager.prefetch()` also accepts `PREFETCH_TYPE.JOIN`:

```python
import peewee

users = await manager.prefetch(
    User.select(),
    Comment,
    prefetch_type=peewee.PREFETCH_TYPE.JOIN,
)
```

`ModelSelect.prefetch()` accepts subqueries only. Use `manager.prefetch()` when
you need to pass `prefetch_type`.

Calling `prefetch()` without subqueries simply executes the query:

```python
users = await User.select().prefetch()  # same as await User.select()
```

A filtered prefetch attaches only matching rows. For a forward foreign key
whose row was filtered out, the relation stays unloaded; with
`FetchForeignKeyField` this raises `RuntimeError`.

Prefetch caches relations on the instances, not globally. When a relation was
prefetched, `fetch()` and `await instance.fk` read the cache instead of
querying. Relations excluded by a filtered prefetch are not cached; a normal
foreign key will query lazily, while `FetchForeignKeyField` raises
`RuntimeError`. This is also the intended way to load `FetchForeignKeyField`
relations.

### Transactions

```python
async with manager.transaction():
    await User.create(name="Dmitry")  # committed on exit

async with manager.transaction() as trans:
    await User.create(name="Dmitry")
    await trans.rollback()
```

Any exception inside the block rolls the transaction back. The transaction
pins a connection for its duration; further queries in the block use it.

### Raw SQL

```python
users = await User.raw("SELECT * FROM user WHERE name = ?", "Dmitry")
rows = await manager.fetchall("SELECT name FROM user")
row = await manager.fetchone("SELECT name FROM user WHERE id = ?", 1)
rows = await manager.fetchmany(10, "SELECT name FROM user")
async for row in manager.iterate("SELECT name FROM user"):
    ...
name = await manager.fetchval("SELECT name FROM user WHERE id = ?", 1)
await manager.execute("UPDATE user SET name = ? WHERE id = ?", "Andrew", 1)
```

`Model.raw()` returns model instances. For raw SQL, `manager.fetchall()`,
`fetchone()` and `fetchmany()` return driver rows, and `manager.iterate()`
streams them without loading them all. `manager.fetchval()` returns the first
column of the first row.

`manager.execute()` returns the last inserted id for a single-row insert and
the affected row count otherwise.

You can also pass a peewee query to the manager fetch methods. By default they
run it through the model row processor and return model instances; pass
`raw=True` to get driver rows:

```python
users = await manager.fetchall(User.select())
rows = await manager.fetchall(User.select(), raw=True)
```

Placeholders are driver-specific: `?` for SQLite, `%s` for PostgreSQL and
MySQL. `manager.pw_database.param` holds the right one for the configured
backend.

### Sync usage

The library still supports sync mode (use `manager.allow_sync`):

```python
import peewee


class Test(peewee.Model):
    data = peewee.CharField()


manager.register(Test)

with manager.allow_sync():
    Test.create_table()
    Test.create(data="test")
    assert Test.select().count()
    Test.update(data="new-test").execute()
```

Sync mode switches the peewee database into synchronous execution and closes
it when the block exits. Use it for sync code paths, not for concurrent
queries.

### Late initialization

`Manager` needs the database URL in `__init__`, but models don't need a manager
when they are declared. Declare them first, then create the manager and
register the models (the URL can come from config or env at any point):

```python
from peewee_aio import AIOModel, Manager, fields


class Base(AIOModel):
    pass


class Role(Base):
    name = fields.CharField()


class User(Base):
    name = fields.CharField()
    role = fields.ForeignKeyField(Role, null=True)


# Later, when the URL is known
manager = Manager(db_url)

for model in (Role, User):
    manager.register(model)
```

`register()` sets both `Model._manager` and `Model._meta.database`, so neither
a `peewee.DatabaseProxy` nor a manager subclass is needed. Setting
`Model._manager = manager` alone is not enough.

### Fields

All peewee field types have a typed counterpart in `peewee_aio.fields`:

- numbers: `IntegerField`, `BigIntegerField`, `SmallIntegerField`, `AutoField`,
  `BigAutoField`, `IdentityField`, `FloatField`, `DoubleField`, `DecimalField`
- text and bytes: `CharField`, `FixedCharField`, `TextField`, `BlobField`,
  `BitField`, `BigBitField`
- dates and time: `DateTimeField`, `DateField`, `TimeField`, `TimestampField`
- misc: `BooleanField`, `UUIDField`, `BinaryUUIDField`, `IPField`
- relations: `ForeignKeyField` (awaitable), `FetchForeignKeyField`
  (prefetch-only), `DeferredForeignKey`

A type argument gives the descriptor a precise type; with `null=True` it
includes `None`:

```python
class User(AIOModel):
    name = fields.CharField[str]()
    email = fields.CharField[str | None](null=True)
    age = fields.IntegerField[int]()
```

The type argument is for the type checker only. `fields.CharField[str]` is a
plain `CharField` at runtime, and `null=True` adds `None` to the descriptor
type without validating values.

## Things to know

- `await model` returns the model itself. It exists so peewee code that awaits
  instances keeps working; it does not reload the row.
- `insert_many([])` raises `DefaultValuesException`.
- `:memory:` SQLite is per connection. Keep a pinned connection
  (`manager.connection()`) for the lifetime of the manager.
- `allow_sync()` is for synchronous code paths only.

## Bug tracker

If you have any suggestions, bug reports or annoyances please report them to
the issue tracker at <https://github.com/klen/peewee-aio/issues>

## Contributing

Development of the project happens at: <https://github.com/klen/peewee-aio>

## License

Licensed under a [MIT License](http://opensource.org/licenses/MIT)
