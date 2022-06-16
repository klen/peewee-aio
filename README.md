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
* Drivers supported:
    - [aiosqlite](https://github.com/omnilib/aiosqlite)
    - [aiomysql](https://github.com/aio-libs/aiomysql)
    - [aiopg](https://github.com/aio-libs/aiopg)
    - [asyncpg](https://github.com/MagicStack/asyncpg)
    - [triopg](https://github.com/python-trio/triopg)
    - [trio_mysql](https://github.com/python-trio/trio-mysql)


## Requirements

* python >= 3.7

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
    from peewee_aio import Manager

    manager = Manager('aiosqlite:///:memory:')

    class TestModel(manager.Model):
        text = peewee.CharField()

    async def handler():

        # Initialize the database's pool (optional)
        async with manager:

            # Acquire a connection
            async with manager.connection():

                # Create the table in database
                await TestModel.create_table()

                # Create a record
                test = await TestModel.create(text="I'm working!")
                assert test
                assert test.id

                # Iterate through records
                async for test in TestModel.select():
                    assert test
                    assert test.id

                # Change records
                test.text = "I'm changed"
                await test.save()

                # Update records
                await TestModel.update({'text': "I'm updated!"}).where(TestModel.id == test.id)

                # Delete records
                await TestModel.delete().where(TestModel.id == test.id)

                # Drop the table in database
                await TestModel.drop_table()

    # Run the handler with your async library
    import asyncio

    asyncio.run(handler())
```

## Usage

TODO

## Bug tracker

If you have any suggestions, bug reports or annoyances please report them to
the issue tracker at https://github.com/klen/peewee-aio/issues


## Contributing

Development of the project happens at: https://github.com/klen/peewee-aio


## License

Licensed under a [MIT License](http://opensource.org/licenses/MIT)
