"""Support Peewee ORM with asyncio."""

# isort: skip_file


__version__ = "0.16.3"


from .model import AIOModel as Model
from .manager import Manager

__all__ = "Manager", "Model"
