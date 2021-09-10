import logging

import pytest


CONNECTIONS = {
    'aiosqlite': 'aiosqlite:///:memory:',
    'aiomysql': 'mysql://root@127.0.0.1:3306/tests',
    'aiopg': 'aiopg://test:test@localhost:5432/tests',

    'asyncpg': 'asyncpg://test:test@localhost:5432/tests',
    'trio-mysql': 'trio-mysql://root@127.0.0.1:3306/tests',
    'triopg': 'triopg://test:test@localhost:5432/tests',
}
BACKENDS = {
    'trio-mysql',
    'aiosqlite',
    'aiomysql',
    'aiopg',
    'asyncpg',
}


@pytest.fixture(scope='session', autouse=True)
def setup_logging():
    logger = logging.getLogger('peewee')
    logger.setLevel(logging.DEBUG)


@pytest.fixture(scope='session', params=BACKENDS)
def backend(request):
    return request.param


# Supported drivers/databases
@pytest.fixture(scope='session')
def db_url(backend, aiolib):
    if aiolib[0] == 'trio' and backend not in {'trio-mysql', 'triopg'}:
        return pytest.skip()

    if aiolib[0] == 'asyncio' and backend not in {'aiosqlite', 'aiomysql', 'aiopg', 'asyncpg'}:
        return pytest.skip()

    return CONNECTIONS[backend]


@pytest.fixture(scope='session')
async def manager(db_url):
    from peewee_aio import Manager

    async with Manager(db_url, convert_params=True) as manager:
        async with manager.connection():
            yield manager


@pytest.fixture(scope='session')
def models(manager):
    from .models import Role, User, UserToRole

    manager.register(Role)
    manager.register(User)
    manager.register(UserToRole)

    return Role, User, UserToRole


@pytest.fixture(scope='session')
async def schema(models, manager):
    await manager.create_tables(*models, safe=True)
    yield models
    await manager.drop_tables(*models, safe=True)


@pytest.fixture
async def transaction(schema, manager):
    async with manager.transaction() as trans:
        yield manager
        await trans.rollback()
