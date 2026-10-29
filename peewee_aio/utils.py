from __future__ import annotations

from peewee import JOIN, Expression, Model, ModelAlias, ModelSelect

TSource = type[Model] | ModelAlias


def safe_join(  # noqa: PLR0913, PLR0917
    query: ModelSelect,
    dest: TSource,
    join_type: str = JOIN.INNER,
    src: TSource | None = None,
    on: Expression | None = None,
    attr: str | None = None,
) -> ModelSelect:
    """Join a model to a query if it is not already joined."""

    joins = query._joins.get(src)  # type: ignore[]
    if joins:
        # peewee >= 4.5 also returns a join context as the 4th value
        on, attr, constructor = query._normalize_join(src, dest, on, attr)[:3]  # type: ignore[]
        for dest_, attr_, constructor_, _ in joins:
            if dest_ == dest and attr_ == attr and constructor_ == constructor:
                return query

    return query.join(dest, join_type=join_type, on=on, src=src)
