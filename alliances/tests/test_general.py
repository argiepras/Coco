from django.test import TestCase
from nation.models import Alliance
from nation.testutils import nation_generator

class alliance_checks(TestCase):

    def test_creation(self):
        #tests that alliances are created properly
        #that the related models are automatically created
        x = Alliance.objects.create()
        self.check_allianceattrs(x)
        self.assertEqual(alliance.members.count(), 0)
        self.assertEqual(alliance.memberstats.count(), 0)
        self.assertEqual(alliance.permissions.count(), 0)

    def test_foundered_creation(self):
        n = nation_generator()
        x = Alliance.objects.create(founder=n.name)
        check_allianceattrs(x)
        self.assertEqual(alliance.members.count(), 1)
        self.assertEqual(alliance.memberstats.count(), 1)
        self.assertEqual(alliance.permissions.count(), 1)
        self.check_allianceattrs(x)

    def check_allianceattrs(self, alliance):
        self.assertTrue(hasattr(alliance, 'bank'))
        self.assertTrue(hasattr(alliance, 'initiatives'))
        self.assertEqual(alliance.bank_logs.count(), 0)
        self.assertEqual(alliance.bankstats.count(), 1)
        self.assertEqual(alliance.outstanding_invites.count(), 0)
        self.assertEqual(alliance.templates.count(), 3) #founder, officer and member base templates