from django.test import TestCase
from nation.testutils import *
from nation.models import *
from nation.policies.domestic import *
import nation.variables as v



class generaltests(TestCase):
    def setUp(self):
        self.subject = nation_generator()[0]

    def test_arrest(self):
        nation = nation_generator()[0]
        policy = arrest(nation)
        #default nations can arrest until they turn blue in the face
        self.assertTrue(policy.can_apply())
        nation.budget = 0
        self.assertFalse(policy.can_apply(), msg="Can't enact with no budget")
        nation.budget = 500
        nation.government = 0
        self.assertFalse(policy.can_apply(), msg="Can't arrest at government=0")
        nation.refresh_from_db()
        snap = snapshoot(nation)
        policy.enact()
        nation.refresh_from_db()
        cost_check(self, nation, snap, policy.cost)
        self.assertGreater(snap.government, nation.government, msg="Arresting should decrease government")


    def test_releasing(self):
        nation = nation_generator()[0]
        policy = release(nation)
        #same as above lol, just in reverse
        self.assertTrue(policy.can_apply())
        nation.budget = 0
        self.assertFalse(policy.can_apply())
        nation.budget = 500
        nation.government = 100
        self.assertFalse(policy.can_apply())
        nation.refresh_from_db()
        snap = snapshoot(nation)
        policy.enact()
        nation.refresh_from_db()
        cost_check(self, nation, snap, policy.cost)
        self.assertGreater(nation.government, snap.government)


    def test_martial_law(self):
        nation = nation_generator()[0]
        policy = martial(nation)
        #again, fresh nations can do it
        self.assertTrue(policy.can_apply())
        nation.budget = 0
        self.assertFalse(policy.can_apply())
        nation.budget = 500
        nation.government = 0
        self.assertFalse(policy.can_apply())
        nation.government = 50
        nation.manpower = 0
        self.assertFalse(policy.can_apply())
        nation.refresh_from_db()
        army = nation.military.army
        snap = snapshoot(nation)
        policy.enact()
        nation.refresh_from_db()
        nation.military.refresh_from_db()
        cost_check(self, nation, snap, policy.cost)
        self.assertGreater(nation.military.army, army)

    def test_elections(self):
        nation = nation_generator()[0]
        policy = elections