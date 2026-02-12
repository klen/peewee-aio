from __future__ import annotations

import datetime as dt
import logging
from uuid import uuid4

import peewee as pw
import pytest

from peewee_aio import Manager

CONNECTIONS = {
    "aiosqlite": "aiosqlite:///:memory:",
    "aiomysql": "mysql://root@127.0.0.1:3306/tests",
    "aiopg": "aiopg://test:test@localhost:5432/tests",
    "asyncpg": "asyncpg://test:test@localhost:5432/tests",
    "trio-mysql": "trio-mysql://root@127.0.0.1:3306/tests",
    "triopg": "triopg://test:test@localhost:5432/tests",
}
BACKENDS = {
    "aiosqlite",
    "aiomysql",
    "aiopg",
    "asyncpg",
    "trio-mysql",
}


class Role(pw.Model):
    id = pw.UUIDField(primary_key=True, default=uuid4)
    created = pw.DateTimeField(default=dt.datetime.now)
    name = pw.CharField()


class User(pw.Model):
    id = pw.AutoField()
    created = pw.DateTimeField(default=dt.datetime.now)
    name = pw.CharField()
    is_active = pw.BooleanField(default=True)


class UserToRole(pw.Model):
    user = pw.ForeignKeyField(User, backref="roles")
    role = pw.ForeignKeyField(Role, backref="users")

    class Meta:
        primary_key = pw.CompositeKey("user", "role")


class Comment(pw.Model):
    created = pw.DateTimeField(default=dt.datetime.now)
    body = pw.CharField()
    user = pw.ForeignKeyField(User)


@pytest.fixture(scope="session", autouse=True)
def _setup_logging():

    logger = logging.getLogger("peewee")
    logger.setLevel(logging.DEBUG)


@pytest.fixture(scope="session", params=BACKENDS)
def backend(request):
    return request.param


# Supported drivers/databases
@pytest.fixture(scope="session")
def db_url(backend, aiolib):
    if aiolib[0] == "trio" and backend not in {"trio-mysql", "triopg"}:
        return pytest.skip("not supported by trio")

    if aiolib[0] == "asyncio" and backend not in {
        "aiosqlite",
        "aiomysql",
        "aiopg",
        "asyncpg",
    }:
        return pytest.skip("not supported by asyncio")

    return CONNECTIONS[backend]


@pytest.fixture(scope="session")
async def manager(db_url):

    async with Manager(db_url) as manager, manager.connection():
        yield manager


@pytest.fixture(scope="session")
async def schema(manager):
    await manager.create_tables()
    yield True
    await manager.drop_tables()


@pytest.fixture
async def transaction(schema, manager):
    async with manager.transaction() as trans:
        yield manager
        await trans.rollback()


@pytest.fixture(scope="session", autouse=True)
def _register_models(manager):
    manager.register(Role)
    manager.register(User)
    manager.register(UserToRole)
    manager.register(Comment)
