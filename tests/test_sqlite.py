import datetime as dt

import pytest


@pytest.fixture(scope="session")
def backend():
    return "aiosqlite"


async def test_sqlite(manager):
    unow = dt.datetime.now(tz=dt.timezone.utc)

    assert await manager.fetchval("SELECT 1") == 1
    assert await manager.fetchval("SELECT date_part('day', datetime())") == unow.day
    assert await manager.fetchval("SELECT date_trunc('day', datetime())") == unow.strftime(
        "%Y-%m-%d 00:00:00"
    )
