from django.test import TestCase
from nation.models import Alliance
from nation.testutils import nation_generator

class alliance_checks(TestCase):

    def test_creation(self):
        #tests that alliances are created properly
        #that the related models are automatically created
        alliance = Alliance.objects.create()
        self.check_allianceattrs(alliance)
        self.assertEqual(alliance.members.count(), 0)
        self.assertEqual(alliance.memberstats.count(), 0)
        self.assertEqual(alliance.permissions.count(), 0)

    def test_foundered_creation(self):
        n = nation_generator()
        alliance = Alliance.objects.create(founder=n.name)
        self.check_allianceattrs(alliance)
        self.assertEqual(alliance.members.count(), 1)
        self.assertEqual(alliance.memberstats.count(), 1)
        self.assertEqual(alliance.permissions.count(), 1)
        self.check_allianceattrs(alliance)

    def check_allianceattrs(self, alliance):
        self.assertTrue(hasattr(alliance, 'bank'))
        self.assertTrue(hasattr(alliance, 'initiatives'))
        self.assertEqual(alliance.bank_logs.count(), 0)
        self.assertEqual(alliance.bankstats.count(), 1)
        self.assertEqual(alliance.outstanding_invites.count(), 0)
        self.assertEqual(alliance.templates.count(), 3) #founder, officer and member base templates

    def test_notification_squad(self):
        founder = nation_generator()
        alliance = Alliance.objects.create(founder=founder.name)
        members = nation_generator(20)
        for member in members:
            alliance.add_member(member)

        invite_officers = nation_generator(5)
        application_officers = nation_generator(5)
        bothlol_officers = nation_generator(5)
        
        invite_template = alliance.templates.create(invite=True, rank=3)
        application_template = alliance.templates.create(applicants=True, rank=3)
        both_template = alliance.templates.create(invite=True, applicants=True, rank=3)

        for a, b, c in zip(invite_officers, application_officers, bothlol_officers):
            for officer, template in zip([a, b, c], [invite_template, application_template, both_template]):
                alliance.add_member(officer)
                officer.permissions.template = template
                officer.permissions.save()

        self.assertEqual(alliance.members.filter(permissions__template__rank__lt=5).count(), 16, msg="Should have 15 officers and 1 founder")
        self.assertEqual(alliance.notification_squad('invite').count(), 11, msg="invite permission should be 5+5 + founder")
        self.assertEqual(alliance.notification_squad('applicants').count(), 11, msg="applicant permission should be 5+5 + founder")
        self.assertEqual(alliance.notification_squad(['invite', 'applicants']).count(), 16, msg="invite and applicant permissions should be everyone")
        self.assertEqual(alliance.notification_squad(['kick']).count(), 1, msg="only the founder has kick permission")

        #check that it doesn't just accept wrong permission types
        self.assertRaises(ValueError, alliance.notification_squad, 'not_a_permission')
        self.assertRaises(ValueError, alliance.notification_squad, ['invite', 'not_a_permission'])
