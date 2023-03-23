from __future__ import annotations


def test_readme():
    from peewee_aio import AIOModel, Manager, fields

    manager = Manager("aiosqlite:///:memory:")

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
                role = await Role.create(name="user")
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

    import asyncio

    asyncio.run(handler())
