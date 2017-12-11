from nation.models import *
from nation.testutils import *
from nation.mod.multidetect.basic_checks import *
import nation.variables as v
from nation.aid import send_aid, give_weapons, expeditionary

from django.test import TestCase
from django.utils import timezone
import random

class multi_tests(TestCase):
    @classmethod
    def setUpTestData(cls):
        #we need to generate data that emulates actual players
        #or whatever comes close to an actual player
        farmer = nation_generator(1)
        farmed = nation_generator(5)

        normies = nation_generator(20)
        for x in xrange(1, 20):



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



class logout_tests(TestCase):
    @classmethod
    def setUpTestData(cls):
        a = nation_generator(30)
        


class basic_login_test(TestCase):
    def setUp(self):
        nations = nation_generator(2)
        a = nations[0]
        a.creationtime = timezone.now() - timezone.timedelta(days=40)
        for x in range(1,40):
            a.login_times.create(
                turn=x, 
                timestamp=timezone.now() - timezone.timedelta(days=40-x))
        self.nation = a
        self.reference = nations[1]

    def test_logincheck(self):
        self.assertEqual(self.nation.multimeter.logins, 50)
        login_check(self.nation)
        login_check(self.reference)
        self.assertGreater(self.nation.multimeter.logins, 50)
        self.assertEqual(self.reference.multimeter.logins, 50)