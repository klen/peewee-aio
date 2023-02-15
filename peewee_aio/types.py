from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from .model import AIOModel

import peewee as pw

TVModel = TypeVar("TVModel", bound=pw.Model)
TVAIOModel = TypeVar("TVAIOModel", bound="AIOModel")
