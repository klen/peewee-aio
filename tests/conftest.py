import sys
import pytest

from .models import *  # noqa


CONNECTIONS = {
    'aiosqlite': 'aiosqlite:///:memory:',
    'aiomysql': 'mysql://root@127.0.0.1:3306/tests',
    'aiopg': 'aiopg://test:test@localhost:5432/tests',

    'asyncpg': 'asyncpg://test:test@localhost:5432/tests',
    'trio-mysql': 'trio-mysql://root@127.0.0.1:3306/tests',
    'triopg': 'triopg://test:test@localhost:5432/tests',
}
BACKENDS = {
    'aiosqlite',
    'aiomysql',
    'aiopg',
    'asyncpg',
    'trio-mysql',
}


@pytest.fixture(scope='session', autouse=True)
def setup_logging():
    import logging

    logger = logging.getLogger('peewee')
    logger.setLevel(logging.DEBUG)


@pytest.fixture(scope='session', params=BACKENDS)
def backend(request):
    return request.param


# Supported drivers/databases
@pytest.fixture(scope='session')
def db_url(backend, aiolib):
    if backend == 'aiomysql' and sys.version_info >= (3, 10):
        return pytest.skip('aiomysql doesnt support python 3.10')

    if aiolib[0] == 'trio' and backend not in {'trio-mysql', 'triopg'}:
        return pytest.skip('invalid backend')

    if aiolib[0] == 'asyncio' and backend not in {'aiosqlite', 'aiomysql', 'aiopg', 'asyncpg'}:
        return pytest.skip('invalid backend')

    return CONNECTIONS[backend]


@pytest.fixture(scope='session')
async def manager(db_url):
    from peewee_aio import Manager

    async with Manager(db_url) as manager:
        async with manager.connection():
            yield manager


@pytest.fixture(scope='session')
async def schema(manager, User, Role, UserToRole, Comment):
    await manager.create_tables()
    yield (User, Role, UserToRole, Comment)
    await manager.drop_tables()


@pytest.fixture
async def transaction(schema, manager):
    async with manager.transaction() as trans:
        yield manager
        await trans.rollback()
