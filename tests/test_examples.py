import peewee


def test_readme():
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

    import asyncio
    asyncio.run(handler())
