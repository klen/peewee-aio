import pytest

import peewee as pw


@pytest.mark.skip
def test_pw():
    from .models import Role, User

    db = pw.SqliteDatabase(':memory:')
    User._meta.database = db
    User.create_table()
    Role._meta.database = db
    Role.create_table()

    role = Role.create(name='admin')
    assert role
