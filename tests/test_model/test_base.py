from __future__ import annotations

import peewee
from playhouse.test_utils import count_queries


async def test_base():
    from peewee_aio import AIOModel

    assert issubclass(AIOModel, peewee.Model)


async def test_base_model(test_model, manager):
    from peewee_aio import fields

    assert test_model
    assert test_model._manager is manager
    assert test_model._meta.database is manager.pw_database

    class ChildModel(test_model):
        is_active = fields.BooleanField(default=True)

    return ChildModel


async def test_backref(test_model, manager, schema):
    from peewee_aio import fields

    class BaseModel(test_model):
        class Meta:
            table_name = "testmodel"

    class Ref(manager.Model):
        data = fields.CharField()

        test = fields.ForeignKeyField(BaseModel, on_delete="CASCADE")

    await Ref.drop_table()
    await Ref.create_table()

    source = await BaseModel.create(data="data")

    from peewee_aio.model import AIOModelSelect

    assert isinstance(source.ref_set, AIOModelSelect)

    ref = await Ref.create(data="ref", test=source)
    assert ref == await source.ref_set.first()

    # Load foreing keys
    ref: Ref = await Ref.get(data="ref")
    test = await ref.test
    assert test == source

    # Check cache
    with count_queries() as counter:
        assert await ref.test == source
        assert await ref.test == source

    assert counter.count == 0

    ref = await Ref.select(Ref, BaseModel).join(BaseModel).first()
    assert ref

    # Check preload
    with count_queries() as counter:
        assert await ref.test == source

    assert counter.count == 0

    ref = await Ref(data="ref", test=test).save()

    # Check initiated
    with count_queries() as counter:
        assert await ref.test == source

    assert counter.count == 0

    await Ref.drop_table()


async def test_fk(test_model, manager, schema):
    from peewee_aio import fields

    class ParentModel(manager.Model):
        child = fields.ForeignKeyField(test_model, null=True, on_delete="CASCADE")

    from peewee_aio.model import AIOForeignKeyField

    assert isinstance(ParentModel.child, AIOForeignKeyField)

    await ParentModel.create_table()

    parent = await ParentModel.create()
    assert parent.child_id is None
    assert await parent.child is None

    child = await test_model.create(data="body")
    parent = await ParentModel.create(child=child)

    assert await parent.child == child

    await ParentModel.drop_table()


async def test_deferred_fk(manager):
    from peewee_aio import fields

    class ParentModel(manager.Model):
        child = fields.DeferredForeignKey("ChildModel", null=True, on_delete="CASCADE")

    class ChildModel(manager.Model):
        pass

    from peewee_aio.model import AIOForeignKeyField

    assert isinstance(ParentModel.child, AIOForeignKeyField)

    await ChildModel.create_table()
    await ParentModel.create_table()

    child = await ChildModel.create()

    parent = ParentModel(child=child.id)
    assert await parent.child == child
    assert await parent.child == child

    await ParentModel.drop_table()
    await ChildModel.drop_table()


async def test_await_model(test_model):
    test = test_model(id=1)
    assert await test == test
    assert await test == test
