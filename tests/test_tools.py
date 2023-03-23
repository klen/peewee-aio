import pytest


async def test_getrel():
    from peewee_aio import AIOModel, fields, getrel

    class User(AIOModel):
        id = fields.IntegerField()
        name = fields.CharField()

    class Comment(AIOModel):
        id = fields.IntegerField()
        text = fields.CharField()
        user = fields.ForeignKeyField(User)

    user = User(id=1, name="test")
    comment = Comment(id=1, text="test", user=user)

    test = getrel(comment, Comment.user)
    assert test == user

    comment = Comment(id=1, text="test", user_id=1)
    with pytest.raises(ValueError, match="Relation user is not loaded into"):
        getrel(comment, Comment.user)
