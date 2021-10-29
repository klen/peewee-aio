import peewee
import pytest


@pytest.fixture(scope='session')
async def TestModel(manager):

    class TestModel(manager.Model):
        data = peewee.CharField()

    return TestModel


@pytest.fixture
async def schema(TestModel):
    await TestModel.create_table()
    yield
    await TestModel.drop_table()
