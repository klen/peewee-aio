from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from .model import AIOModel

import peewee as pw

TV = TypeVar("TV")
TVModel = TypeVar("TVModel", bound=pw.Model)
TVAIOModel = TypeVar("TVAIOModel", bound="AIOModel")
