from nation.models import *
from nation.testutils import *
import nation.variables as v
from nation.tasks import *

from django.test import TestCase
from django.db.models import Q

from random import randint


class turns(TestCase):
    @classmethod
    def setUpTestData(cls):
        Market.objects.create()
        nation_generator(300)

    #turns are daisy chained
    #so they ought to be tested in reverse order
    def test_basic_turns(self):
        self.spy_turns()
        self.market_turn()
        self.base_turn()

    def spy_turns(self):
        a = Nation.objects.all()[0:2]
        Spy.objects.create(nation=a[0], location=a[1], actioned=True)
        infilgain()
        q = Spy.objects.get()
        self.assertGreater(q.infiltration, Spy._meta.get_field('infiltration').default)
        self.assertFalse(q.actioned)

    def market_turn(self):
        marketturn()
        self.assertGreater(Market.objects.all().count(), 1)

    def base_turn(self):
        turn = current_turn()
        turnchange()
        self.assertGreater(current_turn(), turn)

    def test_trade_balancing(self):
        #the purpose of the trade balancing function is to
        #create a record of the changes in trade balance
        #so we test for that behaviour
        a = Nation.objects.all()[5]
        b = Nation.objects.all()[7]
        a.trade_balance = 0
        b.trade_balance = 0
        a.save()
        b.save()
        for turn in range(10):
            a.trade_balance += 500
            b.trade_balance += randint(-1500, 1500)
            a.save()
            b.save()
            turnchange()
        for tb in a.multimeter.trade_balances.all():
            self.assertEqual(tb.change, 500, msg="change is and should be 500")

        entries = {}
        for tb in b.multimeter.trade_balances.all():
            if tb.change in entries:
                entries[tb.change] += 1
            else:
                entries[tb.change] = 1

        #should be 10 in a perfect world
        #but rng makes it not a perfect world
        #so 5 is a decent compromise
        self.assertGreater(len(entries), 5)