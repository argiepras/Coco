from django.test import TestCase
from nation.testutils import *
from nation.models import *
from nation.alliances.memberactions import *
from nation.alliances.officeractions import *
import nation.variables as v



class member_tests(TestCase):
    def setUp(self):
        self.founder = nation_generator()
        self.member = nation_generator()
        self.alliance = alliance_generator(self.founder)
        self.founder.refresh_from_db()
        self.alliance.add_member(self.member)

    def test_invites(self):
        self.invite_actions(reject_invite)
        self.assertEqual(self.alliance.members.count(), 2)

        self.invite_actions(accept_invite)
        self.assertEqual(self.alliance.members.count(), 4) #is run twice

    def invite_actions(self, action):
        alliance = self.alliance
        self.member_invite(self, action)
        self.assertTrue(result)
        self.assertTrue(result != '')
        self.assertEqual(newfie.invites.all().count(), 0)
        self.assertEqual(self.alliance.outstanding_invites.all().count(), 0)
        self.assertEqual(self.founder.news.all().count(), 1, msg="Event should be generated")

        alliance.event_on_invite = False
        alliance.save()
        self.member_invite(self, action)
        self.assertEqual(self.founder.news.all().count(), 1, msg="Event shouldn't be generated")


    def member_invite(self, action):
        newfie = nation_generator()
        self.alliance.outstanding_invites.create(nation=newfie, inviter=self.founder)
        result = action(newfie, self.alliance)
        self.assertEqual(newfie.actionlogs.all().count(), 1, msg="Actionlog should be generated")
        return result

    def test_leaving(self):
        self.leave_alliance()
        self.assertEqual(self.founder.news.all().count(), 1, msg="a member leaving should generate an event")

        #reset and check that no event is generated
        self.alliance.add_member(self.member)
        self.member.refresh_from_db()
        self.alliance.event_on_leaving = False
        self.alliance.save()

        self.leave_alliance()
        self.assertEqual(self.founder.news.all().count(), 1, msg="a member leaving shouldn't generate an event")
        self.assertEqual(self.alliance.permissions.all().count(), 1, msg="Permissions should be deleted when leaving")
        self.assertEqual(self.alliance.Memberstats.all().count(), 1, msg="Memberstats should be deleted when leaving")

        leave(self.founder)

        self.assertEqual(Alliance.objects.all().count(), 0)
        self.assertEqual(Memberstats.objects.all().count(), 0)
        self.assertEqual(Permissions.objects.all().count(), 0)
        self.assertEqual(Bank.objects.all().count(), 0)
        self.assertEqual(Initiatives.objects.all().count(), 0)
        self.assertEqual(Bankstats.objects.all().count(), 0)
        self.assertEqual(Permissiontemplate.objects.all().count(), 0)

    def leave_alliance(self):
        self.assertEqual(self.alliance.members.all().count(), 2)
        leave(self.member)
        self.member.refresh_from_db()
        self.assertNone(member.alliance, msg='leaving should lead to alliance=None')
        self.assertEqual(self.alliance.members.all().count(), 1)
        self.assertEqual(self.member.actionlogs.all().count(), 1, msg="actions should be logged")


    def test_chat(self):
        payload = {'message': 'a message that is an appropriate size'}
        #first we do too short
        result = post_chat(self.member, {'message', '123'})
        self.assertTrue(result)
        self.assertEqual(self.alliance.chat.all().count(), 0)

        #then normal + spam
        for x in range(10):
            result = post_chat(self.member, payload)
            self.assertTrue(result)
            self.assertEqual(self.alliance.chat.all().count(), 1)

        #and then test for a message that's way too long
        result = post_chat(self.member, {'message', ''.join((str(x) for x in range(500)))})
        self.assertTrue(result)
        self.assertEqual(self.alliance.chat.all().count(), 1)

        self.assertEqual(self.member.actionlogs.all().count(), 1, msg="actions should be logged")

