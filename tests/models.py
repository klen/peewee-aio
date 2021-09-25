"""Peewee models for the tests."""

from uuid import uuid4
import datetime as dt

import peewee as pw
import pytest


@pytest.fixture(scope='session')
def Role(manager):

    @manager.register
    class Role(pw.Model):
        id = pw.UUIDField(primary_key=True, default=uuid4)
        created = pw.DateTimeField(default=dt.datetime.utcnow)
        name = pw.CharField()

    return Role


@pytest.fixture(scope='session')
def User(manager):

    @manager.register
    class User(pw.Model):
        created = pw.DateTimeField(default=dt.datetime.utcnow)
        name = pw.CharField()
        is_active = pw.BooleanField(default=True)

    return User


@pytest.fixture(scope='session')
def UserToRole(manager, Role, User):

    @manager.register
    class UserToRole(pw.Model):
        user = pw.ForeignKeyField(User, backref="roles")
        role = pw.ForeignKeyField(Role, backref="users")

        class Meta:
            primary_key = pw.CompositeKey('user', 'role')

    return UserToRole


@pytest.fixture(scope='session')
def Comment(manager, User):

    @manager.register
    class Comment(pw.Model):
        created = pw.DateTimeField(default=dt.datetime.utcnow)
        body = pw.CharField()
        user = pw.ForeignKeyField(User)

    return Comment
