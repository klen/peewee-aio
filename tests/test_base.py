from __future__ import annotations

import pytest

from peewee_aio import Manager

from .conftest import User


async def test_sync(manager):
    with pytest.raises(RuntimeError):
        User.create(name="Mickey")

    with pytest.raises(RuntimeError):
        User.insert(name="Mickey").execute()

    with pytest.raises(RuntimeError):
        User.update(name="Mickey").execute()

    user = User(id=1, name="Mickey")
    with pytest.raises(RuntimeError):
        user.save()

    with pytest.raises(RuntimeError):
        user.delete_instance()

    with pytest.raises(RuntimeError):
        list(User.select())

    with manager.allow_sync():
        User.drop_table(safe=True)
        User.create_table()
        User.create(name="Mickey")
        assert User.get()
        User.delete().execute()

    with pytest.raises(RuntimeError):
        User.create(name="Mickey")


def test_databases():

    manager = Manager("sqlite:///:memory:")
    assert manager
    assert manager.backend.db_type == "sqlite"
    assert manager.pw_database
    assert manager.pw_database.database == ":memory:"

    manager = Manager("aiosqlite:///db.sqlite")
    assert manager
    assert manager.backend.db_type == "sqlite"
    assert manager.pw_database
    assert manager.pw_database.database == "db.sqlite"

    assert Manager("mysql://localhost")
    assert Manager("aiomysql://localhost")

    assert Manager("postgresql://localhost")
    assert Manager("postgres://localhost")
    assert Manager("aiopg://localhost")

    manager = Manager("dummy://localhost")
    assert manager
    assert manager.backend.db_type == "dummy"
    assert manager.pw_database
    assert manager.pw_database.database == ""  # noqa:
