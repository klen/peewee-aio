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


async def test_base():
    from peewee_aio import Model

    assert Model


async def test_model(TestModel, manager):
    assert TestModel
    assert TestModel._meta.manager is manager
    assert TestModel._meta.database is manager.pw_database

    class ChildModel(TestModel):
        is_active = peewee.BooleanField(default=True)

    return ChildModel
    return ChildModel._meta.manager is manager
    return ChildModel._meta.database is manager.pw_database


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


async def test_get_or_create(TestModel, schema):

    with pytest.raises(peewee.DatabaseError):
        inst, created = await TestModel.get_or_create(defaults={})

    class TestModel(TestModel):

        async def save(self, **kwargs):
            self.data += '-custom'
            return await super().save(**kwargs)

    inst, created = await TestModel.get_or_create(data='data')
    assert inst
    assert inst.data == 'data-custom'
    assert created

    inst2, created = await TestModel.get_or_create(data='data-custom')
    assert inst2 == inst
    assert not created


async def test_get(TestModel, schema):
    source = await TestModel.create(data='data')

    inst = await TestModel.get_or_none(TestModel.id == source.id)
    assert inst
    assert inst == source

    inst = await TestModel.get_or_none(TestModel.id == 999)
    assert inst is None

    inst = await TestModel.get(TestModel.id == source.id)
    assert inst
    assert inst == source

    inst = await TestModel.get_by_id(source.id)
    assert inst
    assert inst == source


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


async def test_select(TestModel, schema):
    await TestModel.delete()
    inst = await TestModel.create(data='data')

    assert [inst] == await TestModel.select().where(TestModel.id == inst.id)

    async for data in TestModel.select():
        assert data == inst

    assert await TestModel.select().exists()
    assert await TestModel.select().count() == 1
    assert await TestModel.select().get() == inst
    assert await TestModel.select().peek() == inst
    assert await TestModel.select().first() == inst
    assert await TestModel.select(peewee.fn.MAX(TestModel.id)).scalar()


async def test_select_items(TestModel, schema):
    await TestModel.insert_many([dict(data=f"t{n}") for n in range(3)])
    qs = TestModel.select()
    t1 = await qs[0]
    assert t1
    assert t1.data == 't0'

    t2 = await qs[1]
    assert t2
    assert t2.data == 't1'

    res = await qs[0:2]
    assert res
    assert res == [t1, t2]


async def test_prefetch(manager):
    class BaseModel(manager.Model):
        data = peewee.CharField()

    class RelModel(manager.Model):
        data = peewee.CharField()
        base = peewee.ForeignKeyField(BaseModel)

    await BaseModel.create_table(safe=True)
    await RelModel.create_table(safe=True)

    source = await BaseModel.create(data='data')
    res = await BaseModel.select().prefetch()
    assert res

    await RelModel.insert_many([dict(base=source, data=f"{n}") for n in range(3)])
    res = await BaseModel.select().prefetch(RelModel)
    assert res
    assert res[0].relmodel_set
    assert len(res[0].relmodel_set) == 3

    await RelModel.drop_table(safe=True)
    await BaseModel.drop_table(safe=True)


async def test_backref(TestModel, manager, schema):

    class Ref(manager.Model):
        data = peewee.CharField()

        test = peewee.ForeignKeyField(TestModel)

    await Ref.drop_table()
    await Ref.create_table()

    source = await TestModel.create(data='data')

    from peewee_aio.model import ModelSelect

    assert isinstance(source.ref_set, ModelSelect)

    ref = await Ref.create(data='ref', test=source)
    assert ref == await source.ref_set.first()

    # Load foreing keys
    ref = await Ref.get(data='ref')
    test = await ref.test
    assert test == source

    assert ref.test == source
    assert await ref.test == source

    ref = await Ref.select(Ref, TestModel).join(TestModel).first()
    assert ref
    assert ref.test == source

    ref = await Ref(data='ref', test=test).save()
    assert ref.test == source

    await Ref.drop_table()


async def test_await_model(TestModel):
    test = TestModel(id=1)
    assert await test == test
    assert await test == test
