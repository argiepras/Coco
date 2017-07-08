from django.test import TestCase
from nation.testutils import *
from nation.models import *
from nation.alliances.memberactions import *
from nation.alliances.officeractions import *
import nation.variables as v



class generaltests(TestCase):
    def setUp(self):
        self.subject = nation_generator()
        self.alliance = alliance_generator(self.subject)