import logging

import pytest


CONNECTIONS = {
    'sqlite': 'aiosqlite:///:memory:',
    'mysql': 'mysql://root@127.0.0.1:3306/tests',
    'postgres': 'aiopg://test:test@localhost:5432/tests',

    'asyncpg': 'asyncpg://test:test@localhost:5432/tests',
}
BACKENDS = {
    'sqlite',
    'mysql',
    'postgres',
    #  'asyncpg',
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
def db_url(backend):
    return CONNECTIONS[backend]


@pytest.fixture(scope='session')
async def manager(db_url):
    from peewee_aio import Manager

    async with Manager(db_url) as manager:
        yield manager


@pytest.fixture(scope='session')
def models(manager):
    from .models import Role, User, UserToRole

    manager.register(Role)
    manager.register(User)
    manager.register(UserToRole)

    return User, Role, UserToRole


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
