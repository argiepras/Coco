from django.test import TestCase
from django.http.request import QueryDict

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
        self.alliance2 = alliance_generator(nation_generator())
        self.founder.refresh_from_db()
        self.alliance.add_member(self.member)
        self.member.refresh_from_db()

    def test_invites(self):
        #This tests the invite actions for non-members
        #ie rejecting and accepting invites
        #it's broken down into several functions to decrease amount of needed code
        self.invite_actions(reject_invite)
        self.assertEqual(self.alliance.members.count(), 2)

        self.invite_actions(accept_invite)
        self.assertEqual(self.alliance.members.count(), 4) #is run twice

    def invite_actions(self, action):
        #accepting and rejecting invites are tested twice
        #with and without event generation for relevant officers
        alliance = self.alliance
        result = self.member_invite(action)
        self.assertTrue(result)
        self.assertTrue(result != '')
        self.assertEqual(newfie.invites.all().count(), 0)
        self.assertEqual(self.alliance.outstanding_invites.all().count(), 0)
        self.assertEqual(self.founder.news.all().count(), 1, msg="Event should be generated")

        alliance.event_on_invite = False
        alliance.save()
        self.member_invite(action)
        self.assertEqual(self.founder.news.all().count(), 1, msg="Event shouldn't be generated")


    def member_invite(self, action):
        newfie = nation_generator()
        inv = self.alliance.outstanding_invites.create(nation=newfie, inviter=self.founder)
        result = action(newfie, self.alliance, inv)
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
        self.assertIsNone(self.member.alliance, msg='leaving should lead to alliance=None')
        self.assertEqual(self.alliance.members.all().count(), 1)
        self.assertEqual(self.member.actionlogs.all().count(), 1, msg="actions should be logged")


    def test_chat(self):
        payload = {'message': 'a message that is an appropriate size'}
        #first we do too short
        result = post_chat(self.member, {'message': '123'})
        self.assertTrue(result)
        self.assertEqual(self.alliance.chat.all().count(), 0)

        #then normal + spam
        for x in range(10):
            result = post_chat(self.member, payload)
            self.assertTrue(result)
            self.assertEqual(self.alliance.chat.all().count(), 1)

        #and then test for a message that's way too long
        result = post_chat(self.member, {'message': ''.join((str(x) for x in range(500)))})
        self.assertTrue(result)
        self.assertEqual(self.alliance.chat.all().count(), 1)

        self.assertEqual(self.member.actionlogs.all().count(), 1, msg="actions should be logged")


    def test_applying_nonmember(self):
        applyee =nation_generator()
        result = apply(applyee, self.alliance)
        self.assertTrue(result != '')
        self.assertEqual(self.alliance.applications.all().count(), 1, msg="Application should be generated")
        self.assertEqual(self.founder.news.all().count(), 1, msg="Event should be generated")

        self.alliance.event_on_applicants = False
        self.alliance.applications.all().delete()
        result = apply(applyee, self.alliance)
        self.assertEqual(self.founder.news.all().count(), 1, msg="Event should not be generated")

