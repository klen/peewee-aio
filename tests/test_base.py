import pytest
import peewee as pw


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


async def test_manager(manager, User, transaction):
    # Execute
    await manager.execute(User.insert(name='Mickey'))
    await manager.execute(User.insert(name='John'))
    await manager.execute(User.insert(name='Timmy'))

    # Fetchval
    data = await manager.fetchval(User.select())
    assert data

    # Fetchone raw
    data = await manager.fetchone(User.select(), raw=True)
    assert data
    assert data['id']
    assert data['name'] == 'Mickey'

    # Fetchone model
    data = await manager.fetchone(User.select())
    assert data
    assert isinstance(data, User)
    assert data.id
    assert data.name == 'Mickey'

    # Fetchmany raw
    data = await manager.fetchmany(2, User.select(), raw=True)
    assert data
    assert len(data) == 2
    assert [d['name'] for d in data] == ['Mickey', 'John']

    # Fetchmany model
    data = await manager.fetchmany(2, User.select())
    assert data
    assert len(data) == 2
    assert [d.name for d in data] == ['Mickey', 'John']

    # Fetchall raw
    data = await manager.fetchall(User.select(), raw=True)
    assert data
    assert len(data) == 3
    assert [d['name'] for d in data] == ['Mickey', 'John', 'Timmy']

    # Fetchall model
    data = await manager.fetchall(User.select())
    assert data
    assert len(data) == 3
    assert [d.name for d in data] == ['Mickey', 'John', 'Timmy']

    # Iterate raw
    async for data in manager.iterate(User.select(), raw=True):
        assert data['name'] in ['Mickey', 'John', 'Timmy']

    # Iterate model
    async for data in manager.iterate(User.select()):
        assert data.name in ['Mickey', 'John', 'Timmy']

    # Run fetchall
    data = await manager.run(User.select())
    assert data
    assert len(data) == 3
    assert [d.name for d in data] == ['Mickey', 'John', 'Timmy']

    # Run iterate
    async for data in manager.run(User.select()):
        assert data.name in ['Mickey', 'John', 'Timmy']


async def test_errors(manager, User, transaction):
    await manager.execute(User.delete())
    await manager.create(User, id=1, name='Mickey')

    with pytest.raises(pw.IntegrityError):
        await manager.create(User, id=1, name='John')
