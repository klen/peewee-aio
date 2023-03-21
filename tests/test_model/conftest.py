from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from peewee_aio import AIOModel
from peewee_aio.fields import AutoField, CharField

if TYPE_CHECKING:
    from peewee_aio.manager import Manager


class DataModel(AIOModel):
    id = AutoField()
    data = CharField()


@pytest.fixture(scope="session", autouse=True)
async def register_test_model(manager: Manager):
    return manager.register(DataModel)


@pytest.fixture()
async def schema(manager: Manager):
    await DataModel.create_table()
    yield True
    await DataModel.drop_table(
        cascade=manager.backend.db_type != "sqlite",
    )
