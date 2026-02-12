from peewee_aio import AIOModel, fields


class Model1(AIOModel):
    fint1 = fields.IntegerField(default=0)
    fint2 = fields.IntegerField(null=True, default=0)
    fint3 = fields.IntegerField(null=False, default=0)
    fbint1 = fields.BigIntegerField(default=0)
    fbint2 = fields.BigIntegerField(null=True, default=0)
    fbint3 = fields.BigIntegerField(null=False, default=0)
    fsint1 = fields.SmallIntegerField(default=0)
    fsint2 = fields.SmallIntegerField(null=True, default=0)
    fsint3 = fields.SmallIntegerField(null=False, default=0)
    faint1 = fields.AutoField()
    ffloat1 = fields.FloatField(default=0.0)
    ffloat2 = fields.FloatField(null=True, default=0.0)
    ffloat3 = fields.FloatField(null=False, default=0.0)


class Model2(AIOModel):
    fk1 = fields.ForeignKeyField(Model1, null=True)
    fk2 = fields.ForeignKeyField(Model1, null=False)
    fk3 = fields.ForeignKeyField(Model1)


assert Model1.fint1
assert Model1.fint2
assert Model1.fint3
assert Model1.fbint1
assert Model1.fbint2
assert Model1.fbint3
assert Model1.fsint1
assert Model1.fsint2
assert Model1.fsint3


m1 = Model1()
assert m1.fint1
assert m1.fint2
assert m1.fint3
assert m1.fbint1
assert m1.fbint2
assert m1.fbint3
assert m1.fsint1
assert m1.fsint2
assert m1.fsint3
assert m1.faint1
assert m1.ffloat1
assert m1.ffloat2
assert m1.ffloat3

test = Model1.fint1 == 1
test = Model1.fint1.in_([1, 2, 3])
test = Model1.fint1 << [1, 2, 3]
test = Model1.fint1 << [1, 2, 3]
test = Model1.select().where(Model1.fint1 == 1).peek(2)
test = Model1.select().where(Model1.fint1 << [1, 2, 3]).peek(1)
test = Model1.select().where(Model1.fint1 << [1, 2, 3]).first()
test = Model1.select().where(Model1.fint1 << [1, 2, 3]).dicts()

qs = Model1.select()
test = qs[2]
test = qs[1:2]
test = qs.limit(10).offset(10)


m2 = Model2(fk1=m1, fk2=m1)
assert m2.fk1
assert m2.fk2
assert m2.fk3
assert m2.meta

Model2.select().where(Model2.fk1 << [1, 2, 3])
