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
        Market.objects.get_or_create()
        for ptype in ['economic', 'military', 'foreign', 'domestic']:
            policies = get_policies(Policy.registry, self.subject, ptype)
            for policy in policies:
                self.assertTrue(policy.can_apply() or policy.contextual == False, msg="%s shouldn't be included" % policy.name)


    def test_views(self):
        c = Client(HTTP_USER_AGENT='Mozilla/5.0')
        c.post('/login/', {'username': self.subject.user.username, 'password': 'password'})
        self.assertEqual(c.get('/main/economic/').status_code, 200)
        self.assertEqual(c.get('/main/domestic/').status_code, 200)
        self.assertEqual(c.get('/main/military/').status_code, 200)
        self.assertEqual(c.get('/main/foreign/').status_code, 200)