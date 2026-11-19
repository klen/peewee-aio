"""Compile-time checks of the public typing; verified by ``uv run pyrefly check``."""

from __future__ import annotations

from typing import Any, assert_type

import peewee as pw

from peewee_aio import AIOModel, Manager, fields

manager = Manager("sqlite:///:memory:")


@manager.register
class Customer(AIOModel):
    id = fields.AutoField()
    phone = fields.CharField(max_length=20, unique=True)
    status = fields.CharField(max_length=20)


async def _write() -> None:
    assert_type(await Customer.update(status="rejected").where(Customer.id == 1), int)
    assert_type(await Customer.delete().where(Customer.id == 1), int)
    assert_type(await Customer.update(status="x").returning(Customer), list[Customer])
    assert_type(await Customer.delete().returning(Customer), list[Customer])
    assert_type(
        await Customer.insert(phone="1")
        .on_conflict(conflict_target=[Customer.phone], preserve=[Customer.phone])
        .returning(Customer),
        list[Customer],
    )


async def _read() -> None:
    qs = Customer.select(Customer.phone, pw.fn.COUNT(Customer.id)).group_by(Customer.phone)
    assert_type(await qs.tuples(), list[tuple[Any, ...]])
    assert_type(await qs.namedtuples(), list[tuple[Any, ...]])
    assert_type(await qs.dicts(), list[dict[str, Any]])
    assert_type(await Customer.select().first(), Customer | None)
    assert_type(await Customer.select().first(2), list[Customer])
    assert_type(await Customer.select().objects(), list[Customer])
    assert_type(await Customer.select().objects(dict), list[Any])
    assert_type(await Customer.get(Customer.id == 1), Customer)
