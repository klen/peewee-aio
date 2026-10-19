from __future__ import annotations

import asyncio

import pytest

from peewee_aio import AIOModel, Manager, fields


def test_readme():

    manager = Manager("aiosqlite:///:memory:")

    @manager.register
    class Role(AIOModel):
        id = fields.AutoField()
        name = fields.CharField()

    @manager.register
    class User(AIOModel):
        id = fields.AutoField()
        name = fields.CharField()
        role = fields.ForeignKeyField(Role)

    async def handler():
        # Initialize the database's pool (optional)
        async with manager, manager.connection():
            # Create the tables in database
            await Role.create_table()
            await User.create_table()

            # Create a record
            role = await Role.create(name="user")
            assert role
            assert role.id
            user = await User.create(name="Andrey", role=role)
            assert user
            assert user.id
            role = await user.role
            assert role

            # Iterate through records
            async for user in User.select(User, Role).join(Role):
                assert user
                assert user.id
                role = await user.role

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

    asyncio.run(handler())


def test_usage():  # noqa: PLR0915

    manager = Manager("aiosqlite:///:memory:")

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

    @manager.register
    class Comment(AIOModel):
        user = fields.FetchForeignKeyField(User)
        body = fields.CharField()

    async def handler():  # noqa: PLR0915
        async with manager, manager.connection():
            await manager.create_tables()

            role = await Role.create(name="admin")
            user = await User.create(name="Andrey", role=role)

            user.name = "Dmitry"
            await user.save()
            await user.save(only=[User.name])

            assert await User.get(User.name == "Dmitry")
            assert await User.get_by_id(user.id)
            assert await User.get_or_none(User.name == "nobody") is None
            found, created = await User.get_or_create(name="Dmitry")
            assert found.id == user.id
            assert not created

            await User.set_by_id(user.id, {"name": "Andrew"})
            assert (await User.get_by_id(user.id)).name == "Andrew"
            await User.delete_by_id(user.id)
            assert await User.get_or_none(User.id == user.id) is None

            user = await User.create(name="Misha", role=role)
            assert (await user.role).name == "admin"
            await user.delete_instance()

            await User.bulk_create([User(name="a"), User(name="b")])
            users = await User.select()
            assert await User.bulk_update(users, fields=[User.name]) == len(users)

            # Queries
            users = await User.select()
            assert len(users) == 2
            async for u in User.select().where(User.name == "a"):
                assert u.id

            assert await User.select().order_by(User.id).limit(10).offset(20) == []
            assert await User.select()[0:2] == users
            assert (await User.select()[0]).id
            assert await User.select().first()
            assert await User.select().count() == 2
            assert await User.select().limit(1).count(clear_limit=True) == 2
            assert await User.select().where(User.name == "a").exists()
            assert await User.select(User.name).scalars() == ["a", "b"]
            rows = await User.select(User.name).dicts()
            assert rows[0]["name"] == "a"

            # Relations
            user = await User.create(name="Kate", role=role)
            assert (await user.role).name == "admin"
            assert await User.select(User, Role).join(Role).where(User.name == "Kate")

            users = await User.select(User).prefetch(Role)
            for user in users:
                user.fetch(User.role)

            comment = await Comment.create(user_id=user.id, body="hi")
            with pytest.raises(RuntimeError):
                _ = comment.user
            comments = await Comment.select().prefetch(User)
            assert comments[0].user

            # Transactions
            async with manager.transaction():
                await User.create(name="committed")
            assert await User.get_or_none(User.name == "committed")

            async with manager.transaction() as trans:
                await User.create(name="rolled back")
                await trans.rollback()
            assert await User.get_or_none(User.name == "rolled back") is None

            # Raw SQL
            assert await User.raw("SELECT * FROM user WHERE name = ?", "Kate")
            assert await manager.fetchall("SELECT name FROM user")
            assert await manager.fetchval("SELECT count(*) FROM user") == 4
            await manager.execute("UPDATE user SET name = ? WHERE id = ?", "Ann", user.id)
            assert (await User.get_by_id(user.id)).name == "Ann"

            await manager.drop_tables()

    asyncio.run(handler())
