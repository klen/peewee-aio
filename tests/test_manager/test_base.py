from __future__ import annotations

import peewee
import pytest


async def test_manager(manager, user_model, transaction):
    assert manager.current_conn

    # Execute
    await manager.execute(user_model.insert(name="Mickey"))
    await manager.execute(user_model.insert(name="John"))
    await manager.execute(user_model.insert(name="Timmy"))

    # Fetchval
    data = await manager.fetchval(user_model.select())
    assert data

    # Fetchone raw
    data = await manager.fetchone(user_model.select(), raw=True)
    assert data
    assert data["id"]
    assert data["name"] == "Mickey"

    # Fetchone model
    data = await manager.fetchone(user_model.select())
    assert data
    assert isinstance(data, user_model)
    assert data.id
    assert data.name == "Mickey"

    # Fetchmany raw
    data = await manager.fetchmany(2, user_model.select(), raw=True)
    assert data
    assert len(data) == 2
    assert [d["name"] for d in data] == ["Mickey", "John"]

    # Fetchmany model
    data = await manager.fetchmany(2, user_model.select())
    assert data
    assert len(data) == 2
    assert [d.name for d in data] == ["Mickey", "John"]

    # Fetchall raw
    data = await manager.fetchall(user_model.select(), raw=True)
    assert data
    assert len(data) == 3
    assert [d["name"] for d in data] == ["Mickey", "John", "Timmy"]

    # Fetchall model
    data = await manager.fetchall(user_model.select())
    assert data
    assert len(data) == 3
    assert [d.name for d in data] == ["Mickey", "John", "Timmy"]

    # Iterate raw
    async for data in manager.iterate(user_model.select(), raw=True):
        assert data["name"] in ["Mickey", "John", "Timmy"]

    # Iterate model
    async for data in manager.iterate(user_model.select()):
        assert data.name in ["Mickey", "John", "Timmy"]

    # Run fetchall
    data = await manager.run(user_model.select())
    assert data
    assert len(data) == 3
    assert [d.name for d in data] == ["Mickey", "John", "Timmy"]

    # Run iterate
    async for data in manager.run(user_model.select()):
        assert data.name in ["Mickey", "John", "Timmy"]


async def test_errors(manager, user_model, transaction):
    await manager.execute(user_model.delete())
    await manager.create(user_model, id=1, name="Mickey")

    with pytest.raises(peewee.IntegrityError):
        await manager.create(user_model, id=1, name="John")
