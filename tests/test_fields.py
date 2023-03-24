import pytest


async def test_fetchfk():
    from peewee_aio import AIOModel, fields

    class User(AIOModel):
        id = fields.IntegerField()
        name = fields.CharField()

    class Comment(AIOModel):
        id = fields.IntegerField()
        text = fields.CharField()
        user = fields.FetchForeignKeyField(User)

    user = User(id=1, name="test")
    comment = Comment(id=1, text="test", user=user)
    assert comment.user is user

    comment = Comment(id=1, text="test", user_id=user.id)
    with pytest.raises(RuntimeError):
        comment.user

    user2 = User(name="test2")
    comment = Comment(id=1, text="test", user=user2)
    assert comment.user is user2


async def test_aiofk():
    from peewee_aio import AIOModel, fields

    class User(AIOModel):
        id = fields.IntegerField()
        name = fields.CharField()

    class Comment(AIOModel):
        id = fields.IntegerField()
        text = fields.CharField()
        user = fields.AIOForeignKeyField(User)

    user = User(name="test2")
    comment = Comment(id=1, text="test", user=user)
    assert await comment.user is user
