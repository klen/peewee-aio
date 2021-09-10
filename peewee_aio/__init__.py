"""Support Peewee ORM with asyncio."""


__version__ = "0.2.1"


from .model import AIOModel as Model  # noqa
from .manager import Manager  # noqa
