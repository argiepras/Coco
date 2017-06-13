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
        gl.enact()
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
            policy.enact()
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
        policy.enact()
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
            policy.enact()
            nation.refresh_from_db()
            if 'Miami' in policy.result: #success!
                self.assertEqual(nation.budget, budget+policy.gain['budget'])
                break
            else:
                if nation.reputation > 0:
                    self.assertGreater(reputation, nation.reputation)
                else:
                    self.assertEqual(nation.reputation, 0)
            policy = drugs(nation)


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
            policy.enact()
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
        nations = nation_generator(3)
        zero = nations[0]
        one = nations[1]
        ten = nations[2]
        zero.factories = 0
        one.factories = 1
        ten.factories = 10
        #First as assert that the 0 facco guy is ineligible
        #as it requires at least 1 factory
        policy = labordiscipline(zero)
        self.assertFalse(policy.can_apply())
        #then to 1 facco
        one.rm = 0
        policy = labordiscipline(one)
        self.assertFalse(policy.can_apply())
        set_nation(one, policy.requirements)
        one.oil = 0
        self.assertFalse(policy.can_apply())
        set_nation(one, policy.requirements)
        self.assertTrue(policy.can_apply())
        one.factories = 0
        self.assertFalse(policy.can_apply())
        set_nation(one, policy.requirements)
        policy.enact()
        self.assertEqual(one.mg, 1)
        one.econdata.refresh_from_db()
        self.assertEqual(one.econdata.labor, 2)

        #now we test with research added
        ten.mg = 0
        ten.researchdata.industrialtech = 5 #+50%
        #have to create a new instance for the research
        #modifiers to have an effect
        policy = labordiscipline(ten)
        set_nation(ten, policy.cost)
        snap = snapshoot(ten)
        #1 facco is a requirement
        #and such set_nation sets faccos to 1
        policy.enact()
        ten.refresh_from_db()
        cost_check(self, ten, snap, policy.cost)
        self.assertEqual(15, ten.mg)


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
        policy.enact()
        nation.refresh_from_db()
        self.assertEqual(nation.factories, 11)
        self.assertEqual(nation.rm, 0)
        self.assertEqual(nation.oil, 0)
        self.assertEqual(nation.mg, 0)

        #check that closed factories are counted as well
        policy = industrialize(nation)
        cost = policy.cost
        nation.closed_factories = 1
        policy = industrialize(nation) #have grab a new instance
        #because cost is calculated at creation
        for field in cost:
            self.assertNotEqual(cost[field], policy.cost[field])


    def test_deindustrialize(self):
        nation = self.subject
        nation.factories = 0
        policy = deindustrialize(nation)
        self.assertFalse(policy.can_apply())
        set_nation(nation, policy.requirements)
        self.assertTrue(policy.can_apply())
        policy.enact()
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
        policy.enact()
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
        policy.enact()
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
        policy.enact()
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
        policy.enact()
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
        policy.enact()
        nation.refresh_from_db()
        self.assertEqual(nation.growth, policy.requirements['growth'] - policy.cost['growth'])
        self.assertGreater(nation.budget, budget)


    def test_humanitarian(self):
        nation = self.subject
        growth = nation.growth
        policy = humanitarian(nation)
        nation.gdp = 350
        self.assertFalse(policy.can_apply())
        set_nation(nation, policy.requirements)
        nation.gdp = 200
        self.assertTrue(policy.can_apply())
        policy.enact()
        nation.refresh_from_db()
        self.assertEqual(nation.budget, 0)
        self.assertGreater(nation.growth, growth)


    def test_foreigninvestment(self):
        nation = self.subject
        nation.budget = 0
        nation.rm = 0
        nation.economy = 0
        policy = foreigninvestment(nation)
        self.assertFalse(policy.can_apply())
        set_nation(nation, policy.requirements)
        self.assertFalse(policy.can_apply())
        nation.economy = 50
        self.assertTrue(policy.can_apply())
        success = failure = False
        while not success and not failure:
            set_nation(nation, policy.requirements)
            policy.enact()
            nation.refresh_from_db()
            if 'trickles' in policy.result:
                self.assertGreater(nation.FI, 0)
                self.assertGreater(nation.growth, 0)
                success = True
            elif 'unfortunately' in policy.result:
                self.assertGreater(nation.FI, 0)
                failure = True
            nation.FI = nation.growth = 0
            nation.save()


    def test_mine(self):
        nation = self.subject
        nation.budget = 0
        nation.subregion = 'China'
        policy = mine(nation)
        self.assertFalse(policy.can_apply())
        set_nation(nation, policy.requirements)
        self.assertTrue(policy.can_apply())
        #check of land costs are respected
        nation.land = 400
        self.assertFalse(policy.can_apply())
        nation.land = 30000
        minecost = policy.cost['budget']
        nation.subregion = 'Nigeria'
        africost = mine(nation).cost['budget']
        self.assertGreater(minecost, africost)
        mines = nation.mines
        policy.enact()
        nation.refresh_from_db()
        self.assertEqual(nation.budget, 0)
        self.assertEqual(nation.mines, mines + 1)


    def test_closemine(self):
        nation = self.subject
        nation.mines = 0
        policy = closemine(nation)
        self.assertFalse(policy.can_apply())
        set_nation(nation, policy.requirements)
        approval = nation.approval
        mines = nation.mines
        closed_mines = nation.closed_mines
        self.assertTrue(policy.can_apply())
        policy.enact()
        nation.refresh_from_db()
        self.assertEqual(nation.mines, mines - 1)
        self.assertEqual(nation.closed_mines, closed_mines + 1)
        self.assertGreater(approval, nation.approval)
        self.assertEqual(nation.approval, approval - policy.cost['approval'])


    def test_openmine(self):
        nation = self.subject
        nation.closed_mines = 0
        policy = openmine(nation)
        self.assertFalse(policy.can_apply())
        set_nation(nation, policy.requirements)
        self.assertTrue(policy.can_apply())
        mines = nation.mines
        #check of land costs are respected
        nation.land = 400
        self.assertFalse(policy.can_apply())
        nation.land = 30000
        policy.enact()
        nation.refresh_from_db()
        self.assertEqual(nation.closed_mines, 0)
        self.assertGreater(nation.mines, mines)
        self.assertEqual(nation.mines, mines + 1)
        self.assertEqual(nation.budget, 0)


    def test_privatemine(self):
        nation = self.subject
        nation.FI = 0
        nation.subregion = 'China'
        mines = nation.mines
        #FI = 0 lol

        policy = privatemine(nation)
        self.assertFalse(policy.can_apply())
        set_nation(nation, policy.requirements)
        nation.economy = 10 #commies not allowed
        self.assertFalse(policy.can_apply())
        nation.economy = 80
        self.assertTrue(policy.can_apply())
        #check of land costs are respected
        nation.land = 400
        self.assertFalse(policy.can_apply())
        nation.land = 30000

        policy.enact()
        nation.refresh_from_db()
        self.assertEqual(nation.FI, 0)
        regcost = policy.cost['FI']
        nation.subregion = "Ethiopia"
        afcost = privatemine(nation).cost['FI']
        self.assertGreater(regcost, afcost)
        self.assertGreater(nation.mines, mines)


    def test_well(self):
        nation = self.subject
        nation.budget = 0
        nation.subregion = 'China'
        policy = well(nation)
        self.assertFalse(policy.can_apply())
        set_nation(nation, policy.requirements)
        self.assertTrue(policy.can_apply())
        #check of land costs are respected
        nation.land = 400
        self.assertFalse(policy.can_apply())
        nation.land = 30000
        wellcost = policy.cost['budget']
        nation.subregion = 'Arabia'
        MEcost = well(nation).cost['budget']
        self.assertGreater(wellcost, MEcost)
        wells = nation.wells
        policy.enact()
        nation.refresh_from_db()
        self.assertEqual(nation.budget, 0)
        self.assertEqual(nation.wells, wells + 1)


    def test_privatewell(self):
        nation = self.subject
        nation.FI = 0
        nation.subregion = 'China'
        wells = nation.wells
        #FI = 0 lol

        policy = privatewell(nation)
        self.assertFalse(policy.can_apply())
        set_nation(nation, policy.requirements)
        nation.economy = 10 #commies not allowed
        self.assertFalse(policy.can_apply())
        nation.economy = 80
        self.assertTrue(policy.can_apply())
        #check of land costs are respected
        nation.land = 400
        self.assertFalse(policy.can_apply())
        nation.land = 30000

        policy.enact()
        nation.refresh_from_db()
        self.assertEqual(nation.FI, 0)
        regcost = policy.cost['FI']
        nation.subregion = "Arabia"
        MEcost = privatemine(nation).cost['FI']
        self.assertGreater(regcost, MEcost)
        self.assertGreater(nation.wells, wells)


    def test_closewell(self):
        nation = self.subject
        nation.wells = 0
        policy = closewell(nation)
        self.assertFalse(policy.can_apply())
        set_nation(nation, policy.requirements)
        approval = nation.approval
        wells = nation.wells
        closed_wells = nation.closed_wells
        self.assertTrue(policy.can_apply())
        policy.enact()
        nation.refresh_from_db()
        self.assertEqual(nation.wells, wells - 1)
        self.assertEqual(nation.closed_wells, closed_wells + 1)
        self.assertGreater(approval, nation.approval)
        self.assertEqual(nation.approval, approval - policy.cost['approval'])


    def test_openwell(self):
        nation = self.subject
        nation.closed_wells = 0
        policy = openwell(nation)
        self.assertFalse(policy.can_apply())
        set_nation(nation, policy.requirements)
        self.assertTrue(policy.can_apply())
        wells = nation.wells
        #check of land costs are respected
        nation.land = 400
        self.assertFalse(policy.can_apply())
        nation.land = 30000
        policy.enact()
        nation.refresh_from_db()
        self.assertEqual(nation.closed_wells, 0)
        self.assertGreater(nation.wells, wells)
        self.assertEqual(nation.wells, wells + 1)
        self.assertEqual(nation.budget, 0)


    def test_forced(self):
        nation = self.subject
        nation.government = 60
        policy = forced(nation)
        self.assertFalse(policy.can_apply())
        nation.government = 10
        set_nation(nation, policy.requirements)
        self.assertTrue(policy.can_apply())
        snap = snapshoot(nation)
        policy.enact()
        nation.refresh_from_db()
        if 'improved' in policy.result:
            self.assertEqual(nation.growth, snap.growth + policy.gain['growth'])
        cost_check(self, nation, snap, policy.cost)


    def test_sez(self):
        nation = self.subject
        nation.subregion = "Arabia"
        Market.objects.create()
        policy = sez(nation)
        self.assertFalse(policy.can_apply())
        nation.subregion = 'China'
        self.assertTrue(policy.can_apply())
        set_nation(nation, policy.requirements)
        snap = snapshoot(nation)
        self.assertTrue(policy.can_apply())
        policy.enact()
        cost_check(self, nation, snap, policy.cost)
