from uuid import uuid4
import datetime as dt

import peewee as pw


class Role(pw.Model):
    id = pw.UUIDField(primary_key=True, default=uuid4)
    created = pw.DateTimeField(default=dt.datetime.utcnow)
    name = pw.CharField()


class User(pw.Model):
    created = pw.DateTimeField(default=dt.datetime.utcnow)
    name = pw.CharField()
    is_active = pw.BooleanField(default=True)


class UserToRole(pw.Model):
    user = pw.ForeignKeyField(User, backref="roles")
    role = pw.ForeignKeyField(Role, backref="users")

    class Meta:
        primary_key = pw.CompositeKey('user', 'role')
