import peewee as pw


class Database:

    def execute(self, query, commit=pw.SENTINEL, **context_options):
        raise RuntimeError('Sync queries are not allowed')


class SqliteDatabase(Database, pw.SqliteDatabase):
    pass


class MySQLDatabase(Database, pw.MySQLDatabase):
    pass


class PostgresqlDatabase(Database, pw.PostgresqlDatabase):
    param = "%s"


_backend_to_db = {
    'sqlite': lambda: SqliteDatabase('sqlite:///:memory:'),
    'postgres': lambda: PostgresqlDatabase(''),
    'mysql': lambda: MySQLDatabase(''),
}
_backend_to_db['postgresql'] = _backend_to_db['postgres']


def get_db(backend: str) -> pw.Database:
    return _backend_to_db.get(backend, _backend_to_db['sqlite'])()
