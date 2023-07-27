from __future__ import annotations

from typing import Optional, Type, cast

from peewee import JOIN, Expression, Model, ModelSelect


def safe_join(  # noqa: PLR0913
    query: ModelSelect,
    dest: Type[Model],
    join_type: str = JOIN.INNER,
    src: Optional[Type[Model]] = None,
    on: Optional[Expression] = None,
    attr: Optional[str] = None,
) -> ModelSelect:
    """Join a model to a query if it is not already joined."""

    joins = query._joins.get(src)  # type: ignore[]
    if joins:
        on, attr, constructor = query._normalize_join(src, dest, on, attr)  # type: ignore[]
        for dest_, attr_, constructor_, _ in joins:
            if dest_ == dest and attr_ == attr and constructor_ == constructor:
                return query

    return cast(ModelSelect, query.join(dest, join_type=join_type, on=on, src=src))
