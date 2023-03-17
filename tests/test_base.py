from __future__ import annotations

import pytest


async def test_sync(user_model, manager):
    with pytest.raises(RuntimeError):
        user_model.create(name="Mickey")

    with pytest.raises(RuntimeError):
        user_model.insert(name="Mickey").execute()

    with pytest.raises(RuntimeError):
        user_model.update(name="Mickey").execute()

    user = user_model(id=1, name="Mickey")
    with pytest.raises(RuntimeError):
        user.save()

    with pytest.raises(RuntimeError):
        user.delete_instance()

    with pytest.raises(RuntimeError):
        list(user_model.select())

    with manager.allow_sync():
        user_model.create_table(True)
        user_model.create(name="Mickey")
        assert user_model.get()
        user_model.delete().execute()

    with pytest.raises(RuntimeError):
        user_model.create(name="Mickey")


def test_databases():
    from peewee_aio import Manager

    manager = Manager("sqlite:///:memory:")
    assert manager
    assert manager.aio_database
    assert manager.pw_database
    assert manager.pw_database.database == ":memory:"

    manager = Manager("aiosqlite:///db.sqlite")
    assert manager
    assert manager.aio_database
    assert manager.pw_database
    assert manager.pw_database.database == "db.sqlite"

    assert Manager("mysql://localhost")
    assert Manager("aiomysql://localhost")

    assert Manager("postgresql://localhost")
    assert Manager("postgres://localhost")
    assert Manager("aiopg://localhost")

    manager = Manager("dummy://localhost")
    assert manager
    assert manager.aio_database
    assert manager.pw_database
    assert manager.pw_database.database == ""
