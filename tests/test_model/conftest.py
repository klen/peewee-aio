from __future__ import annotations

from typing import TYPE_CHECKING, Type

import pytest

if TYPE_CHECKING:
    from peewee_aio import AIOModel
    from peewee_aio.manager import Manager


@pytest.fixture(scope="session")
async def test_model(manager: Manager):
    from peewee_aio import AIOModel
    from peewee_aio.fields import CharField

    @manager.register
    class TestModel(AIOModel):
        data = CharField()

    return TestModel


@pytest.fixture()
async def schema(test_model: Type[AIOModel], manager: Manager):
    await test_model.create_table()
    yield True
    await test_model.drop_table(
        cascade=manager.backend.db_type != "sqlite",
    )
