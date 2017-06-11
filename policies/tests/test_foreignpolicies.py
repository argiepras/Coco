from django.test import TestCase
from nation.testutils import *
from nation.models import *
from nation.policies.foreign import *
import nation.variables as v


class policytests(TestCase):
    def setUp(self):
        self.subject = nation_generator()[0]

    def test_praise_ussr(self):
        nation = self.subject
        #default nations should be able to praise the ussr
        policy = praise_ussr(nation)
        self.assertTrue(policy.can_apply())
        nation.alignment = 1
        self.assertFalse(policy.can_apply())
        nation.alignment = 2
        nation.budget = 0
        self.assertFalse(policy.can_apply())
        set_nation(nation, requirements)
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
        set_nation(nation, requirements)
        self.assertTrue(policy.can_apply()) #for good measure
        snap = snapshoot(nation)
        policy.enact()
        nation.refresh_from_db()
        self.assertNotEqual(snap.alignment, nation.alignment)
        self.assertEqual(nation.alignment, 3)