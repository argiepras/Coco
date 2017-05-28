from nation.models import *
from nation.testutils import *
from nation.mod.multidetect.basic_checks import *
import nation.variables as v
from django.test import TestCase
import random

"""
class base_checks(TestCase):

    @classmethod
    def setUpTestData(cls):
        a = nation_generator(30)
        gdp = 300
        balance = -2000
        for n in a:
            n.trade_balance = balance
            n.gdp = gdp
            n.creationtime -= timezone.timedelta(hours=random.randint(1, 100))
            n.save()
            gdp += 100
            balance += 250
        ID.objects.get_or_create()
        Market.objects.create()


    def test_tradecheck(self):
        a = Nation.objects.filter(trade_balance__gte=2000)[0]
        b = Nation.objects.filter(trade_balance__lte=-2000)[0]
        c = Nation.objects.get(trade_balance=250)
        self.assertEqual(trade_balance_check(a), True)
        self.assertEqual(trade_balance_check(b), True)
        self.assertEqual(trade_balance_check(c), False)

    def test_bp(self):
        prod = Nation.objects.all().order_by('?')[0]
        prod = base_production(prod)
        self.assertGreater(prod, 0)
"""