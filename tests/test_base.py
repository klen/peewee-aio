from __future__ import annotations

import peewee as pw
import pytest

from peewee_aio import Manager


async def test_sync(manager):
    # A dedicated table: the test used to drop and recreate the shared `User` one
    class SyncUser(pw.Model):
        name = pw.CharField()

        class Meta:
            database = manager.pw_database

    with pytest.raises(RuntimeError):
        SyncUser.create(name="Mickey")

    with pytest.raises(RuntimeError):
        SyncUser.insert(name="Mickey").execute()

    with pytest.raises(RuntimeError):
        SyncUser.update(name="Mickey").execute()

    user = SyncUser(id=1, name="Mickey")
    with pytest.raises(RuntimeError):
        user.save()

    with pytest.raises(RuntimeError):
        user.delete_instance()

    with pytest.raises(RuntimeError):
        list(SyncUser.select())

    with manager.allow_sync():
        SyncUser.drop_table(safe=True)
        SyncUser.create_table()
        try:
            SyncUser.create(name="Mickey")
            assert SyncUser.get()
            SyncUser.delete().execute()
        finally:
            SyncUser.drop_table()

    with pytest.raises(RuntimeError):
        SyncUser.create(name="Mickey")


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
    assert manager.pw_database.database == ""
