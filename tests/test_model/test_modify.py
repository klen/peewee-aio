from __future__ import annotations

import peewee
import pytest

from .conftest import DataModel


async def test_create(schema):
    from .conftest import DataModel  # type: ignore[]

    Base = DataModel  # noqa: N806

    await Base.delete()

    class DataModel(Base):  # type: ignore[no-redef,valid-type,misc]
        async def save(self, **kwargs):
            self.data += "-custom"
            return await super().save(**kwargs)

    inst = await DataModel.create(data="data")
    assert inst
    assert inst.id
    assert inst.data == "data-custom"


async def test_bulk_create(schema):
    instances = [DataModel(data=f"n{n}") for n in range(3)]
    await DataModel.bulk_create(instances, 2)
    assert await DataModel.select().count() == 3


async def test_save(schema):
    inst = DataModel(data="data")
    await inst.save()

    assert inst.id
    assert inst == await DataModel.get(DataModel.id == inst.id)


async def test_delete_instance(schema):
    inst = await DataModel.create(data="data")
    await inst.delete_instance()
    assert None is await DataModel.get_or_none(DataModel.id == inst.id)


async def test_insert(schema):
    await DataModel.delete()
    await DataModel.insert(data="inserted")

    test = await DataModel.get_or_none()
    assert test
    assert test.data == "inserted"

    assert await DataModel.insert_many([{"data": f"data{n}"} for n in range(4)])
    assert await DataModel.select().count() == 5

    assert await DataModel.insert_many([DataModel(data=f"data{n}") for n in range(4)])
    assert await DataModel.select().count() == 9


async def test_insert_many(schema):
    with pytest.raises(peewee.Insert.DefaultValuesException):
        await DataModel.insert_many([])

    qs = DataModel.insert_many([{"data": f"t{n}"} for n in range(3)])

    await qs
    assert await DataModel.select().count() == 3

    await qs.on_conflict_ignore()
    assert await DataModel.select().count() == 6


async def test_insert_many_returning(schema, manager):
    qs = DataModel.insert_many([{"data": f"t{n}"} for n in range(1, 4)])
    qs = qs.returning(DataModel)
    if manager.backend.db_type not in {"postgresql"}:
        return pytest.skip("only postgres is supported")

    res = await qs
    assert res
    for idx, tm in enumerate(res, 1):
        assert isinstance(tm, DataModel)
        assert tm.id == idx
        assert tm.data == f"t{idx}"
    return None


async def test_update(schema):
    inst = await DataModel.create(data="data")

    await DataModel.update({"data": "updated"}).where(DataModel.id == inst.id)

    test = await DataModel.get_or_none(DataModel.id == inst.id)
    assert test
    assert test.data == "updated"


async def test_bulk_update(schema):
    await DataModel.insert_many([{"data": f"t{n}"} for n in range(3)])
    instances = await DataModel.select()

    for instance in instances:
        instance.data = "updated"

    await DataModel.bulk_update(instances, [DataModel.data], 2)
    async for instance in DataModel.select():
        assert instance.data == "updated"


async def test_delete(schema):
    inst = await DataModel.create(data="data")
    await DataModel.delete().where(DataModel.id == inst.id)

    test = await DataModel.get_or_none(DataModel.id == inst.id)
    assert test is None
