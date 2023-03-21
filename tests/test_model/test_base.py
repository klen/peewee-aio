from __future__ import annotations

from typing import Any, Optional

from playhouse.test_utils import count_queries

from .conftest import DataModel


async def test_base_model(manager):
    from peewee_aio import fields

    assert DataModel._manager is manager
    assert DataModel._meta.database is manager.pw_database

    class ChildModel(DataModel):
        is_active = fields.BooleanField(default=True)

    return ChildModel


async def test_backref(manager, schema):
    from peewee_aio import AIOModel, fields

    class BaseModel(DataModel):
        ref_set: Any

        class Meta:
            table_name = "datamodel"

    @manager.register
    class Ref(AIOModel):
        data = fields.CharField()

        test = fields.ForeignKeyField(BaseModel, on_delete="CASCADE")

    await Ref.drop_table()
    await Ref.create_table()

    source = await BaseModel.create(data="data")

    from peewee_aio.model import AIOModelSelect

    assert isinstance(source.ref_set, AIOModelSelect)

    ref: Optional[Ref] = await Ref.create(data="ref", test=source)
    assert ref == await source.ref_set.first()

    # Load foreing keys
    ref = await Ref.get(data="ref")
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


async def test_fk(manager, schema):
    from peewee_aio import AIOModel, fields

    @manager.register
    class ParentModel(AIOModel):
        child_id: Optional[int]
        child = fields.ForeignKeyField(DataModel, null=True, on_delete="CASCADE")

    from peewee_aio.model import AIOForeignKeyField

    assert isinstance(ParentModel.child, AIOForeignKeyField)

    await ParentModel.create_table()

    parent = await ParentModel.create()
    assert await parent.child is None
    assert parent.child_id is None

    child = await DataModel.create(data="body")
    parent = await ParentModel.create(child=child)

    assert await parent.child == child

    await ParentModel.drop_table()


async def test_deferred_fk(manager):
    from peewee_aio import AIOModel, fields

    @manager.register
    class ParentModel(AIOModel):
        child = fields.DeferredForeignKey("ChildModel", null=True, on_delete="CASCADE")

    @manager.register
    class ChildModel(AIOModel):
        id = fields.AutoField()

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


async def test_await_model():
    test = DataModel(id=1)
    assert await test == test
    assert await test == test
