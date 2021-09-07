# Peewee-AIO

Async support for [Peewee ORM](https://github.com/coleifer/peewee)

[![Tests Status](https://github.com/klen/peewee-aio/workflows/tests/badge.svg)](https://github.com/klen/peewee-aio/actions)
[![PYPI Version](https://img.shields.io/pypi/v/peewee-aio)](https://pypi.org/project/peewee-aio/)
[![Python Versions](https://img.shields.io/pypi/pyversions/peewee-aio)](https://pypi.org/project/peewee-aio/)

## Features

* Make [Peewee ORM](https://github.com/coleifer/peewee) to work async
* Supports PostgresQL, MySQL, SQLite

## Requirements

* python >= 3.7

## Installation

**peewee-aio** should be installed using pip:

```shell
$ pip install peewee-aio
```

You can install optional database drivers with:

```shell
$ pip install peewee-aio[sqlite]
$ pip install peewee-aio[postgresql]
$ pip install peewee-aio[mysql]
```

### Quickstart

```python
    import peewee
    from peewee_aio import Manager

    manager = Manager('sqlite:///:memory:')

    class TestModel(manager.Model):
        text = peewee.CharField()

    async def handler():

        # Initialize the database
        async with manager:

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
            test.text = "I'm changed'
            await test.save()

            # Update records
            await TestModel.update({'text': "I'm updated'"}).where(TestModel.id == test.id)

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
