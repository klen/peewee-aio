import peewee


async def test_base():
    from peewee_aio import Model

    assert Model  # type: ignore


async def test_model(TestModel, manager):
    assert TestModel
    assert TestModel._manager is manager
    assert TestModel._meta.database is manager.pw_database

    class ChildModel(TestModel):
        is_active = peewee.BooleanField(default=True)

    return ChildModel


async def test_backref(TestModel, manager, schema):
    class BaseModel(TestModel):
        class Meta:
            table_name = "testmodel"

    class Ref(manager.Model):
        data = peewee.CharField()

        test = peewee.ForeignKeyField(BaseModel)

    await Ref.drop_table()
    await Ref.create_table()

    source = await BaseModel.create(data="data")

    from peewee_aio.model import ModelSelect

    assert isinstance(source.ref_set, ModelSelect)

    ref = await Ref.create(data="ref", test=source)
    assert ref == await source.ref_set.first()

    # Load foreing keys
    ref = await Ref.get(data="ref")
    test = await ref.test
    assert test == source

    assert ref.test == source
    assert await ref.test == source

    ref = await Ref.select(Ref, BaseModel).join(BaseModel).first()
    assert ref
    assert ref.test == source

    ref = await Ref(data="ref", test=test).save()
    assert ref.test == source

    await Ref.drop_table()


async def test_fk(TestModel, manager, schema):
    class ParentModel(manager.Model):
        child = peewee.ForeignKeyField(TestModel, null=True)

    from peewee_aio.model import AIOForeignKeyField

    assert isinstance(ParentModel.child, AIOForeignKeyField)

    await ParentModel.create_table()

    parent = await ParentModel.create()
    assert parent.child is None

    child = await TestModel.create(data="body")
    parent = await ParentModel.create(child=child)

    assert parent.child == child

    await ParentModel.drop_table()


async def test_deferred_fk(manager):
    class ParentModel(manager.Model):
        child = peewee.DeferredForeignKey("ChildModel", null=True)

    class ChildModel(manager.Model):
        pass

    from peewee_aio.model import AIOForeignKeyField

    assert isinstance(ParentModel.child, AIOForeignKeyField)

    await ChildModel.create_table()
    await ParentModel.create_table()

    child = await ChildModel.create()

    parent = ParentModel(child=child.id)
    assert await parent.child == child
    assert parent.child == child

    await ParentModel.drop_table()
    await ChildModel.drop_table()


async def test_await_model(TestModel):
    test = TestModel(id=1)
    assert await test == test
    assert await test == test
