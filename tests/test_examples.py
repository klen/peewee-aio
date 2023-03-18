from __future__ import annotations

import peewee


def test_readme():
    from peewee_aio import AIOModel, Manager

    manager = Manager("sqlite:///:memory:")

    @manager.register
    class TestModel(AIOModel):
        text = peewee.CharField()

    async def handler():
        # Initialize the database (pool)
        async with manager:
            # Get a connection
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
                await TestModel.update({"text": "I'm updated'"}).where(
                    TestModel.id == test.id,
                )

                # Delete records
                await TestModel.delete().where(TestModel.id == test.id)

                # Drop the table in database
                await TestModel.drop_table()

    import asyncio

    asyncio.run(handler())
