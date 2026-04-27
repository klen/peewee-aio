from __future__ import annotations

from typing import Any, Optional

import pytest
from playhouse.test_utils import count_queries

from peewee_aio import AIOModel, fields
from peewee_aio.model import AIOModelSelect

from .conftest import DataModel


async def test_base_model(manager):

    assert DataModel._manager is manager
    assert DataModel._meta.database is manager.pw_database

    class ChildModel(DataModel):
        is_active = fields.BooleanField(default=True)

    return ChildModel


async def test_backref(manager, schema):

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
    @manager.register
    class ParentModel(AIOModel):
        child_id: Optional[int]
        child = fields.ForeignKeyField(DataModel, null=True, on_delete="CASCADE")

    assert isinstance(ParentModel.child, fields.AIOForeignKeyField)

    await ParentModel.create_table()

    parent = await ParentModel.create()
    assert await parent.child is None
    assert parent.child_id is None

    child = await DataModel.create(data="body")
    parent = await ParentModel.create(child=child)

    assert await parent.child == child

    await ParentModel.drop_table()


async def test_deferred_fk(manager):

    @manager.register
    class ParentModel(AIOModel):
        child = fields.DeferredForeignKey("ChildModel", null=True, on_delete="CASCADE")

    @manager.register
    class ChildModel(AIOModel):
        id = fields.AutoField()

    assert isinstance(ParentModel.child, fields.AIOForeignKeyField)

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


class _FetchUser(AIOModel):
    id = fields.IntegerField()
    name = fields.CharField()


class _FetchComment(AIOModel):
    id = fields.IntegerField()
    text = fields.CharField()
    user = fields.ForeignKeyField(_FetchUser, null=False)


class _FetchNullableComment(AIOModel):
    id = fields.IntegerField()
    text = fields.CharField()
    user = fields.ForeignKeyField(_FetchUser, null=True)


async def test_model_fetch_from_cache():
    user = _FetchUser(id=1, name="test")
    comment = _FetchComment(id=1, text="test", user=user)

    assert comment.fetch(_FetchComment.user) is user
    assert comment.fetch(_FetchComment.user, silent=True) is user


async def test_model_fetch_unsaved_instance():
    new_user = _FetchUser(name="test")
    comment = _FetchComment(id=1, text="test", user=new_user)

    assert comment.fetch(_FetchComment.user) is new_user


async def test_model_fetch_not_loaded_raises():
    comment = _FetchComment(id=1, text="test", user_id=1)

    with pytest.raises(ValueError, match="Relation user is not loaded into"):
        comment.fetch(_FetchComment.user)


async def test_model_fetch_silent():
    comment = _FetchComment(id=1, text="test", user_id=1)
    assert comment.fetch(_FetchComment.user, silent=True) is None

    comment = _FetchComment.__new__(_FetchComment)
    comment.__data__ = {"id": 1, "text": "test"}
    comment.__rel__ = {}
    assert comment.fetch(_FetchComment.user, silent=True) is None


async def test_model_fetch_nullable():
    comment = _FetchNullableComment(id=1, text="test", user=None)

    assert comment.fetch(_FetchNullableComment.user) is None
    assert comment.fetch(_FetchNullableComment.user, silent=True) is None


async def test_model_fetch_missing_key():
    comment = _FetchComment.__new__(_FetchComment)
    comment.__data__ = {"id": 1, "text": "test"}
    comment.__rel__ = {}

    with pytest.raises(ValueError, match="Relation user is not loaded into"):
        comment.fetch(_FetchComment.user)


async def test_model_fetch_deferred(manager):
    @manager.register
    class Tag(AIOModel):
        id = fields.IntegerField()
        name = fields.CharField()
        post = fields.DeferredForeignKey("Post", null=False)

    @manager.register
    class Post(AIOModel):
        id = fields.IntegerField()
        title = fields.CharField()

    assert isinstance(Tag.post, fields.AIOForeignKeyField)

    post = Post(id=1, title="test")
    tag = Tag(id=1, name="tag", post=post)

    assert tag.fetch(Tag.post) is post
    assert tag.fetch(Tag.post, silent=True) is post

    tag = Tag(id=1, name="tag", post_id=1)
    with pytest.raises(ValueError, match="Relation post is not loaded into"):
        tag.fetch(Tag.post)
    assert tag.fetch(Tag.post, silent=True) is None
