from django.test import TestCase
from nation.testutils import *
from nation.models import *
from nation.policies.foreign import *
import nation.variables as v


class generaltests(TestCase):
    def setUp(self):
        self.subject = nation_generator()


    def test_htmlattrs(self):
        from nation.policies.economic import Policy
        import nation.policies.foreign
        import nation.policies.military
        import nation.policies.domestic
        #check if they contain the necessary description, button names
        #and names and whatnot
        Market.objects.get_or_create()
        for policyname in Policy.registry:
            policy = Policy.registry[policyname](self.subject)
            self.assertNotEqual(policy.description, '', msg='%s need a valid description' % policyname)
            self.assertNotEqual(policy.name, '', msg='%s need a valid name' % policyname)
            self.assertNotEqual(policy.button, '', msg='%s needs a button name' % policyname)
            self.assertNotEqual(policy.render_cost(), '', msg="%s cost shouldn't be emptystring" % policyname)

