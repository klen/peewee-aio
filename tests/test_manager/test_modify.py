from __future__ import annotations


async def test_insert(manager, role_model, user_model, ur_model, transaction):
    res = await manager.run(user_model.select())
    assert not res

    await manager.run(user_model.insert(name="Mickey"))
    [user] = await manager.run(user_model.select())
    assert user
    assert user.id
    assert user.name == "Mickey"

    await manager.run(role_model.insert(name="admin"))
    [role] = await manager.run(role_model.select())
    assert role
    assert role.id
    assert role.name == "admin"

    await manager.run(ur_model.insert(role=role, user=user))
    [user_to_role] = await manager.run(ur_model.select())
    assert user_to_role


async def test_insert_many(manager, user_model, transaction):
    query = user_model.insert_many(
        [
            {"name": "Mickey"},
            {"name": "John"},
        ],
    )
    last_id = await manager.run(query)
    assert last_id is not None

    [user1, user2] = await manager.run(user_model.select().order_by(user_model.id))
    assert user1
    assert user2
    assert user1.name == "Mickey"
    assert user2.name == "John"


async def test_create(manager, user_model, transaction):
    user = await manager.create(user_model, name="Mickey")
    assert user
    assert user.id
    assert user.name == "Mickey"


async def test_create_uid(manager, role_model, transaction):
    from uuid import UUID

    role = await manager.create(role_model, name="admin")
    assert role
    assert role.id
    assert UUID(str(role.id))


async def test_update(manager, user_model, transaction):
    await manager.create(user_model, name="Mickey")
    await manager.create(user_model, name="John")
    query = user_model.update(name="Timmy")
    upd = await manager.run(query)
    assert upd == 2
    user = await manager.get(user_model)
    assert user.name == "Timmy"


async def test_save(manager, user_model, transaction):
    res = await manager.run(user_model.select())
    assert not res

    user = user_model(name="Mickey")
    rows = await manager.save(user)
    assert rows
    assert user.id
    assert user.name == "Mickey"
    assert not user._dirty

    user.name = "John"
    assert user._dirty
    rows = await manager.save(user)
    assert rows
    assert user.id
    assert user.name == "John"
    assert not user._dirty

    user = await manager.get(user_model, id=user.id)
    assert user.name == "John"


async def test_delete(manager, user_model, transaction):
    source = await manager.create(user_model, name="Mickey")
    await manager.execute(user_model.delete())
    res = await manager.run(user_model.select())
    assert not res

    await manager.create(user_model, name="John")

    source = await manager.create(user_model, name="Mickey")
    await manager.delete_instance(source)
    res = await manager.get_or_none(user_model, user_model.id == source.id)
    assert res is None

    source = await manager.create(user_model, name="Mickey")
    await manager.delete_by_id(user_model, source.id)
    res = await manager.get_or_none(user_model, user_model.id == source.id)
    assert res is None

    assert await manager.run(user_model.select())
