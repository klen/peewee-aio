from __future__ import annotations

import peewee as pw
import pytest


async def test_get(manager, user_model, transaction):
    res = await manager.run(user_model.select())
    assert not res

    user1 = await manager.create(user_model, name="Mickey")
    assert user1
    user2 = await manager.create(user_model, name="John")
    assert user2

    res1 = await manager.get(user_model, user_model.id == user2.id)
    assert res1
    assert res1.name == "John"
    assert res1 == user2
    res2 = await manager.get(user_model, id=user2.id)
    assert res2
    assert res2 == user2

    with pytest.raises(user_model.DoesNotExist):
        await manager.get(user_model, id=999)

    res = await manager.get_or_none(user_model, user_model.id == user1.id)
    assert res == user1

    res = await manager.get_or_none(user_model, user_model.id == 999)
    assert res is None

    res = await manager.get_by_id(user_model, user1.id)
    assert res == user1


async def test_get_or_create(manager, user_model, transaction):
    user1, created = await manager.get_or_create(user_model, name="Mickey")
    assert created
    assert user1
    assert user1.name == "Mickey"

    user2, created = await manager.get_or_create(user_model, name="Mickey")
    assert not created
    assert user2 == user1


async def test_select(manager, user_model, transaction):
    await manager.run(user_model.insert(name="Mickey"))
    [user] = await manager.run(user_model.select())
    assert user
    assert isinstance(user, user_model)
    assert user.id
    assert user.name == "Mickey"
    assert user.is_active

    res = await manager.run(user_model.select())
    assert list(res) == [user]
    assert list(res) == [user]


async def test_select_fk(manager, role_model, user_model, ur_model, transaction):
    user = await manager.create(user_model, name="Mickey")
    role = await manager.create(role_model, name="admin")

    await manager.create(ur_model, user=user, role=role)

    query = (
        ur_model.select(ur_model, user_model, role_model)
        .join(role_model)
        .switch(ur_model)
        .join(user_model)
    )

    [obj] = await manager.run(query)
    assert obj
    assert obj.role.id
    assert obj.user.id

    async for obj in manager.run(query):
        assert obj
        assert obj.role.id
        assert obj.user.id


async def test_select_tuples(manager, user_model, transaction):
    await manager.run(user_model.insert(name="Mickey"))
    [data] = await manager.run(user_model.select().tuples())
    assert data == (data[0], data[1], "Mickey", True)


async def test_select_dicts(manager, user_model, transaction):
    await manager.run(user_model.insert(name="Mickey"))
    [data] = await manager.run(user_model.select().dicts())
    assert data == {
        "id": data["id"],
        "created": data["created"],
        "name": "Mickey",
        "is_active": True,
    }


async def test_scalar(manager, user_model, transaction):
    await manager.run(user_model.insert(name="Mickey"))
    await manager.run(user_model.insert(name="John"))
    count = await manager.fetchval(user_model.select(pw.fn.Count(user_model.id)))
    assert count == 2


async def test_count(manager, user_model, transaction):
    await manager.run(user_model.insert(name="Mickey"))
    await manager.run(user_model.insert(name="John"))

    count = await manager.count(user_model.select())
    assert count == 2

    count = await manager.count(user_model.select().limit(1))
    assert count == 1


async def test_raw(manager, user_model, transaction):
    sql = "select id, name from user"
    if manager.backend.db_type == "postgresql":
        sql = 'select "id", "name" from "user"'

    await manager.create(user_model, name="Mickey")
    res = await manager.run(user_model.raw(sql))
    assert res
    assert isinstance(res[0], user_model)


async def test_prefetch(manager, user_model, comment_model, transaction):
    user = await manager.create(user_model, name="Mickey")
    qs = comment_model.insert_many(
        [{"body": f"body{n}", "user": user} for n in range(3)],
    )
    await manager.run(qs)

    res = await manager.prefetch(user_model.select())
    assert res

    res = await manager.prefetch(user_model.select(), comment_model)
    assert res
    user = res[0]
    assert user.comment_set
    assert isinstance(user.comment_set, list)
    assert len(user.comment_set) == 3


async def test_union(manager, user_model, transaction):
    await manager.run(user_model.insert(name="Mickey"))
    await manager.run(user_model.insert(name="John"))

    qs = user_model.select().where(
        user_model.name == "Mickey",
    ) | user_model.select().where(
        user_model.name == "John",
    )

    res = await manager.run(qs.limit(2))
    assert res
