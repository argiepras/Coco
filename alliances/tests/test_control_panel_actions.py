from django.test import TestCase
from nation.models import Alliance
from nation.testutils import nation_generator, alliance_generator

class membertests(Testcase):
    def setUp(self):
        self.alliance = alliance_generator(members=10, officers=5)
