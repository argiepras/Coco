from django.test import TestCase
from nation.models import *
from nation.views import *
from nation.testutils import nation_generator, snapshoot
from django.utils import timezone


class ground_tests(TestCase):
    def setUp(self):
        self.attacker = nation_generator()
        self.attacker.military.army = 30
        self.attacker.military.weapons = 50
        self.attacker.military.save()
        self.defender = nation_generator()
        self.defender.military.army = 20
        self.defender.military.weapons = 50
        self.defender.military.save()
        self.war = War.objects.create(attacker=self.attacker, defender=self.defender)

    def test_groundassault(self):
        battle(self.attacker, self.defender, self.war)
        refresh(self)
        self.assertGreater(20, self.defender.military.army)
        self.assertGreater(50, self.attacker.military.weapons)
        self.assertGreater(self.attacker.land, self.defender.land)
        self.assertEqual(self.defender.news.all().count(), 1)
        self.assertTrue(self.war.attacks.all().exists())
        self.assertEqual(Loss.objects.all().count(), 1, msg="Losses are army guys")
        self.assertEqual(Wargains.objects.all().count(), 1)

    def test_warwin(self):
        self.defender.military.army = 5
        self.defender.military.save()
        war_win(self.attacker, self.defender, self.war)
        refresh(self)
        self.assertEqual(self.defender.military.army, 10)
        self.assertTrue(Wargains.objects.all().exists())

        self.war.refresh_from_db()
        self.assertTrue(self.war.over)
        self.assertEqual(self.war.winner, self.attacker.name)
        self.assertEqual(self.defender.news.all().count(), 1)
        self.assertGreater(self.defender.protection, timezone.now())


class naval_tests(TestCase):
    def setUp(self):
        self.attacker = nation_generator()
        self.attacker.military.navy = 30
        self.attacker.military.weapons = 50
        self.attacker.military.save()
        self.defender = nation_generator()
        self.defender.military.navy = 30
        self.defender.military.army = 20
        self.defender.military.weapons = 50
        self.defender.military.save()
        self.war = War.objects.create(attacker=self.attacker, defender=self.defender)


    def test_shore_bombardment(self):
        self.defender.military.navy = 0
        navalstrike(self.attacker, self.defender, self.war)
        refresh(self)
        self.assertEqual(self.war.attacks.all().count(), 1)
        self.assertTrue(Loss.objects.filter(loss_type="army").exists())
        self.assertEqual(self.war.attacks.all()[0].attack_type, "naval")
        self.assertEqual(self.war.attacks.all()[0].lost, 0)
        self.assertEqual(self.war.attacks.all().count(), 1)
        self.assertEqual(self.war.attacks.all()[0].attacker, self.attacker)
        self.assertGreater(20, self.defender.military.army)
        self.assertEqual(self.defender.news.all().count(), 1)


    def test_naval_battle(self):
        navalstrike(self.attacker, self.defender, self.war)
        refresh(self)
        self.assertEqual(self.war.attacks.all().count(), 1)
        self.assertTrue(Loss.objects.filter(loss_type="navy").exists())
        self.assertEqual(self.war.attacks.all()[0].attack_type, "naval")
        self.assertNotEqual(self.war.attacks.all()[0].lost, 0)
        self.assertEqual(self.war.attacks.all().count(), 1)
        self.assertEqual(self.war.attacks.all()[0].attacker, self.attacker)
        self.assertGreater(30, self.defender.military.navy)
        self.assertEqual(self.defender.news.all().count(), 1)


class air_tests(TestCase):
    def setUp(self):
        self.attacker = nation_generator()
        self.defender = nation_generator()
        self.attacker.military.planes = 10
        self.attacker.military.save()
        self.defender.military.planes = 1
        self.defender.military.navy = 1
        self.defender.wells = 1
        self.defender.factories = 1
        self.defender.military.chems = 10
        self.defender.save()
        self.defender.military.save()
        self.war = War.objects.create(attacker=self.attacker, defender=self.defender)

    def test_airbattle(self):
        self.attack(airbattle)
        self.assertEqual(self.defender.military.planes, 0)

    def test_ground_bombing(self):
        self.attack(groundbombing)
        self.assertGreater(20, self.defender.military.army)

    def test_city_bombing(self):
        self.attack(citybombing)
        self.assertEqual(self.defender.manpower, 90)
        self.assertGreater(nation_generator().qol, self.defender.qol)

    def test_naval_bombing(self):
        self.attack(navalbombing)
        self.assertEqual(self.defender.military.navy, 0)
        self.assertEqual(self.war.attacks.all()[0].kills.all()[0].amount, 1)

    def test_industry_bombing(self):
        self.attack(industrybombing)
        self.assertEqual(self.defender.factories, 0)

    def test_econbombing(self):
        x = snapshoot(self.defender)
        self.attack(econbombing)
        self.assertGreater(x.gdp, self.defender.gdp)
        self.assertGreater(x.growth, self.defender.growth)

    def test_oilbombing(self):
        self.attack(oilbombing)
        self.assertEqual(self.defender.wells, 0)
        self.assertEqual(Loss.objects.get().amount, 1)

    def test_chembombing(self):
        self.attack(chembombing)
        self.assertEqual(self.defender.military.chems, 8)

    def test_farmbombing(self):
        self.attack(agentorange)
        self.assertEqual(self.defender.econdata.foodproduction, 0)

    def attack(self, func):
        q = snapshoot(self.attacker)
        x = func(self.attacker, self.defender, self.war)
        self.assertFalse("defeated" in x['result'])
        refresh(self)
        self.assertGreater(q.oil, self.attacker.oil)
        self.base_tests()

    def base_tests(self):
        self.assertEqual(self.war.attacks.all().count(), 1)
        self.assertTrue(self.war.attacks.filter(attack_type="air").exists())
        self.assertEqual(self.defender.news.all().count(), 1)






def refresh(self):
    self.attacker.refresh_from_db()
    self.defender.refresh_from_db()
    self.attacker.military.refresh_from_db()
    self.defender.military.refresh_from_db()
    self.attacker.econdata.refresh_from_db()
    self.defender.econdata.refresh_from_db()
