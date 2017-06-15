from django.test import TestCase
from nation.testutils import *
from nation.models import *
from nation.policies.foreign import *
import nation.variables as v


class policytests(TestCase):
    def setUp(self):
        self.subject = nation_generator()


    def test_praise_ussr(self):
        nation = self.subject
        #default nations should be able to praise the ussr
        policy = praise_ussr(nation)
        print policy.cost
        self.assertTrue(policy.can_apply())
        nation.alignment = 1
        self.assertFalse(policy.can_apply())
        nation.alignment = 2
        nation.budget = 0
        self.assertFalse(policy.can_apply())
        set_nation(nation, policy.requirements)
        self.assertTrue(policy.can_apply()) #for good measure
        snap = snapshoot(nation)
        policy.enact()
        nation.refresh_from_db()
        self.assertNotEqual(snap.alignment, nation.alignment)
        self.assertEqual(nation.alignment, 1)


    def test_praise_us(self):
        nation = self.subject
        policy = praise_us(nation)
        self.assertTrue(policy.can_apply())
        nation.alignment = 3
        self.assertFalse(policy.can_apply())
        nation.alignment = 2
        nation.budget = 0
        self.assertFalse(policy.can_apply())
        set_nation(nation, policy.requirements)
        self.assertTrue(policy.can_apply()) #for good measure
        snap = snapshoot(nation)
        policy.enact()
        nation.refresh_from_db()
        self.assertNotEqual(snap.alignment, nation.alignment)
        self.assertEqual(nation.alignment, 3)


    def test_neutrality(self):
        nation = self.subject
        policy = declareneutrality(nation)
        self.assertFalse(policy.can_apply()) #standard to be neutral
        nation.alignment = 3
        nation.save(update_fields=['alignment'])
        self.assertTrue(policy.can_apply())
        nation.budget = 0
        self.assertFalse(policy.can_apply())
        set_nation(nation, policy.requirements)
        self.assertTrue(policy.can_apply()) #for good measure
        snap = snapshoot(nation)
        policy.enact()
        nation.refresh_from_db()
        self.assertNotEqual(snap.alignment, nation.alignment)
        self.assertEqual(nation.alignment, 2)


    def test_us_intervention(self):
        nation = self.subject
        policy = us_intervention(nation)
        self.assertFalse(policy.can_apply())
        set_nation(nation, policy.requirements)
        self.assertTrue(policy.can_apply())
        nation.alignment = 1 #commie
        self.assertFalse(policy.can_apply())
        nation.alignment = 2
        troops = nation.military.army
        policy.enact()
        nation.refresh_from_db()
        nation.military.refresh_from_db()
        self.assertGreater(nation.military.army, troops)
        self.assertEqual(nation.us_points, 0)


    def test_ussr_intervention(self):
        nation = self.subject
        policy = soviet_intervention(nation)
        self.assertFalse(policy.can_apply())
        set_nation(nation, policy.requirements)
        self.assertTrue(policy.can_apply())
        nation.alignment = 3 #commie
        self.assertFalse(policy.can_apply())
        nation.alignment = 2
        troops = nation.military.army
        policy.enact()
        nation.refresh_from_db()
        nation.military.refresh_from_db()
        self.assertGreater(nation.military.army, troops)
        self.assertEqual(nation.soviet_points, 0)


    def test_usaid(self):
        nation = self.subject
        policy = usaid(nation)
        self.assertFalse(policy.can_apply())
        set_nation(nation, policy.requirements)
        self.assertTrue(policy.can_apply())
        nation.alignment = 1 #commie
        self.assertFalse(policy.can_apply())
        nation.alignment = 2
        snap = snapshoot(nation)
        policy.enact()
        nation.refresh_from_db()
        cost_check(self, nation, snap, policy.cost)
        self.assertGreater(nation.growth, snap.growth)


    def test_sovietaid(self):
        nation = self.subject
        policy = sovietaid(nation)
        self.assertFalse(policy.can_apply())
        set_nation(nation, policy.requirements)
        self.assertTrue(policy.can_apply())
        nation.alignment = 3
        self.assertFalse(policy.can_apply())
        nation.alignment = 2
        snap = snapshoot(nation)
        policy.enact()
        nation.refresh_from_db()
        cost_check(self, nation, snap, policy.cost)
        self.assertGreater(nation.growth, snap.growth)


