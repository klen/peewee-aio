import pytest


async def test_sync(User, manager):
    with pytest.raises(RuntimeError):
        User.create(name='Mickey')

    with pytest.raises(RuntimeError):
        User.insert(name='Mickey').execute()

    with pytest.raises(RuntimeError):
        User.update(name='Mickey').execute()

    user = User(id=1, name='Mickey')
    with pytest.raises(RuntimeError):
        user.save()

    with pytest.raises(RuntimeError):
        user.delete_instance()

    with pytest.raises(RuntimeError):
        for user in User.select():
            pass

    with manager.allow_sync():
        User.create_table(True)
        User.create(name='Mickey')
        assert User.get()
        User.delete().execute()

    with pytest.raises(RuntimeError):
        User.create(name='Mickey')


def test_databases():
    from peewee_aio import Manager

    manager = Manager('sqlite:///:memory:')
    assert manager
    assert manager.aio_database
    assert manager.pw_database
    assert manager.pw_database.database == ':memory:'

    manager = Manager('aiosqlite:///db.sqlite')
    assert manager
    assert manager.aio_database
    assert manager.pw_database
    assert manager.pw_database.database == 'db.sqlite'

    assert Manager('mysql://localhost')
    assert Manager('aiomysql://localhost')

    assert Manager('postgresql://localhost')
    assert Manager('postgres://localhost')
    assert Manager('aiopg://localhost')

    manager = Manager('dummy://localhost')
    assert manager
    assert manager.aio_database
    assert manager.pw_database
    assert manager.pw_database.database == ''
