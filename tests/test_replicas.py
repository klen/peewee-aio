from __future__ import annotations

import os
import tempfile

import peewee as pw
import pytest

from peewee_aio import AIOModel, Manager


@pytest.fixture
async def replica_manager(aiolib):
    if aiolib[0] != "asyncio":
        pytest.skip("replica tests only support asyncio")

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    manager = Manager(f"aiosqlite:///{db_path}", replicas=[f"aiosqlite:///{db_path}"])

    @manager.register
    class TestUser(AIOModel):
        id = pw.AutoField()
        name = pw.CharField()

    async with manager, manager.connection():
        await manager.create_tables(TestUser)
        yield manager, TestUser
        await manager.drop_tables(TestUser)

    os.unlink(db_path)  # noqa: PTH108


async def test_replica_context_manager(replica_manager):
    manager, TestUser = replica_manager  # noqa: N806
    await TestUser.create(name="test")

    async with manager.replica():
        user = await TestUser.select().get()
        assert user.name == "test"


async def test_replica_async_for(replica_manager):
    manager, TestUser = replica_manager  # noqa: N806
    await TestUser.create(name="test1")
    await TestUser.create(name="test2")

    async with manager.replica():
        users = [u async for u in TestUser.select().order_by(TestUser.id)]
        assert len(users) == 2
        assert users[0].name == "test1"
        assert users[1].name == "test2"
