from __future__ import annotations

import asyncio
from uuid import UUID

import pytest

from peewee_aio import AIOModel, fields
from tests.conftest import Role, User, UserToRole


async def test_insert(manager, transaction):
    res = await manager.run(User.select())
    assert not res

    await manager.run(User.insert(name="Mickey"))
    [user] = await manager.run(User.select())
    assert user
    assert user.id
    assert user.name == "Mickey"

    await manager.run(Role.insert(name="admin"))
    [role] = await manager.run(Role.select())
    assert role
    assert role.id
    assert role.name == "admin"

    await manager.run(UserToRole.insert(role=role, user=user))
    [user_to_role] = await manager.run(UserToRole.select())
    assert user_to_role


async def test_insert_many(manager, transaction):
    query = User.insert_many(
        [
            {"name": "Mickey"},
            {"name": "John"},
        ],
    )
    last_id = await manager.run(query)
    assert last_id is not None

    [user1, user2] = await manager.run(User.select().order_by(User.id))
    assert user1
    assert user2
    assert user1.name == "Mickey"
    assert user2.name == "John"


async def test_create(manager, transaction):
    user = await manager.create(User, name="Mickey")
    assert user
    assert user.id
    assert user.name == "Mickey"


async def test_create_uid(manager, transaction):
    role = await manager.create(Role, name="admin")
    assert role
    assert role.id
    assert UUID(str(role.id))


async def test_update(manager, transaction):
    await manager.create(User, name="Mickey")
    await manager.create(User, name="John")
    query = User.update(name="Timmy")
    upd = await manager.run(query)
    assert upd == 2
    user = await manager.get(User)
    assert user.name == "Timmy"


async def test_save(manager, transaction):
    res = await manager.run(User.select())
    assert not res

    user = User(name="Mickey")
    rows = await manager.save(user)
    assert rows
    assert user.id
    assert user.name == "Mickey"
    assert not user.dirty_fields

    user.name = "John"  # type: ignore[]
    assert user.dirty_fields
    rows = await manager.save(user)
    assert rows
    assert user.id
    assert user.name == "John"
    assert not user.dirty_fields

    user = await manager.get(User, id=user.id)
    assert user.name == "John"


async def test_delete(manager, transaction):
    source = await manager.create(User, name="Mickey")
    await manager.execute(User.delete())
    res = await manager.run(User.select())
    assert not res

    await manager.create(User, name="John")

    source = await manager.create(User, name="Mickey")
    await manager.delete_instance(source)
    res = await manager.get_or_none(User, User.id == source.id)
    assert res is None

    source = await manager.create(User, name="Mickey")
    await manager.delete_by_id(User, source.id)
    res = await manager.get_or_none(User, User.id == source.id)
    assert res is None

    assert await manager.run(User.select())


async def test_save_only_keeps_unsaved_fields_dirty(manager):
    @manager.register
    class DirtyUser(AIOModel):
        name = fields.CharField()
        num = fields.IntegerField(null=True)

        class Meta:
            only_save_dirty = True

    await DirtyUser.drop_table(safe=True)
    await DirtyUser.create_table()
    try:
        inst = await DirtyUser.create(name="a", num=1)
        inst.name = "b"
        inst.num = 2

        await inst.save(only=[DirtyUser.name])

        assert inst.is_dirty()
        row = await DirtyUser.get_by_id(inst.id)
        assert row.name == "b"
        assert row.num == 1

        await inst.save()

        row = await DirtyUser.get_by_id(inst.id)
        assert row.num == 2
    finally:
        await DirtyUser.drop_table(safe=True)


async def test_save_on_conflict_ignore(manager):
    @manager.register
    class UniqueUser(AIOModel):
        name = fields.CharField(unique=True)

    await UniqueUser.drop_table(safe=True)
    await UniqueUser.create_table()
    try:
        first = await UniqueUser.create(name="Mickey")

        duplicate = UniqueUser(name="Mickey")
        await duplicate.save(force_insert=True, on_conflict_ignore=True)

        assert duplicate._pk is None
        assert duplicate.is_dirty()
        assert await UniqueUser.select().count() == 1
        assert (await UniqueUser.get()).id == first.id
    finally:
        await UniqueUser.drop_table(safe=True)


async def test_get_or_create_concurrent(manager):
    if manager.backend.db_type != "postgresql":
        pytest.skip("needs separate connections; in-memory sqlite has separate databases")

    @manager.register
    class RaceUser(AIOModel):
        name = fields.CharField(unique=True)

    await RaceUser.drop_table(safe=True)
    await RaceUser.create_table()
    try:

        async def create():
            async with manager.connection():
                return await RaceUser.get_or_create(name="Mickey")

        results = await asyncio.gather(create(), create())

        assert sorted(created for _, created in results) == [False, True]
        assert results[0][0].id == results[1][0].id
        assert await RaceUser.select().count() == 1
    finally:
        await RaceUser.drop_table(safe=True)
