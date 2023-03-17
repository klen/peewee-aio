from __future__ import annotations

import datetime as dt
import sys
from uuid import uuid4

import peewee as pw
import pytest

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


@pytest.fixture(scope="session", autouse=True)
def _setup_logging():
    import logging

    logger = logging.getLogger("peewee")
    logger.setLevel(logging.DEBUG)


@pytest.fixture(scope="session", params=BACKENDS)
def backend(request):
    return request.param


# Supported drivers/databases
@pytest.fixture(scope="session")
def db_url(backend, aiolib):
    if backend == "aiomysql" and sys.version_info >= (3, 10):
        return pytest.skip("aiomysql doesnt support python 3.10")

    if aiolib[0] == "trio" and backend not in {"trio-mysql", "triopg"}:
        return pytest.skip("invalid backend")

    if aiolib[0] == "asyncio" and backend not in {
        "aiosqlite",
        "aiomysql",
        "aiopg",
        "asyncpg",
    }:
        return pytest.skip("invalid backend")

    return CONNECTIONS[backend]


@pytest.fixture(scope="session")
async def manager(db_url):
    from peewee_aio import Manager

    async with Manager(db_url) as manager:
        async with manager.connection():
            yield manager


@pytest.fixture(scope="session")
async def schema(manager, user_model, role_model, ur_model, comment_model):
    await manager.create_tables()
    yield (user_model, role_model, ur_model, comment_model)
    await manager.drop_tables()


@pytest.fixture()
async def transaction(schema, manager):
    async with manager.transaction() as trans:
        yield manager
        await trans.rollback()


@pytest.fixture(scope="session")
def role_model(manager):
    @manager.register
    class Role(pw.Model):
        id = pw.UUIDField(primary_key=True, default=uuid4)
        created = pw.DateTimeField(default=dt.datetime.utcnow)
        name = pw.CharField()

    return Role


@pytest.fixture(scope="session")
def user_model(manager):
    @manager.register
    class User(pw.Model):
        created = pw.DateTimeField(default=dt.datetime.utcnow)
        name = pw.CharField()
        is_active = pw.BooleanField(default=True)

    return User


@pytest.fixture(scope="session")
def ur_model(manager, role_model, user_model):
    @manager.register
    class UserToRole(pw.Model):
        user = pw.ForeignKeyField(user_model, backref="roles")
        role = pw.ForeignKeyField(role_model, backref="users")

        class Meta:
            primary_key = pw.CompositeKey("user", "role")

    return UserToRole


@pytest.fixture(scope="session")
def comment_model(manager, user_model):
    @manager.register
    class Comment(pw.Model):
        created = pw.DateTimeField(default=dt.datetime.utcnow)
        body = pw.CharField()
        user = pw.ForeignKeyField(user_model)

    return Comment
