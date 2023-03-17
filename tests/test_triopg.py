from __future__ import annotations

import pytest


@pytest.fixture(scope="session")
def backend():
    return "triopg"


@pytest.fixture(scope="session")
async def manager(db_url):
    from peewee_aio import Manager

    return Manager(db_url)


async def test_base(manager, user_model):
    import trio_asyncio

    async with trio_asyncio.open_loop():
        async with manager:
            await manager.create_tables()

            res = await manager.run(user_model.select())
            assert not res

            user1 = await manager.create(user_model, name="Mickey")
            assert user1
            user2 = await manager.create(user_model, name="John")
            assert user2

            res1 = await manager.get(user_model, user_model.id == user2.id)
            assert res1
            assert res1.name == "John"
            assert res1 == user2
            res2 = await manager.get(user_model, id=user2.id)
            assert res2
            assert res2 == user2

            res = await manager.get_or_none(user_model, user_model.id == user1.id)
            assert res == user1

            res = await manager.get_or_none(user_model, user_model.id == 999)
            assert res is None

            res = await manager.get_by_id(user_model, user1.id)
            assert res == user1

            [user1, user2] = await manager.run(user_model.select())
            assert user1
            assert user2

            await manager.drop_tables()
