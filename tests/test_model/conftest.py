from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from peewee_aio import AIOModel
from peewee_aio.fields import AutoField, CharField, IntegerField

if TYPE_CHECKING:
    from peewee_aio.manager import Manager


class DataModel(AIOModel):
    id = AutoField()
    data = CharField()
    num = IntegerField(null=True)


@pytest.fixture(scope="session", autouse=True)
async def register_test_model(manager: Manager):
    return manager.register(DataModel)


@pytest.fixture()
async def schema(manager: Manager):
    cascade = manager.backend.db_type != "sqlite"
    await DataModel.drop_table(safe=True, cascade=cascade)
    await DataModel.create_table()
    yield True
    await DataModel.drop_table(cascade=cascade)
