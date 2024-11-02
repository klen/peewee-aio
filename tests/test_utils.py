import peewee as pw

from peewee_aio.utils import safe_join


async def test_safe_join():
    class Role(pw.Model):
        name = pw.CharField()

    class User(pw.Model):
        name = pw.CharField()
        role = pw.ForeignKeyField(Role)

    query = User.select()

    query = safe_join(query, Role, src=User)
    assert str(query)
    assert "JOIN" in str(query)

    query = safe_join(query, Role, src=User)
    assert str(query)
    assert "JOIN" in str(query)
    assert str(query).count("JOIN") == 1
