from typing import Dict, Type

import aio_databases as aiodb
import peewee as pw
from playhouse import db_url


class Database(pw.Database):

    enabled: bool = False

    def execute(self, *args, **kwargs):
        if not self.enabled:
            raise RuntimeError(
                "Sync operations are not available. Use `manager.allow_sync` to enable."
            )

        return super().execute(*args, **kwargs)  # type: ignore


class SqliteDatabase(Database, pw.SqliteDatabase):
    pass


class MySQLDatabase(Database, pw.MySQLDatabase):
    pass


class PostgresqlDatabase(Database, pw.PostgresqlDatabase):
    pass


_backend_to_db: Dict[str, Type[Database]] = {
    "sqlite": SqliteDatabase,
    "postgres": PostgresqlDatabase,
    "mysql": MySQLDatabase,
}
_backend_to_db["postgresql"] = _backend_to_db["postgres"]


def get_db(db: aiodb.Database) -> Database:
    url = db.backend.url
    if url.path and not url.path.startswith("/"):
        url = url._replace(path=f"/{url.path}")
    params = db_url.parseresult_to_dict(url)
    db_cls = _backend_to_db.get(db.backend.db_type, _backend_to_db["sqlite"])
    return db_cls(**params)
