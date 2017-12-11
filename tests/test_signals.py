from django.test import TestCase

from nation.models import Alliance, Nation
from nation.testutils import nation_generator


class checkalliance(TestCase):

    def test_dummy_alliance(self):
        a = Alliance.objects.create()
        self.base_test(a)
        self.assertEqual(a.founder, 'admin')

    def test_founded_alliance(self):
        subject = nation_generator()
        alliance = Alliance.objects.create(founder=subject.name)
        self.base_test(alliance)
        self.assertEqual(alliance.members.all().count(), 1)
        self.assertEqual(alliance.permissions.all().count(), 1)
        self.assertEqual(alliance.memberstats.all().count(), 1
            )

    def base_test(self, alliance):
        self.assertTrue(alliance.initiatives)
        self.assertTrue(alliance.initiatives.timers)
        self.assertTrue(alliance.bank)
        self.assertEqual(alliance.templates.all().count(), 3, msg="Should be founder officer and members")


class checknation(TestCase):
    def test_creation(self):
        a = Nation.objects.create()
        self.assertTrue(a.econdata)
        self.assertTrue(a.settings)
        self.assertTrue(a.military)
        self.assertTrue(a.researchdata)
        self.assertTrue(a.multimeter)
        self.assertGreater(a.news.all().count(), 0)
