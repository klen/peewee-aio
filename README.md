# Peewee-AIO

Async support for [Peewee ORM](https://github.com/coleifer/peewee)

[![Tests Status](https://github.com/klen/peewee-aio/workflows/tests/badge.svg)](https://github.com/klen/peewee-aio/actions)
[![PYPI Version](https://img.shields.io/pypi/v/peewee-aio)](https://pypi.org/project/peewee-aio/)
[![Python Versions](https://img.shields.io/pypi/pyversions/peewee-aio)](https://pypi.org/project/peewee-aio/)

## Features

* Make [Peewee ORM](https://github.com/coleifer/peewee) to work async
* Supports PostgresQL, MySQL, SQLite
* Supports [asyncio](https://docs.python.org/3/library/asyncio.html) and
  [trio](https://github.com/python-trio/trio)
* Contains types as well
* Drivers supported:
    - [aiosqlite](https://github.com/omnilib/aiosqlite)
    - [aiomysql](https://github.com/aio-libs/aiomysql)
    - [aiopg](https://github.com/aio-libs/aiopg)
    - [asyncpg](https://github.com/MagicStack/asyncpg)
    - [triopg](https://github.com/python-trio/triopg)
    - [trio_mysql](https://github.com/python-trio/trio-mysql)


## Requirements

* python >= 3.8

## Installation

**peewee-aio** should be installed using pip:

```shell
$ pip install peewee-aio
```

You can install optional database drivers with:

```shell
$ pip install peewee-aio[aiosqlite]
$ pip install peewee-aio[aiomysql]
$ pip install peewee-aio[aiopg]
$ pip install peewee-aio[asyncpg]
$ pip install peewee-aio[trio_mysql]
$ pip install peewee-aio[triopg]
```

### Quickstart

```python
    import peewee
    from peewee_aio import Manager, AIOModel, fields

    manager = Manager('aiosqlite:///:memory:')

    @manager.register
    class Role(AIOModel):
        # Pay attention that we are using fields from Peewee-AIO for better typing support
        id = fields.AutoField()
        name = fields.CharField()

    @manager.register
    class User(AIOModel):

        # Pay attention that we are using fields from Peewee-AIO for better typing support
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
                role = await Role.create(name='user')
                assert role
                assert role.id  # role.id contains correct string type
                user = await User.create(name="Andrey", role=role)
                assert user
                assert user.id
                role = await user.role  # Load role from DB using the foreign key
                assert role  # role has a correct Role Type

                # Iterate through records
                async for user in User.select(User, Role).join(Role):
                    assert user  # user has a corrent User Type
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

TODO

### Sync usage

The library still supports sync mode (use `manager.allow_sync`):

```python

class Test(peewee.Model):
  data = peewee.CharField()

with manager.allow_sync():
  Test.create_table()
  Test.create(data='test')
  assert Test.select().count()
  Test.update(data='new-test').execute()

```


### Get prefetched relations

TODO

```python
# We prefetched roles here
async for user in User.select(User, Role).join(Role):
  role = user.fetch(User.role)  # get role from user relations cache

```

## Bug tracker

If you have any suggestions, bug reports or annoyances please report them to
the issue tracker at https://github.com/klen/peewee-aio/issues


## Contributing

Development of the project happens at: https://github.com/klen/peewee-aio


## License

Licensed under a [MIT License](http://opensource.org/licenses/MIT)
