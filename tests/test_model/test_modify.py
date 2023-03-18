from __future__ import annotations

from typing import TYPE_CHECKING, Type

import peewee
import pytest

if TYPE_CHECKING:
    from peewee_aio import AIOModel


async def test_create(test_model: Type[AIOModel], schema):
    await test_model.delete()

    class TestModel(test_model):  # type: ignore[valid-type,misc]
        async def save(self, **kwargs):
            self.data += "-custom"
            return await super().save(**kwargs)

    inst = await TestModel.create(data="data")
    assert inst
    assert inst.id
    assert inst.data == "data-custom"


@pytest.mark.skip("Not implemented")
async def test_bulk_create(test_model, schema):
    instances = [test_model(data=f"n{n}") for n in range(3)]
    await test_model.bulk_create(instances, 2)
    assert await test_model.select().count() == 3


async def test_save(test_model, schema):
    inst = test_model(data="data")
    await inst.save()

    assert inst.id
    assert inst == await test_model.get(test_model.id == inst.id)


async def test_delete_instance(test_model, schema):
    inst = await test_model.create(data="data")
    await inst.delete_instance()
    assert None is await test_model.get_or_none(test_model.id == inst.id)


async def test_insert(test_model, schema):
    await test_model.delete()
    await test_model.insert(data="inserted")

    test = await test_model.get_or_none()
    assert test.data == "inserted"

    assert await test_model.insert_many([{"data": f"data{n}"} for n in range(4)])
    assert await test_model.select().count() == 5

    assert await test_model.insert_many([test_model(data=f"data{n}") for n in range(4)])
    assert await test_model.select().count() == 9


async def test_insert_many(test_model, schema):
    with pytest.raises(peewee.Insert.DefaultValuesException):
        await test_model.insert_many([])

    qs = test_model.insert_many([{"data": f"t{n}"} for n in range(3)])

    await qs
    assert await test_model.select().count() == 3

    await qs.on_conflict_ignore()
    assert await test_model.select().count() == 6


async def test_insert_many_returning(test_model, schema, manager):
    qs = test_model.insert_many([{"data": f"t{n}"} for n in range(1, 4)])
    qs = qs.returning(test_model)
    if manager.backend.db_type not in {"postgresql"}:
        return pytest.skip("only postgres is supported")

    res = await qs
    assert res
    for idx, tm in enumerate(res, 1):
        assert isinstance(tm, test_model)
        assert tm.id == idx
        assert tm.data == f"t{idx}"
    return None


async def test_update(test_model, schema):
    inst = await test_model.create(data="data")

    await test_model.update({"data": "updated"}).where(test_model.id == inst.id)

    test = await test_model.get_or_none(test_model.id == inst.id)
    assert test.data == "updated"


async def test_delete(test_model, schema):
    inst = await test_model.create(data="data")
    await test_model.delete().where(test_model.id == inst.id)

    test = await test_model.get_or_none(test_model.id == inst.id)
    assert test is None
