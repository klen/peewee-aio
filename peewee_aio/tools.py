from typing import Coroutine, Optional, Union, overload

from peewee_aio.types import TVAIOModel

from .fields import ForeignKeyField
from .model import AIOModel


@overload
def getrel(
    instance: AIOModel, fk: ForeignKeyField[Coroutine[None, None, TVAIOModel]]
) -> TVAIOModel:
    ...


@overload
def getrel(
    instance: AIOModel, fk: ForeignKeyField[Coroutine[None, None, Optional[TVAIOModel]]]
) -> Optional[TVAIOModel]:
    ...


def getrel(
    instance: AIOModel,
    fk: Union[
        ForeignKeyField[Coroutine[None, None, TVAIOModel]],
        ForeignKeyField[Coroutine[None, None, Optional[TVAIOModel]]],
    ],
) -> Union[TVAIOModel, Optional[TVAIOModel]]:
    """Get fk relation from the given instance cache. Raise ValueError if not loaded."""

    attr = fk.name
    fk = instance.__data__.get(attr)
    if fk is None:
        return None

    try:
        return instance.__rel__[attr]
    except KeyError:
        raise ValueError(f"Relation {attr} is not loaded into {instance!r}") from None
