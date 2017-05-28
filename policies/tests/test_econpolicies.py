from django.test import TestCase
from nation.testutils import *
from nation.models import *
from nation.policies.economic import *
import nation.variables as v


class policytests(TestCase):
    def setUp(self):
        self.subject = nation_generator()[0]

    def test_great_leap(self):
        #a newly created nation is unable to do GP
        #because wrong econ
        nation = self.subject
        nation.economy = 90
        gl = great_leap(nation)
        self.assertEqual(gl.can_apply(), False)
        self.assertEqual(gl.result, '')
        for field in gl.requirements:
            nation.__dict__[field] = gl.requirements[field]

        gl = great_leap(nation)
        self.assertEqual(gl.can_apply(), False) #econ still wrong

        nation.economy = 50 #necessary because it's a property
        nation.budget = 500
        nation.growth = 0
        nation.rm = 10
        nation.save()
        self.assertEqual(gl.can_apply(), True)
        gl()
        self.assertNotEqual(gl.result, '')
        #check if cost is subtracted properly
        nation.refresh_from_db()
        self.assertEqual(nation.budget, 500 - gl.cost['budget'])
        self.assertEqual(nation.rm, 10 - gl.cost['rm'])


    def test_reactors(self):
        nation = self.subject
        progress = nation.military.reactor
        policy = reactor(nation)
        self.assertNotEqual(nation.budget, policy.cost['budget'])
        self.assertFalse(policy.can_apply())
        while True:
            set_nation(nation, policy.cost)
            nation.save()
            self.assertTrue(policy.can_apply())
            policy()
            nation.refresh_from_db()
            nation.military.refresh_from_db()
            if 'continues' in policy.result:
                self.assertGreater(nation.military.reactor, progress)
                break
            continue
        for field in policy.cost:
            self.assertEqual(getattr(nation, field), 0)
        self.assertNotEqual(policy.result, '')


    def test_blood_diamonds(self):
        nation = self.subject
        policy = blood(nation)
        nation.subregion = 'The Andes'
        self.assertFalse(policy.can_apply())
        nation.subregion = 'Ethiopia'
        budget = nation.budget
        self.assertTrue(policy.can_apply())
        policy()
        nation.refresh_from_db()
        self.assertNotEqual(policy.result, '')
        self.assertEqual(nation.budget, budget + policy.gain['budget'])


    def test_drugs_smuggling(self):
        nation = self.subject
        nation.subregion = "Ethiopia"
        policy = drugs(nation)
        self.assertFalse(policy.can_apply())
        nation.subregion = "The Andes"
        policy = drugs(nation)
        self.assertTrue(policy.can_apply())
        while True:
            x = nation.econdata
            budget = nation.budget
            reputation = nation.reputation
            policy()
            nation.refresh_from_db()
            if 'Miami' in policy.result: #success!
                self.assertEqual(nation.budget, budget+policy.high['budget'])
                break
            else:
                if nation.reputation > 0:
                    self.assertGreater(reputation, nation.reputation)
                else:
                    self.assertEqual(nation.reputation, 0)

    def test_collectivization(self):
        nation = self.subject
        nation.qol = 20
        nation.approval = 20
        #requirements are 30 30
        policy = collectivization(nation)
        self.assertFalse(policy.can_apply())
        set_nation(nation, policy.requirements)
        nation.economy = 20
        self.assertTrue(policy.can_apply())
        failure = success = False
        while not failure and not success:
            #testing that food production is set correctly
            #because it's a random chance
            #it needs to be looped over for thorough testing
            foodproduction = nation.econdata.foodproduction
            qol = nation.qol
            approval = nation.approval
            policy()
            nation.refresh_from_db()
            nation.econdata.refresh_from_db()
            self.assertEqual(qol, nation.qol + policy.cost['qol'])
            self.assertEqual(approval, nation.approval + policy.cost['approval'])
            if 'grainer' in policy.result:
                success = True
                self.assertGreater(nation.econdata.foodproduction, foodproduction)
            elif 'disaster' in policy.result:
                failure = True
                if foodproduction > 0:
                    self.assertGreater(foodproduction, nation.econdata.foodproduction)
                else: #must not go below 0
                    self.assertEqual(foodproduction, nation.econdata.foodproduction)
            set_nation(nation, policy.requirements)
            nation.save()


    def test_labordiscipline(self):
        nation = self.subject
        nation.factories = 10
        nation.mg = 0
        nation.oil = 5
        nation.save()
        policy = labordiscipline(nation)
        self.assertFalse(policy.can_apply())
        set_nation(nation, policy.requirements)
        self.assertTrue(policy.can_apply())
        policy()
        self.assertEqual(nation.mg, 10)
        nation.econdata.refresh_from_db()
        self.assertEqual(nation.econdata.labor, 2)

        #now we test with research added
        set_nation(nation, policy.requirements)
        nation.mg = 0
        nation.researchdata.industrialtech = 5 #+50%
        #have to create a new instance for the research
        #modifiers to have an effect
        policy = labordiscipline(nation)
        policy()
        nation.refresh_from_db()
        self.assertEqual(15, nation.mg)


    def test_industrialize(self):
        nation = self.subject
        nation.factories = 10
        nation.rm = 5
        policy = industrialize(nation)
        self.assertFalse(policy.can_apply())
        set_nation(nation, policy.requirements)
        self.assertTrue(policy.can_apply())
        nation.mines = nation.wells = 0
        nation.land = 10000 #no land left
        self.assertFalse(policy.can_apply())
        nation.land = 20000
        policy()
        nation.refresh_from_db()
        self.assertEqual(nation.factories, 11)
        self.assertEqual(nation.rm, 0)
        self.assertEqual(nation.oil, 0)
        self.assertEqual(nation.mg, 0)


    def test_deindustrialize(self):
        nation = self.subject
        nation.factories = 0
        policy = deindustrialize(nation)
        self.assertFalse(policy.can_apply())
        set_nation(nation, policy.requirements)
        self.assertTrue(policy.can_apply())
        policy()
        nation.refresh_from_db()
        for field in policy.requirements:
            if field == 'approval': #should be 5 and not 0
                self.assertEqual(getattr(nation, field), 5)
            else:
                self.assertEqual(getattr(nation, field), 0)


    def test_reindustrialize(self):
        nation = self.subject
        nation.factories = 0
        policy = reindustrialize(nation)
        self.assertFalse(policy.can_apply())
        set_nation(nation, policy.requirements)
        self.assertTrue(nation.budget, policy.requirements['budget'])
        self.assertNotEqual(nation.budget, 0)
        self.assertTrue(policy.can_apply())
        policy()
        nation.refresh_from_db()
        self.assertEqual(nation.closed_factories, 0)
        self.assertEqual(nation.factories, 1)
        self.assertEqual(nation.budget, 0)


    def test_nationalize(self):
        nation = self.subject
        policy = nationalize(nation)
        self.assertGreater(20, nation.FI)
        self.assertFalse(policy.can_apply())
        nation.economy = 60
        nation.FI = 500
        nation.budget = 0
        nation.save()
        policy = nationalize(nation) #new FI means new instance
        self.assertTrue(policy.can_apply())
        policy()
        nation.refresh_from_db()
        nation.econdata.refresh_from_db()
        self.assertEqual(nation.budget, 500)
        self.assertEqual(nation.FI, 0)
        self.assertEqual(nation.economy, 10)
        self.assertEqual(nation.econdata.nationalize, 1)


    def test_privatize(self):
        nation = self.subject
        nation.economy = 100
        policy = privatize(nation)
        self.assertFalse(policy.can_apply())
        nation.economy = 50
        budget = nation.budget
        gdp = nation.gdp
        self.assertTrue(policy.can_apply())
        policy()
        nation.refresh_from_db()
        nation.econdata.refresh_from_db()
        self.assertEqual(nation.budget, budget + policy.gain['budget'])
        self.assertEqual(gdp, nation.gdp + policy.cost['gdp'])
        self.assertEqual(nation.econdata.nationalize, 1)
        self.assertNotEqual(utils.econsystem(nation.economy), utils.econsystem(50))


    def test_prospect(self):
        nation = self.subject
        nation.oilreserves = 0
        nation.budget = 0
        policy = prospect(nation)
        self.assertFalse(policy.can_apply())
        set_nation(nation, policy.requirements)
        self.assertGreater(nation.budget, 0)
        self.assertTrue(policy.can_apply())
        policy()
        nation.refresh_from_db()
        self.assertGreater(nation.oilreserves, 0)
        self.assertEqual(nation.budget, 0)

        #check that ME cost reduction works
        cost = policy.cost['budget']
        oilgain = policy.gain['oilreserves']
        nation.subregion = 'Arabia'
        MEcost = prospect(nation).cost['budget']
        MEgain = prospect(nation).gain['oilreserves']
        self.assertGreater(cost, MEcost)
        self.assertGreater(MEgain, oilgain)

    def test_imf(self):
        nation = self.subject
        policy = imf(nation)
        nation.alignment = 0
        budget = nation.budget
        self.assertFalse(policy.can_apply())
        set_nation(nation, policy.requirements)
        self.assertTrue(policy.can_apply())
        policy()
        nation.refresh_from_db()
        self.assertEqual(nation.growth, policy.requirements['growth'] - policy.cost['growth'])
        self.assertGreater(nation.budget, budget)