class officer_tests(TestCase):
    def setUp(self):
        self.founder = nation_generator()
        self.alliance = alliance_generator(self.founder, 20, 5)
        self.members = self.alliance.members.filter(permissions__template__rank=5)
        self.officers = self.alliance.members.filter(permissions__template__rank=3)
        self.founder.refresh_from_db()



    def test_kicking(self):
        payload = QueryDict("member_choice=515&member_choice=2050") #No such member should exist
        result = kick(self.founder, payload) 

        self.assertTrue(result != '')
        self.assertEqual(self.alliance.members.all().count(), 26, msg="Nobody should've been kicked")
        self.assertEqual(self.founder.actionlogs.all().count(), 0, msg="Nobody should've been kicked")


        kickees = ''
        for member in self.alliance.members.all().exclude(self.founder).values_list('pk', flat=True)[0:6]:
            kickees +=  'member_choice=%s&' % member
        kickees = kickees[:-1]
        payload = QueryDict(kickees)

        result = kick(self.founder, payload)
        self.assertTrue(result != '')
        self.assertEqual(self.alliance.members.all().count(), 20, msg="6 members should've been kicked")


    def test_officer_kick(self):
        kicker = self.alliance.officers.all().order_by('?')[0]

        kickees = 'member_choice=%s&' % self.officers.exclude(pk=kicker.pk).order_by('?')[0]
        members = []
        for member in self.members.values_list('pk', flat=True)[0:6]:
            kickees +=  'member_choice=%s&' % member
            members.append(member)
        kickees = kickees[:-1]

        result = kick(kicker, payload)
        self.assertTrue(result != '')
        self.assertEqual(self.alliance.members.all().count(), 20, msg="6 members should've been kicked")

        for member in members:
            Nation.objects.get(pk=member)
            self.assertEqual(nation.news.all().count(), 1, msg="Member should recieve notification that they got kicked")


    def test_mass_comms(self):
        result = masscomm(self.founder, {'masscomm': 'everyone', 'message': 'Test mass comms because lol'})
        self.assertTrue(result != '')
        for member in self.alliance.members.all():
            self.assertEqual(member.comms.all(), 1, msg="Every member should get a comm")


    def test_officer_comm(self):
        result = masscomm(self.founder, {'masscomm': 'officers', 'message': 'Test mass comms because lol'})
        self.assertTrue(result != '')
        for member in self.alliance.members.all():
            if member.permissions.template.rank == 5:
                self.assertEqual(member.comms.all(), 0, msg="Members don't get officer comms")
            else:
                self.assertEqual(member.comms.all(), 1, msg="officers should get officer comms")


    def test_comm_failure(self):
        result = masscomm(self.founder, {'masscomm': 'everyone', 'message': '2s'})
        self.assertEqual(result, 'Message must be between 5 and 500 characters', msg="Should be an error")
        for member in self.alliance.members.all():
            self.assertEqual(member.comms.all(), 0, msg="Nobody should get a comm")


    def test_declarations(self):
        decs = [self.founder, self.alliance.officers.all()[0], self.alliance.members.filter(permissions__template__rank=5)[0]]
        for deccer, x in zip(decs, range(1, 4)):
            self.make_declaration(deccer, x)

        payload = {'message': "T"}
        result = declare(self.founder, payload)
        self.assertTrue(result != '')
        self.assertEqual(self.alliance.declarations.all().count(), 3, msg="Too short messages not aloud")

    
    def make_declaration(self, declarer, expected)
        payload = {'message': "This is a declaration"}
        result = declare(self.declarer, payload)
        self.assertTrue(result != '')
        self.assertEqual(self.alliance.declarations.all().count(), expected)
        self.assertEqual(declarer.actionlogs.all().count(), 1, msg="decs should be logged")





class applicant_tests(TestCase):
    def setUp(self):
        self.founder = nation_generator()
        self.alliance = alliance_generator(self.founder, 20, 5)
        self.other_alliance = alliance_generator(nation_generator(), 10, 2)
        self.members = self.alliance.members.filter(permissions__template__rank=5)
        self.officers = self.alliance.members.filter(permissions__template__rank=3)
        self.founder.refresh_from_db()

        self.applicants = nation_generator(5)
        for applicant in applicants:
            apply(applicant, self.alliance)
            apply(applicant, self.other_alliance)

        self.applications = self.alliance.applications.all()


    def test_rejection(self):
        result = reject_applicants(self.founder, self.applications)
        self.assertTrue(result != '')
        for sucker in self.applicants:
            self.assertEqual(sucker.news.all().count(), 1, msg="Should've recieved a rejection notice")
        self.assertEqual(self.founder.actionlogs.all().count(), 1, msg="Action should be logged")
        self.assertEqual(self.alliance.applications.all().count(), 0)
        self.assertEqual(self.other_alliance.applications.all().count(), 0)


    def test_acceptance(self):
        result = reject_applicants(self.founder, self.applications)
        self.assertTrue(result != '')
        for sucker in self.applicants:
            self.assertEqual(sucker.news.all().count(), 1, msg="Should've recieved a rejection notice")
        self.assertEqual(self.founder.actionlogs.all().count(), 1, msg="Action should be logged")
        self.assertEqual(self.alliance.applications.all().count(), 0)
        self.assertEqual(self.other_alliance.applications.all().count(), 0)
