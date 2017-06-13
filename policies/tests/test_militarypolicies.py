from django.test import TestCase
from nation.testutils import *
from nation.models import *
from nation.policies.military import *
import nation.variables as v


class policytests(TestCase):
    def setUp(self):
        self.subject = nation_generator()[0]


    def test_conscription(self):
        #the behaviour of conscription is such that it subtracts from growth, 
        #manpower and training and adds to army size
        nation = self.subject
        policy = conscript(nation)
        #newly generated nations have enough growth and manpower to conscript
        self.assertTrue(policy.can_apply())
        nation.growth = 0
        self.assertFalse(policy.can_apply())
        nation.growth = 10
        nation.manpower = 0
        self.assertFalse(policy.can_apply())
        set_nation(nation, policy.requirements)
        snap = snapshoot(nation)
        troops = nation.military.army
        training = nation.military.training
        policy.enact()
        nation.refresh_from_db()
        nation.military.refresh_from_db()
        self.assertEqual(troops, nation.military.army - 2) #supposed to increase army size by 2k
        cost_check(self, nation, snap, policy.cost)
        self.assertGreater(training, nation.military.training)

    def test_training(self):
        nation = self.subject
        policy = train(nation)
        nation.budget = 0
        self.assertFalse(policy.can_apply())
        nation.budget = policy.cost['budget']
        self.assertTrue(policy.can_apply())
        nation.save()
        nation.military.army = 0
        self.assertFalse(policy.can_apply())
        nation.military.refresh_from_db()
        training = nation.military.training
        snap = snapshoot(nation)
        policy.enact()
        nation.refresh_from_db()
        cost_check(self, nation, snap, policy.cost)
        self.assertEqual(training, nation.military.training - 10)


    def test_demobilize(self):
        nation = self.subject
        policy = demobilize(nation)
        #default nations can deconscript
        self.assertTrue(policy.can_apply())
        nation.military.army = 0
        self.assertFalse(policy.can_apply())
        nation.military.refresh_from_db()
        army = nation.military.army
        policy.enact()
        nation.military.refresh_from_db()
        #demobilization reduces army size, so reference is bigger than database data
        self.assertGreater(army, nation.military.army)


    def test_attack_rebels(self):
        nation = self.subject
        policy = attackrebels(nation)
        self.assertTrue(nation.rebels == 0)
        self.assertFalse(policy.can_apply())
        nation.rebels = 5
        nation.save()
        snap = snapshoot(nation)
        self.assertTrue(policy.can_apply())
        policy.enact()
        nation.refresh_from_db()
        if not 'defeated' in policy.result:
            self.assertGreater(snap.rebels, nation.rebels)
        self.assertGreater(snap.budget, nation.budget)


    def test_gas_rebels(self):
        nation = self.subject
        policy = gasrebels(nation)
        self.assertFalse(policy.can_apply()) #doesn't start with GASSS
        nation.military.chems = 5
        self.assertFalse(policy.can_apply())
        nation.military.chems = 10
        self.assertFalse(policy.can_apply())
        nation.military.chems = 8
        nation.rebels = 20
        self.assertFalse(policy.can_apply())
        nation.military.chems = 10
        self.assertTrue(policy.can_apply())
        snap = snapshoot(nation)
        policy.enact()
        nation.refresh_from_db()
        nation.military.refresh_from_db()
        self.assertGreater(snap.rebels, nation.rebels)
        self.assertGreater(snap.reputation, nation.reputation)


    def test_foreign_weapons(self):
        self.relation_weapons(soviet_weapons, 'soviet_points')
        self.relation_weapons(us_weapons, 'us_points')



    def relation_weapons(self, testingpolicy, relations):
        nation = nation_generator()[0]
        policy = testingpolicy(nation)
        self.assertFalse(policy.can_apply())
        setattr(nation, relations, 100)
        self.assertTrue(policy.can_apply())
        nation.alignment = (3 if relations.split('_')[0] == 'soviet' else 1)
        self.assertFalse(policy.can_apply())
        nation.alignment = (1 if relations.split('_')[0] == 'soviet' else 3)
        nation.oil = 0
        setattr(nation, relations, 0)
        nation.save()
        for weapons in [10, 900, 2500]:
            nation.military.weapons = weapons
            policy = testingpolicy(nation)
            nation.oil = 0
            self.assertFalse(policy.can_apply())
            set_nation(nation, policy.requirements)
            self.assertTrue(policy.can_apply())
            snap = snapshoot(nation)
            policy.enact()
            nation.refresh_from_db()
            nation.military.refresh_from_db()
            self.assertGreater(nation.military.weapons, weapons)
            self.assertGreater(getattr(snap, relations), getattr(nation, relations))


    def test_weapons(self):
        nation = self.subject
        policy = weapons(nation)
        self.assertFalse(policy.can_apply())
        nation.mg = 10
        self.assertFalse(policy.can_apply())
        nation.factories = 2
        self.assertTrue(policy.can_apply())
        nation.save()
        for weaponcount in [10, 900, 2500]:
            nation.military.weapons = weaponcount
            policy = weapons(nation)
            nation.mg = 0
            self.assertFalse(policy.can_apply())
            set_nation(nation, policy.requirements)
            self.assertTrue(policy.can_apply())
            snap = snapshoot(nation)
            policy.enact()
            nation.refresh_from_db()
            nation.military.refresh_from_db()
            self.assertGreater(nation.military.weapons, weaponcount)
            self.assertGreater(snap.mg, nation.mg)


    def test_planes(self):
        self.relation_planes(migs, 'soviet_points')
        self.relation_planes(f8, 'us_points')
        #recycles code
        #IN CASE IT WASN'T OBVIOUS ENOUGH


    def relation_planes(self, testingpolicy, relations):
        nation = nation_generator()[0]
        #default nations do not have the necessary resources to
        #buy planes right out of the gate
        policy = testingpolicy(nation)
        self.assertFalse(policy.can_apply())
        setattr(nation, relations, 100)
        nation.oil = 0
        self.assertFalse(policy.can_apply())
        nation.oil = 100
        self.assertTrue(policy.can_apply())
        nation.alignment = (3 if relations.split('_')[0] == 'soviet' else 1)
        self.assertFalse(policy.can_apply())
        nation.alignment = (1 if relations.split('_')[0] == 'soviet' else 3)
        nation.save()
        snap = snapshoot(nation)
        planes = nation.military.planes
        policy.enact()
        nation.refresh_from_db()
        nation.military.refresh_from_db()
        for cost in policy.cost:
            self.assertGreater(getattr(snap, cost), getattr(nation, cost), msg="%s didn't get subtracted properly" % cost)
        self.assertGreater(nation.military.planes, planes, msg="plane didn't get added")

        #shouldn't be accessible of planes == 10
        nation.military.planes = 10
        nation.military.save()
        policy = testingpolicy(nation)
        set_nation(nation, policy.cost)
        self.assertFalse(policy.can_apply(), msg="Cannot get more at 10 planes")


    def test_planes(self):
        nation = self.subject
        #default nations do not have the necessary resources to
        #buy planes right out of the gate
        policy = aircraft(nation)
        self.assertFalse(policy.can_apply(), msg="Default nations can't make planes")
        nation.mg = 100
        nation.oil = 0
        self.assertFalse(policy.can_apply())
        nation.oil = 100
        self.assertFalse(policy.can_apply())
        nation.factories = 3
        self.assertTrue(policy.can_apply(), msg="100mg, 100oil and 3 faccos can build planes")
        nation.save()
        snap = snapshoot(nation)
        planes = nation.military.planes
        policy.enact()
        nation.refresh_from_db()
        nation.military.refresh_from_db()
        for cost in policy.cost:
            self.assertGreater(getattr(snap, cost), getattr(nation, cost), msg="%s didn't get subtracted properly" % cost)
        self.assertGreater(nation.military.planes, planes, msg="plane didn't get added")

        #shouldn't be accessible of planes == 10
        nation.military.planes = 10
        nation.military.save()
        policy = aircraft(nation)
        set_nation(nation, policy.cost)
        self.assertFalse(policy.can_apply(), msg="Cannot get more at 10 planes")


    def test_navy(self):
        nation = self.subject
        policy = navy(nation)
        self.assertFalse(policy.can_apply())
        nation.mg = 100
        self.assertFalse(policy.can_apply())
        nation.oil = 100
        self.assertFalse(policy.can_apply())
        nation.factories = 2
        self.assertTrue(policy.can_apply())
        nation.save()
        ships = nation.military.navy
        snap = snapshoot(nation)
        print nation.mg
        policy.enact()
        nation.refresh_from_db()
        nation.military.refresh_from_db()
        print nation.mg
        cost_check(self, nation, snap, policy.cost)
        self.assertGreater(nation.military.navy, ships)
        self.assertEqual(nation.military.navy, ships+1)


    def chems(self):
        nation = self.subject
        nation.budget = 0
        policy = chems(nation)
        self.assertFalse(policy.can_apply())
        nation.budget = policy.cost['budget']
        self.assertFalse(policy.can_apply())
        set_nation(nation, policy.requirements)
        self.assertTrue(policy.can_apply())
        snap = snapshoot(nation)
        progress = nation.military.chems
        for x in xrange(1000):
            policy.enact()
            nation.refresh_from_db()
            nation.military.refresh_from_db()
            if nation.military.chems > progress:
                break
            else:
                raise ValueError 
        cost_check(self, nation, snap, policy.cost)