from django.test import TestCase, Client
from nation.testutils import *
from nation.models import *
from nation.policies.foreign import *
import nation.variables as v
from nation.policies.economic import Policy
from nation.policies.views import get_policies
import nation.policies.foreign
import nation.policies.military
import nation.policies.domestic


class generaltests(TestCase):
    @classmethod
    def setUpTestData(self):
        self.subject = nation_generator()
        self.subject.user.set_password('password')
        self.subject.user.save()
        Market.objects.get_or_create()

    def test_htmlattrs(self):
        #check if they contain the necessary description, button names
        #and names and whatnot
        Market.objects.get_or_create()
        for policyname in Policy.registry:
            policy = Policy.registry[policyname](self.subject)
            self.assertNotEqual(policy.description, '', msg='%s need a valid description' % policyname)
            self.assertNotEqual(policy.name, '', msg='%s need a valid name' % policyname)
            self.assertNotEqual(policy.button, '', msg='%s needs a button name' % policyname)
            self.assertNotEqual(policy.render_cost(), '', msg="%s cost shouldn't be emptystring" % policyname)


    def test_policygetting(self):
        for ptype in ['economic', 'military', 'foreign', 'domestic']:
            policies = get_policies(Policy.registry, self.subject, ptype)
            for policy in policies:
                self.assertNotEqual(policy.description, '', msg="%s should have a description" % policy.name)
                self.assertNotEqual(policy.button, '', msg="%s should have a button" % policy.name)
                self.assertFalse(hasattr(policy, 'error'), msg="Should be errors, not error")
                self.assertTrue(policy.can_apply() or policy.contextual == False, msg="%s shouldn't be included" % policy.name)


    def test_views(self):
        c = Client(HTTP_USER_AGENT='Mozilla/5.0')
        c.post('/login/', {'username': self.subject.user.username, 'password': 'password'})
        self.assertEqual(c.get('/main/economic/').status_code, 200)
        self.assertEqual(c.get('/main/domestic/').status_code, 200)
        self.assertEqual(c.get('/main/military/').status_code, 200)
        self.assertEqual(c.get('/main/foreign/').status_code, 200)



class policy_tests(TestCase):
    @classmethod
    def setUpTestData(self):
        Market.objects.get_or_create()
        subjects = nation_generator(3)
        for subject, x in zip(subjects, [20, 50, 80]):
            for attr in Nationattrs._meta.fields:
                setattr(subject, attr.name, 0)
            subject.alignment = 2
            subject.economy = x
            subject.save()

        self.subjects = subjects


    def test_results_commie(self):
        for subject in self.subjects:
            subject.alignment = 1
        self.check_results()


    def test_results_neutral(self):
        self.check_results()


    def test_results_ameribear(self):
        for subject in self.subjects:
            subject.alignment = 3
        self.check_results()


    def check_results(self):
        for subject in self.subjects:
            for ptype in ['economic', 'military', 'foreign', 'domestic']:
                policies = get_policies(Policy.registry, subject, ptype)
                for policy in policies:
                    if policy.can_apply():
                        policy.enact()
                    self.assertNotEqual(policy.result, '', msg="%s should have a nonempty result" % policy.name)
                    self.assertNotEqual(policy.result, ' is too low!', msg="%s should have a legit result" % policy.name)