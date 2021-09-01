import pytest
import peewee as pw


async def test_sync(models):
    User, _, _ = models

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


def test_base():
    from peewee_aio import Manager

    assert Manager('sqlite:///:memory:')
    assert Manager('aiosqlite:///:memory:')

    assert Manager('mysql://localhost')
    assert Manager('aiomysql://localhost')

    assert Manager('postgresql://localhost')
    assert Manager('postgres://localhost')
    assert Manager('aiopg://localhost')


async def test_manager(models, manager, transaction):
    User, _, _ = models

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


async def test_errors(models, manager, transaction):
    User, _, _ = models
    await manager.create(User, id=1, name='Mickey')

    with pytest.raises(pw.IntegrityError):
        await manager.create(User, id=1, name='John')
