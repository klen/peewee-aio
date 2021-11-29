"""Support Peewee ORM with asyncio."""


__version__ = "0.13.0"


from .model import AIOModel as Model
from .manager import Manager

__all__ = 'Manager', 'Model'
