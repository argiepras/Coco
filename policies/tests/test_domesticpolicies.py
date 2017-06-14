from django.test import TestCase
from nation.testutils import *
from nation.models import *
from nation.policies.domestic import *
import nation.variables as v



class generaltests(TestCase):
    def setUp(self):
        self.subject = nation_generator()

    def test_arrest(self):
        nation = nation_generator()
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
        nation = nation_generator()
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
        nation = nation_generator()
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
        nation = nation_generator()
        policy = elections(nation)
        self.assertTrue(policy.can_apply())
        #only requirements are budgetary
        nation.budget = 0
        self.assertFalse(policy.can_apply())
        nation.refresh_from_db()
        snap = snapshoot(nation)
        self.assertTrue((policy.can_apply()))
        policy.enact()
        nation.refresh_from_db()
        cost_check(self, nation, snap, policy.cost)
        self.assertGreater(nation.government, snap.government)
        self.assertGreater(nation.approval, snap.approval)


    def test_housing(self):
        nation = nation_generator()
        policy = housing(nation)
        #default behaviour is increasing approval at the cost of budget
        #and slight decrease in economy
        #only available to commies and mixies at <100 approval
        #defaults should be able to use it
        self.assertTrue(policy.can_apply())
        nation.budget = 0
        self.assertFalse(policy.can_apply())
        nation.budget = 1000
        nation.economy = 90
        self.assertFalse(policy.can_apply())
        nation.economy = 0 
        nation.approval = 100
        self.assertFalse(policy.can_apply())
        nation.refresh_from_db()
        self.assertTrue(policy.can_apply())
        snap = snapshoot(nation)
        policy.enact()
        nation.refresh_from_db()
        cost_check(self, nation, snap, policy.cost)
        self.assertGreater(nation.approval, snap.approval)
        self.assertGreater(snap.economy, nation.economy)


    def test_wage(self):
        nation = nation_generator()
        policy = wage(nation)
        #increase approval at the cost of growth
        #not available to commies
        self.assertTrue(policy.can_apply())
        nation.growth = -10
        self.assertFalse(policy.can_apply())
        nation.growth = 10
        nation.economy = 0
        self.assertFalse(policy.can_apply(), msg="Commies can't minimum wage")
        nation.refresh_from_db()
        snap = snapshoot(nation)
        policy.enact()
        nation.refresh_from_db()
        cost_check(self, nation, snap, policy.cost)
        self.assertGreater(nation.approval, snap.approval, msg="Approval not increased")
        self.assertGreater(snap.growth, nation.growth, msg="Growth didn't subtract")


    def test_freefood(self):
        nation = nation_generator()
        policy = freefood(nation)
        #food for approval
        #everyone can do if they have the food
        #and not maxed approval
        nation.food = 1
        self.assertFalse(policy.can_apply())
        set_nation(nation, policy.requirements)
        nation.save()
        snap = snapshoot(nation)
        self.assertTrue(policy.can_apply())
        nation.approval = 100
        self.assertFalse(policy.can_apply())
        nation.refresh_from_db()
        policy.enact()
        nation.refresh_from_db()
        cost_check(self, nation, snap, policy.cost)
        self.assertGreater(nation.approval, snap.approval)


    def test_school(self):
        nation = nation_generator()
        policy = school(nation)
        #increases literacy at the cost of budget
        #cost decreases with uni count
        self.assertTrue(policy.can_apply())
        nation.budget = 0
        self.assertFalse(policy.can_apply())
        nation.budget = 1000
        nation.rm = 0
        self.assertFalse(policy.can_apply())
        nation.refresh_from_db()
        cost = policy.cost['budget']
        nation.universities = 1
        nation.gdp = 10000
        nation.save()
        policy = school(nation)
        self.assertGreater(policy.cost['budget'], cost, msg="Cost should decrease with uni count")
        set_nation(nation, policy.requirements)
        self.assertTrue(policy.can_apply())
        nation.save()
        snap = snapshoot(nation)
        policy.enact()
        nation.refresh_from_db()
        cost_check(self, nation, snap, policy.cost)
        self.assertGreater(nation.literacy, snap.literacy, msg="schools should increase literacy")


    def test_university(self):
        nation = nation_generator()
        policy = university(nation)
        self.assertFalse(policy.can_apply())
        set_nation(nation, policy.cost)
        nation.save()
        self.assertTrue(policy.can_apply())
        nation.land = nation.land - nation.farmland()
        self.assertFalse(policy.can_apply(), msg="Universities should take up land")
        nation.refresh_from_db()
        snap = snapshoot(nation)
        policy.enact()
        nation.refresh_from_db()
        cost_check(self, nation, snap, policy.cost)
        self.assertGreater(nation.universities, snap.universities, msg="Building universities should increase university count")


    def test_unicost(self):
        nation = nation_generator()
        policy = university(nation)
        cost = policy.cost
        nation.closed_universities = 1
        policy = university(nation)
        for field in cost:
            self.assertGreater(policy.cost[field], cost[field], msg="%s cost should increase with closed universities" % field)

        nation.refresh_from_db()
        nation.subregion = "China"
        policy = university(nation)
        self.assertLess(sum(policy.cost.values()), sum(cost.values()), msg="cost should decrease in Asia")


    def test_closinguni(self):
        nation = nation_generator()
        policy = closeuni(nation)
        self.assertFalse(policy.can_apply())
        self.assertEqual(nation.closed_universities, 0)
        nation.universities = 1
        self.assertTrue(policy.can_apply())
        nation.save()
        policy.enact()
        nation.refresh_from_db()
        self.assertEqual(nation.universities, 0)
        self.assertEqual(nation.closed_universities, 1)


    def test_openuni(self):
        nation = nation_generator()
        policy = reopenuni(nation)
        self.assertFalse(policy.can_apply())
        nation.closed_universities = 1
        nation.budget = 500
        self.assertFalse(policy.can_apply()) #need more budget than default has
        nation.budget = 1000
        nation.save()
        self.assertTrue(policy.can_apply())
        snap = snapshoot(nation)
        policy.enact()
        nation.refresh_from_db()
        cost_check(self, nation, snap, policy.cost)
        self.assertGreater(nation.universities, snap.universities)
        self.assertGreater(snap.closed_universities, nation.closed_universities)


    def test_hospitals(self):
        nation = nation_generator()
        policy = hospital(nation)
        nation.budget = 0
        nation.rm = 0
        self.assertFalse(policy.can_apply())
        nation.budget = policy.requirements['budget']
        self.assertFalse(policy.can_apply())
        set_nation(nation, policy.requirements)
        self.assertTrue(policy.can_apply())
        nation.healthcare = 100
        self.assertFalse(policy.can_apply())
        nation.healthcare = 50
        nation.save()
        snap = snapshoot(nation)
        policy.enact()
        nation.refresh_from_db()
        cost_check(self, nation, snap, policy.cost)
        self.assertGreater(nation.healthcare, snap.healthcare, msg="Building hospitals should increase healthcare")


    def test_medicalresearch(self):
        nation = nation_generator()
        policy = medicalresearch(nation)
        nation.budget = 0
        nation.research = 0
        self.assertFalse(policy.can_apply())
        nation.budget = policy.requirements['budget']
        self.assertFalse(policy.can_apply())
        set_nation(nation, policy.requirements)
        self.assertTrue(policy.can_apply())
        nation.healthcare = 100
        self.assertFalse(policy.can_apply())
        nation.healthcare = 50
        nation.save()
        snap = snapshoot(nation)
        policy.enact()
        nation.refresh_from_db()
        cost_check(self, nation, snap, policy.cost)
        self.assertGreater(nation.healthcare, snap.healthcare, msg="Building hospitals should increase healthcare")


    def test_cultofpersonality(self):
        nation = nation_generator()
        policy = cult(nation)
        self.assertTrue(policy.can_apply())
        nation.budget = 0
        self.assertFalse(policy.can_apply())
        nation.budget = 5000
        nation.government = 40
        self.assertFalse(policy.can_apply())
        nation.government = 60
        nation.refresh_from_db()
        snap = snapshoot(nation)
        policy.enact()
        nation.refresh_from_db()
        cost_check(self, nation, snap, policy.cost)
        self.assertEqual(nation.government, 0)
        self.assertGreater(nation.approval, snap.approval, msg="Cult of personality should increase approvals")
