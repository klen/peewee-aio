import pytest
import peewee


async def test_create(TestModel, schema):
    await TestModel.delete()

    class TestModel(TestModel):

        async def save(self, **kwargs):
            self.data += '-custom'
            return await super().save(**kwargs)

    inst = await TestModel.create(data='data')
    assert inst
    assert inst.id
    assert inst.data == 'data-custom'


@pytest.mark.skip('Not implemented')
async def test_bulk_create(TestModel, schema):
    instances = [TestModel(data=f"n{n}") for n in range(3)]
    await TestModel.bulk_create(instances, 2)
    assert await TestModel.select().count() == 3


async def test_save(TestModel, schema):
    inst = TestModel(data='data')
    await inst.save()

    assert inst.id
    assert inst == await TestModel.get(TestModel.id == inst.id)


async def test_delete_instance(TestModel, schema):
    inst = await TestModel.create(data='data')
    await inst.delete_instance()
    assert None is await TestModel.get_or_none(TestModel.id == inst.id)


async def test_insert(TestModel, schema):
    await TestModel.delete()
    await TestModel.insert(data='inserted')

    test = await TestModel.get_or_none()
    assert test.data == 'inserted'

    assert await TestModel.insert_many([{'data': f"data{n}"} for n in range(4)])
    assert await TestModel.select().count() == 5

    assert await TestModel.insert_many([TestModel(data=f"data{n}") for n in range(4)])
    assert await TestModel.select().count() == 9


async def test_insert_many(TestModel, schema):
    with pytest.raises(peewee.Insert.DefaultValuesException):
        await TestModel.insert_many([])

    qs = TestModel.insert_many([dict(data=f"t{n}") for n in range(3)])

    await qs
    assert await TestModel.select().count() == 3

    await qs.on_conflict_ignore()
    assert await TestModel.select().count() == 6


async def test_insert_many_returning(TestModel, schema, manager):
    qs = TestModel.insert_many([dict(data=f"t{n}") for n in range(1, 4)])
    qs = qs.returning(TestModel)
    if manager.aio_database.backend.db_type not in {'postgresql'}:
        return pytest.skip('only postgres is supported')

    res = await qs
    assert res
    for idx, tm in enumerate(res, 1):
        assert isinstance(tm, TestModel)
        assert tm.id == idx
        assert tm.data == f"t{idx}"


async def test_update(TestModel, schema):
    inst = await TestModel.create(data='data')

    await TestModel.update({'data': 'updated'}).where(TestModel.id == inst.id)

    test = await TestModel.get_or_none(TestModel.id == inst.id)
    assert test.data == 'updated'


async def test_delete(TestModel, schema):
    inst = await TestModel.create(data='data')
    await TestModel.delete().where(TestModel.id == inst.id)

    test = await TestModel.get_or_none(TestModel.id == inst.id)
    assert test is None
