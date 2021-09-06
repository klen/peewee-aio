import aio_databases as aiodb
import peewee as pw
from playhouse import db_url


class Database:

    enabled: bool = False

    def execute(self, *args, **kwargs):
        if not self.enabled:
            raise RuntimeError(
                'Sync operations are not available. Use `manager.allow_sync` to enable.')

        return super(Database, self).execute(*args, **kwargs)


class SqliteDatabase(Database, pw.SqliteDatabase):
    pass


class MySQLDatabase(Database, pw.MySQLDatabase):
    pass


class PostgresqlDatabase(Database, pw.PostgresqlDatabase):
    #  param = "%s"
    pass


_backend_to_db = {
    'sqlite': lambda params: SqliteDatabase(**params),
    'postgres': lambda params: PostgresqlDatabase(**params),
    'mysql': lambda params: MySQLDatabase(**params),
}
_backend_to_db['postgresql'] = _backend_to_db['postgres']


def get_db(db: aiodb.Database) -> pw.Database:
    url = db.backend.url
    if url.path and not url.path.startswith('/'):
        url = url._replace(path=f"/{url.path}")
    params = db_url.parseresult_to_dict(url)
    return _backend_to_db.get(db.backend.db_type, _backend_to_db['sqlite'])(params)
