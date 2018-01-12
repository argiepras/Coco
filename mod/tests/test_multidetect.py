from nation.models import *
from nation.testutils import *
from nation.mod.multidetect import *
import nation.variables as v
from nation.aid import send_aid, give_weapons, expeditionary
from nation.policies.domestic import hospital, school,  medicalresearch
from nation.policies.military import conscript
from nation.tasks import turnchange

from django.test import TestCase
from django.utils import timezone
import random

class multi_tests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Market.objects.create()
        #we need to generate data that emulates actual players
        #or whatever comes close to an actual player
        farmer = nation_generator(1)
        farmed = nation_generator(5)

        normies = nation_generator(20, random=False)
        for x in xrange(1, 20): #going for 20 turns worth of actions
            #first we log in
            logintime = timezone.now() - timezone.timedelta(days=20-x, hours=5)
            for nation in [farmer] + farmed + normies:
                ip = "127.0.0.1"
                logintime += timezone.timedelta(minutes=random.randint(1, 3))
                logouttime = logintime + timezone.timedelta(minutes=random.randint(1, 3))
                nation.login_times.create(timestamp=logintime, IP=ip)
                #then we log out
                nation.logout_times.create(timestamp=logouttime, IP=ip)


            #actions multis might perform is basic maintenance such as building schools/hospitals
            #and making troops
            for farmee in farmed:
                if x % 2: 
                    policies = [conscript(farmee), hospital(farmee), school(farmee), medicalresearch(farmee)]
                    for policy in policies:
                        if policy.can_apply():
                            policy.enact()
            for resource in v.resources:
                for farmee in farmed: #generate aid logs for the multis
                    send_aid(
                        nation=farmee, 
                        target=farmer, 
                        POST={'resource': resource, 'amount': getattr(farmee, resource)}
                    )
                    latest = farmee.outgoing_aid.all().latest()
                    latest.timestamp = logintime
                    latest.save()
                    farmee.outgoing_aidspam.all().delete()


            for i in [farmer] + farmed + normies:
                i.budget += i.gdp * 2
                i.save()

            turnchange()

        cls.farmer = farmer
        cls.farmed = farmed
        cls.normie = normies[0]



    def test_tradecheck_positive(self):
        a = self.farmer
        current_balance = a.multimeter.trade_balance
        trade_balance_check(a)
        self.assertGreater(a.multimeter.trade_balance, current_balance)

    def test_tradecheck_negative(self):
        a = self.farmed[0]
        current_balance = a.multimeter.trade_balance
        trade_balance_check(a)
        self.assertGreater(a.multimeter.trade_balance, current_balance)

    def test_tradecheck_balanced(self):
        a = self.normie
        current_balance = a.multimeter.trade_balance
        trade_balance_check(a)
        self.assertLess(a.multimeter.trade_balance, current_balance)        

    def test_tradebalance_changes(self):
        #since the simulated multis send out everything not used for maintenance
        #expected result is a lowering of the multimeter trade balance value
        subject = self.farmed[0]
        current_balance = subject.multimeter.trade_balance
        trade_balance_changes(subject)
        self.assertLess(subject.multimeter.trade_balance, current_balance)



    def test_bp(self):
        prod = Nation.objects.all().order_by('?')[0]
        prod = base_production(prod)
        self.assertGreater(prod, 0)


    def test_logincheck(self):
        subject = self.farmed[0]
        self.assertEqual(subject.multimeter.logins, 50)
        self.assertEqual(subject.multimeter.logouts, 50)
        self.assertEqual(self.normie.multimeter.logins, 50)
        self.assertEqual(self.normie.multimeter.logouts, 50)
        compare_logins(subject)
        compare_logins(self.normie)
        self.assertGreater(subject.multimeter.logins, 50)
        self.assertGreater(subject.multimeter.logouts, 50)
        self.assertLess(self.normie.multimeter.logins, 50)
        self.assertLess(self.normie.multimeter.logouts, 50)


    def test_outgoing_aid_volume(self):
        subject = self.farmed[0]
        count = subject.notes.all().count()
        current_aid = subject.multimeter.aid
        outgoing_aid_check_volume(subject)
        self.assertGreater(subject.multimeter.aid, current_aid)
        self.assertGreater(subject.notes.all().count(), count)

        current_aid = self.normie.multimeter.aid
        outgoing_aid_check_volume(self.normie)
        self.assertLess(self.normie.multimeter.aid, current_aid)
        self.assertEqual(self.normie.notes.all().count(), 0)


    def test_outgoing_aid_value(self):
        subject = self.farmed[0]
        count = subject.notes.all().count()
        current_aid = subject.multimeter.aid
        outgoing_aid_by_value(subject)
        self.assertGreater(subject.multimeter.aid, current_aid)
        self.assertGreater(subject.notes.all().count(), count)

        current_aid = self.normie.multimeter.aid
        outgoing_aid_by_value(self.normie)
        self.assertLess(self.normie.multimeter.aid, current_aid)
        self.assertEqual(self.normie.notes.all().count(), 0)


    def test_incoming_aid(self):
        subject = self.farmer
        current_aid = subject.multimeter.aid
        incoming_aid_check(subject)
        self.assertGreater(subject.multimeter.aid, current_aid)

        current_aid = self.normie.multimeter.aid
        incoming_aid_check(self.normie)
        self.assertLess(self.normie.multimeter.aid, current_aid)
        self.assertEqual(self.normie.notes.all().count(), 0)