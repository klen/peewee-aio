from __future__ import annotations

from typing import TYPE_CHECKING

import peewee
import pytest

if TYPE_CHECKING:
    from peewee_aio.model import AIOModel


async def test_select(test_model: AIOModel, schema):
    await test_model.delete()
    inst = await test_model.create(data="data")

    assert [inst] == await test_model.select().where(test_model.id == inst.id)

    async for data in test_model.select():
        assert data == inst

    assert await test_model.select().exists()
    assert await test_model.select().count() == 1
    assert await test_model.select().get() == inst
    assert await test_model.select().peek() == inst
    assert await test_model.select().first() == inst
    assert await test_model.select(peewee.fn.MAX(test_model.id)).scalar()


async def test_select_items(test_model, schema):
    await test_model.insert_many([{"data": f"t{n}"} for n in range(3)])
    qs = test_model.select()
    t1 = await qs[0]
    assert t1
    assert t1.data == "t0"

    t2 = await qs[1]
    assert t2
    assert t2.data == "t1"

    res = await qs[0:2]
    assert res
    assert res == [t1, t2]


async def test_get_or_create(test_model, schema):

    with pytest.raises(peewee.DatabaseError):
        inst, created = await test_model.get_or_create(defaults={})

    class TestModel(test_model):
        async def save(self, **kwargs):
            self.data += "-custom"
            return await super().save(**kwargs)

    inst, created = await TestModel.get_or_create(data="data")
    assert inst
    assert inst.data == "data-custom"
    assert created

    inst2, created = await TestModel.get_or_create(data="data-custom")
    assert inst2 == inst
    assert not created


async def test_get(test_model, schema):
    source = await test_model.create(data="data")

    inst = await test_model.get_or_none(test_model.id == source.id)
    assert inst
    assert inst == source

    inst = await test_model.get_or_none(test_model.id == 999)
    assert inst is None

    inst = await test_model.get(test_model.id == source.id)
    assert inst
    assert inst == source

    inst = await test_model.get_by_id(source.id)
    assert inst
    assert inst == source


async def test_prefetch(manager):
    class BaseModel(manager.Model):
        data = peewee.CharField()

    class RelModel(manager.Model):
        data = peewee.CharField()
        base = peewee.ForeignKeyField(BaseModel)

    await BaseModel.create_table(safe=True)
    await RelModel.create_table(safe=True)

    source = await BaseModel.create(data="data")
    res = await BaseModel.select().prefetch()
    assert res

    await RelModel.insert_many([{"base": source, "data": f"{n}"} for n in range(3)])
    res = await BaseModel.select().prefetch(RelModel)
    assert res
    assert res[0].relmodel_set
    assert len(res[0].relmodel_set) == 3

    await RelModel.drop_table(safe=True)
    await BaseModel.drop_table(safe=True)


async def test_union(test_model, schema):
    from peewee_aio.model import AIOModelCompoundSelectQuery

    await test_model.delete()
    await test_model.insert_many([test_model(data=f"t{n}") for n in range(3)])

    qs = (
        test_model.select().where(test_model.data == "t1")
        | test_model.select().where(test_model.data == "t2")
        | test_model.select().where(test_model.data == "t3")
    )

    assert isinstance(qs, AIOModelCompoundSelectQuery)

    res = await qs.limit(2)
    assert res


async def test_scalar(test_model, schema):
    await test_model.delete()
    await test_model.insert_many([test_model(data=f"t{n}") for n in range(3)])
    assert await test_model.select(test_model.data).scalars() == ["t0", "t1", "t2"]

    assert await test_model.select(test_model.data).scalar() == "t0"
    assert await test_model.select(test_model.data).scalar(as_tuple=True) == ("t0",)
    assert await test_model.select(test_model.data).scalar(as_dict=True) == {
        "data": "t0",
    }


async def test_first(test_model, schema):
    await test_model.insert_many([test_model(data=f"t{n}") for n in range(3)])
    qs = test_model.select().order_by(test_model.id)
    ts1, ts2, ts3 = await qs
    ts = await qs.first()
    assert ts == ts1
    assert (await qs) == [ts1, ts2, ts3]
