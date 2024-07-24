from django.db import models


class Premium(models.Model):
    """
    ORM model of the Chat table
    """

    id = models.IntegerField(default=0, primary_key=True)
    uid = models.IntegerField(default=0, unique=True, db_index=True)
    time = models.BigIntegerField(default=0)

    class Meta:
        db_table = f'premium'

    def __str__(self):
        return f'premium: {self.uid}'


class Payments(models.Model):
    """
    ORM model of the Chat table
    """

    uid = models.IntegerField(default=0)
    id = models.IntegerField(default=0, primary_key=True)
    success = models.IntegerField(default=0)

    class Meta:
        db_table = f'payments'

    def __str__(self):
        return f'payments: {self.uid}'


acmodels = {'premium': Premium, 'payments': Payments}
