from __future__ import annotations

import peewee as pw
import pytest

from tests.conftest import Comment, Role, User, UserToRole


async def test_get(manager, transaction):
    res = await manager.run(User.select())
    assert not res

    user1 = await manager.create(User, name="Mickey")
    assert user1
    user2 = await manager.create(User, name="John")
    assert user2

    res1 = await manager.get(User, User.id == user2.id)
    assert res1
    assert res1.name == "John"
    assert res1 == user2
    res2 = await manager.get(User, id=user2.id)
    assert res2
    assert res2 == user2

    with pytest.raises(User.DoesNotExist):  # type: ignore[]
        await manager.get(User, id=999)

    res = await manager.get_or_none(User, User.id == user1.id)
    assert res == user1

    res = await manager.get_or_none(User, User.id == 999)
    assert res is None

    res = await manager.get_by_id(User, user1.id)
    assert res == user1


async def test_get_or_create(manager, transaction):
    user1, created = await manager.get_or_create(User, name="Mickey")
    assert created
    assert user1
    assert user1.name == "Mickey"

    user2, created = await manager.get_or_create(User, name="Mickey")
    assert not created
    assert user2 == user1


async def test_select(manager, transaction):
    await manager.run(User.insert(name="Mickey"))
    [user] = await manager.run(User.select())
    assert user
    assert isinstance(user, User)
    assert user.id
    assert user.name == "Mickey"
    assert user.is_active

    res = await manager.run(User.select())
    assert list(res) == [user]
    assert list(res) == [user]


async def test_select_fk(manager, transaction):
    user = await manager.create(User, name="Mickey")
    role = await manager.create(Role, name="admin")

    await manager.create(UserToRole, user=user, role=role)

    query = UserToRole.select(UserToRole, User, Role).join(Role).switch(UserToRole).join(User)

    [obj] = await manager.run(query)
    assert obj
    assert obj.role.id
    assert obj.user.id

    async for obj in manager.run(query):
        assert obj
        assert obj.role.id
        assert obj.user.id


async def test_select_tuples(manager, transaction):
    await manager.run(User.insert(name="Mickey"))
    [data] = await manager.run(User.select().tuples())
    assert data == (data[0], data[1], "Mickey", True)


async def test_select_dicts(manager, transaction):
    await manager.run(User.insert(name="Mickey"))
    [data] = await manager.run(User.select().dicts())
    assert data == {
        "id": data["id"],
        "created": data["created"],
        "name": "Mickey",
        "is_active": True,
    }


async def test_scalar(manager, transaction):
    await manager.run(User.insert(name="Mickey"))
    await manager.run(User.insert(name="John"))
    count = await manager.fetchval(User.select(pw.fn.Count(User.id)))
    assert count == 2


async def test_count(manager, transaction):
    await manager.run(User.insert(name="Mickey"))
    await manager.run(User.insert(name="John"))

    count = await manager.count(User.select())
    assert count == 2

    count = await manager.count(User.select().limit(1))
    assert count == 1


async def test_raw(manager, transaction):
    sql = "select id, name from user"
    if manager.backend.db_type == "postgresql":
        sql = 'select "id", "name" from "user"'

    await manager.create(User, name="Mickey")
    res = await manager.run(User.raw(sql))
    assert res
    assert isinstance(res[0], User)


async def test_prefetch(manager, transaction):
    user = await manager.create(User, name="Mickey")
    qs = Comment.insert_many(
        [{"body": f"body{n}", "user": user} for n in range(3)],
    )
    await manager.run(qs)

    res = await manager.prefetch(User.select())
    assert res

    res = await manager.prefetch(User.select(), Comment)
    assert res
    user = res[0]
    assert user.comment_set
    assert isinstance(user.comment_set, list)
    assert len(user.comment_set) == 3


async def test_union(manager, transaction):
    await manager.run(User.insert(name="Mickey"))
    await manager.run(User.insert(name="John"))

    qs = User.select().where(
        User.name == "Mickey",
    ) | User.select().where(
        User.name == "John",
    )

    res = await manager.run(qs.limit(2))
    assert res
