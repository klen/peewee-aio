from __future__ import annotations

from typing import Any

import peewee
import pytest

from .conftest import DataModel


@pytest.fixture()
async def data(schema):
    await DataModel.delete()
    await DataModel.insert_many([DataModel(data=f"t{n}") for n in range(3)])
    return await DataModel.select()


async def test_select(data):
    inst = data[0]

    assert [inst] == await DataModel.select().where(DataModel.id == inst.id)

    async for dm in DataModel.select():
        assert dm

    assert await DataModel.select().exists()
    assert await DataModel.select().count() == len(data)
    assert await DataModel.select().get()
    assert await DataModel.select().peek()
    assert await DataModel.select().first()
    assert await DataModel.select(peewee.fn.MAX(DataModel.id)).scalar()


async def test_select_items(data):
    qs = DataModel.select()
    t1 = await qs[0]
    assert t1
    assert t1.data == "t0"

    t2 = await qs[1]
    assert t2
    assert t2.data == "t1"

    res = await qs[0:2]
    assert res
    assert res == [t1, t2]


async def test_get_or_create(schema):
    from .conftest import DataModel  # type: ignore[]

    Base = DataModel  # noqa: N806

    with pytest.raises(peewee.DatabaseError):
        inst, created = await DataModel.get_or_create(defaults={})

    class DataModel(Base):  # type: ignore[no-redef,valid-type,misc]
        async def save(self, **kwargs):
            self.data += "-custom"
            return await super().save(**kwargs)

    inst, created = await DataModel.get_or_create(data="data")
    assert inst
    assert inst.data == "data-custom"
    assert created

    inst2, created = await DataModel.get_or_create(data="data-custom")
    assert inst2 == inst
    assert not created


async def test_get(data):
    source = data[0]

    inst = await DataModel.get_or_none(DataModel.id == source.id)
    assert inst
    assert inst == source

    inst = await DataModel.get_or_none(DataModel.id == 999)
    assert inst is None

    inst = await DataModel.get(DataModel.id == source.id)
    assert inst
    assert inst == source

    inst = await DataModel.get_by_id(source.id)
    assert inst
    assert inst == source


async def test_prefetch(manager):
    from peewee_aio import AIOModel

    @manager.register
    class BaseModel(AIOModel):
        data = peewee.CharField()

        relmodel_set: Any

    @manager.register
    class RelModel(AIOModel):
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


async def test_union(data):
    from peewee_aio.model import AIOModelCompoundSelectQuery

    qs = (
        DataModel.select().where(DataModel.data == "t1")
        | DataModel.select().where(DataModel.data == "t2")
        | DataModel.select().where(DataModel.data == "t3")
    )

    assert isinstance(qs, AIOModelCompoundSelectQuery)

    res = await qs.limit(2)
    assert res


async def test_scalar(data):
    assert await DataModel.select(DataModel.data).scalars() == ["t0", "t1", "t2"]

    assert await DataModel.select(DataModel.data).scalar() == "t0"
    assert await DataModel.select(DataModel.data).scalar(as_tuple=True) == ("t0",)
    assert await DataModel.select(DataModel.data).scalar(as_dict=True) == {
        "data": "t0",
    }


async def test_first(data):
    qs = DataModel.select().order_by(DataModel.id)
    ts1, ts2, ts3 = await qs
    ts = await qs.first()
    assert ts == ts1
    assert (await qs) == [ts1, ts2, ts3]


async def test_alias(data):
    alias = DataModel.alias()
    assert await alias.select(alias)
