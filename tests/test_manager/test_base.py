from __future__ import annotations

import peewee
import pytest

from tests.conftest import User


async def test_manager(manager, transaction):
    assert manager.current_conn

    # Execute
    await manager.execute(User.insert(name="Mickey"))
    await manager.execute(User.insert(name="John"))
    await manager.execute(User.insert(name="Timmy"))

    # Fetchval
    data = await manager.fetchval(User.select())
    assert data

    # Fetchone raw
    data = await manager.fetchone(User.select(), raw=True)
    assert data
    assert data["id"]
    assert data["name"] == "Mickey"

    # Fetchone model
    data = await manager.fetchone(User.select())
    assert data
    assert isinstance(data, User)
    assert data.id
    assert data.name == "Mickey"

    # Fetchmany raw
    data = await manager.fetchmany(2, User.select(), raw=True)
    assert data
    assert len(data) == 2
    assert [d["name"] for d in data] == ["Mickey", "John"]

    # Fetchmany model
    data = await manager.fetchmany(2, User.select())
    assert data
    assert len(data) == 2
    assert [d.name for d in data] == ["Mickey", "John"]

    # Fetchall raw
    data = await manager.fetchall(User.select(), raw=True)
    assert data
    assert len(data) == 3
    assert [d["name"] for d in data] == ["Mickey", "John", "Timmy"]

    # Fetchall model
    data = await manager.fetchall(User.select())
    assert data
    assert len(data) == 3
    assert [d.name for d in data] == ["Mickey", "John", "Timmy"]

    # Iterate raw
    async for data in manager.iterate(User.select(), raw=True):
        assert data["name"] in ["Mickey", "John", "Timmy"]

    # Iterate model
    async for data in manager.iterate(User.select()):
        assert data.name in ["Mickey", "John", "Timmy"]

    # Run fetchall
    data = await manager.run(User.select())
    assert data
    assert len(data) == 3
    assert [d.name for d in data] == ["Mickey", "John", "Timmy"]

    # Run iterate
    async for data in manager.run(User.select()):
        assert data.name in ["Mickey", "John", "Timmy"]


async def test_errors(manager, transaction):
    await manager.execute(User.delete())
    await manager.create(User, id=1, name="Mickey")

    with pytest.raises(peewee.IntegrityError):
        await manager.create(User, id=1, name="John")
