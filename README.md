# Peewee-AIO

Async support for [Peewee ORM](https://github.com/coleifer/peewee)

## Features

* Make [Peewee ORM](https://github.com/coleifer/peewee) to work async
* Supports PostgresQL, MySQL, SQLite

## Requirements

* python >= 3.7

## Installation

**peewee-orm** should be installed using pip:

```shell
$ pip install peewee-orm
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

    @manager.register
    class TestModel(peewee.Model):
        text = peewee.CharField()

    async def handler():

        # Initialize the database
        async with manager:

            # Create the table in database
            await manager.create_tables(TestModel, safe=True)

            # Create a record
            test = await manager.create(TestModel, text="I'm working!")
            assert test
            assert test.id

            # Iterate through records
            async for test in manager.run(TestModel.select()):
                assert test
                assert test.id

            # Drop the table in database
            await manager.drop_tables(TestModel, safe=True)

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
