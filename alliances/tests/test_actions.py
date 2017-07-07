from django.test import TestCase
from nation.testutils import *
from nation.models import *
from nation.policies.domestic import *
import nation.variables as v



class generaltests(TestCase):
    def setUp(self):
        self.subject = nation_generator()