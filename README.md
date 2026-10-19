# Peewee-AIO

Async support for [Peewee ORM](https://github.com/coleifer/peewee): use your
peewee models and queries from asyncio or trio.

[![Tests Status](https://github.com/klen/peewee-aio/workflows/tests/badge.svg)](https://github.com/klen/peewee-aio/actions)
[![PYPI Version](https://img.shields.io/pypi/v/peewee-aio)](https://pypi.org/project/peewee-aio/)
[![Python Versions](https://img.shields.io/pypi/pyversions/peewee-aio)](https://pypi.org/project/peewee-aio/)

## Features

- Peewee models and queries executed through async drivers
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

- python >= 3.10

## Installation

**peewee-aio** should be installed using pip:

```shell
pip install peewee-aio
```

You can install optional database drivers with:

```shell
pip install peewee-aio[aiosqlite]   # for SQLite (asyncio)
pip install peewee-aio[aiomysql]    # for MySQL (asyncio)
pip install peewee-aio[aiopg]       # for Postgresql (asyncio)
pip install peewee-aio[asyncpg]     # for Postgresql (asyncio)
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

## Usage

### Supported schemas

- `aiomysql`
- `aiomysql+pool`
- `aiopg`
- `aiopg+pool`
- `asyncpg`
- `asyncpg+pool`
- `aiosqlite`
- `trio-mysql`

The schema picks the driver, everything after `://` is a regular database URL.

### Connecting

```python
from peewee_aio import Manager


manager = Manager("asyncpg://user:password@localhost/mydb")


async def main():
    async with manager:  # create the connection pool
        async with manager.connection():  # keep one connection for this block
            await manager.fetchval("SELECT 1")
```

`manager.connection()` pins a connection to the current context. Transactions
and `:memory:` SQLite need it; without it every query borrows its own connection
from the pool. The pool is closed when the `async with manager` block exits (or
with `await manager.disconnect()`).

Read replicas are passed at construction:

```python
manager = Manager(url, replicas=["asyncpg://user:password@replica/mydb"])

async with manager:
    async with manager.replica():
        users = await User.select()
```

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
them: `await manager.create_tables(User)`.

Fields from `peewee_aio.fields` accept a type argument and return it from the
descriptor, so `user.name` is typed as `str`. Plain peewee fields work too, but
carry no type hints. `class Base(manager.Model)` gives you a base class already
bound to the manager; models derived from it are not added to the registry
automatically.

Use `fields.DeferredForeignKey` for forward references (including `"self"`):

```python
class Node(AIOModel):
    name = fields.CharField()
    parent = fields.DeferredForeignKey("Node", null=True)
```

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

await User.bulk_create([User(name="a"), User(name="b")])
users = await User.select()
await User.bulk_update(users, fields=[User.name])
```

### Queries

```python
users = await User.select()  # list of models
async for user in User.select().where(User.name == "Dmitry"):
    assert user.id

users = await User.select().order_by(User.id).limit(10).offset(20)
users = await User.select()[20:30]
user = await User.select()[0]
user = await User.select().first()
count = await User.select().count()
count = await User.select().limit(10).count(clear_limit=True)
exists = await User.select().where(User.name == "Dmitry").exists()
names = await User.select(User.name).scalars()
rows = await User.select(User.name).dicts()
users = await User.select(User, Role).join(Role)
```

Awaiting a query executes it and returns all rows. `first()`, `count()` and
`exists()` execute directly and return a single value; `async for` streams rows
without loading them all.

### Relations

```python
role = await user.role  # queried on first access, cached on the instance
```

To avoid one query per row, prefetch the relation:

```python
users = await User.select(User).prefetch(Role)
for user in users:
    role = user.fetch(User.role)  # no query, taken from the prefetch cache
```

`fetch()` raises `ValueError` when the relation was not prefetched. If a model
must never query a relation on its own, use `fields.FetchForeignKeyField`: it
reads only prefetched data and fails loudly otherwise.

```python
class Comment(AIOModel):
    user = fields.FetchForeignKeyField(User)
```

### Transactions

```python
async with manager.transaction():
    await User.create(name="Dmitry")  # committed on exit

async with manager.transaction() as trans:
    await User.create(name="Dmitry")
    await trans.rollback()
```

Any exception inside the block rolls the transaction back.

### Raw SQL

```python
users = await User.raw("SELECT * FROM user WHERE name = ?", "Dmitry")
rows = await manager.fetchall("SELECT name FROM user")
name = await manager.fetchval("SELECT name FROM user WHERE id = ?", 1)
await manager.execute("UPDATE user SET name = ? WHERE id = ?", "Andrew", 1)
```

`Model.raw()` returns model instances, `manager.fetchall()` returns driver rows,
`manager.fetchval()` returns the first column of the first row and
`manager.execute()` returns the driver result: the last inserted id for peewee
insert queries, the affected row count otherwise.

Placeholders are driver-specific: `?` for SQLite, `%s` for PostgreSQL and MySQL.
`manager.pw_database.param` holds the right one for the configured backend.

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

`register()` sets both `Model._manager` and `Model._meta.database`, so neither a
`peewee.DatabaseProxy` nor a manager subclass is needed. Setting
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

## Bug tracker

If you have any suggestions, bug reports or annoyances please report them to
the issue tracker at <https://github.com/klen/peewee-aio/issues>

## Contributing

Development of the project happens at: <https://github.com/klen/peewee-aio>

## License

Licensed under a [MIT License](http://opensource.org/licenses/MIT)
