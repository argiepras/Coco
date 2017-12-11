from nation.models import *
from nation.testutils import *
import nation.variables as v
from nation.tasks import *

from django.test import TestCase
from django.db.models import Q


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

