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
        result, newfie = self.member_invite(action)
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
        return result, newfie

    def test_leaving(self):
        self.leave_alliance()
        self.assertEqual(self.founder.news.all().count(), 1, msg="a member leaving should generate an event")

    def test_leaving_noevent(self):
        self.alliance.event_on_leaving = False
        self.alliance.save()

        self.leave_alliance()
        self.assertEqual(self.founder.news.all().count(), 0, msg="a member leaving shouldn't generate an event")
        self.assertEqual(self.alliance.permissions.all().count(), 1, msg="Permissions should be deleted when leaving")
        self.assertEqual(self.alliance.memberstats.all().count(), 1, msg="Memberstats should be deleted when leaving")

        leave(self.founder)
        #1 because of the second alliance
        self.assertEqual(Alliance.objects.all().count(), 1)
        self.assertEqual(Memberstats.objects.all().count(), 1)
        self.assertEqual(Permissions.objects.all().count(), 1)
        self.assertEqual(Bank.objects.all().count(), 1)
        self.assertEqual(Initiatives.objects.all().count(), 1)
        self.assertEqual(Bankstats.objects.all().count(), 1)
        self.assertEqual(Permissiontemplate.objects.all().count(), 3)

    def test_founder_leave(self):
        leave(self.founder)
        self.assertEqual(self.alliance.members.filter(permissions__template__rank=5).count(), 0, msg="Founder leaving should promote the member to founder")
        self.assertEqual(self.alliance.members.filter(permissions__template__rank=0).count(), 1, msg="Founder leaving should promote the member to founder")
        self.assertEqual(self.alliance.members.all().count(), 1)


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
        self.assertEqual(applyee.actionlogs.all().count(), 1, msg="actionlog should be generated")

        self.alliance.event_on_applicants = False
        self.alliance.applications.all().delete()
        result = apply(applyee, self.alliance)
        self.assertEqual(self.founder.news.all().count(), 1, msg="Event should not be generated")


    def test_apply_member(self):
        result = apply(self.member, self.alliance)
        self.assertTrue(result != '')
        self.assertEqual(self.alliance.applications.all().count(), 0, msg="Application shouldn't be generated")
        self.assertEqual(self.founder.news.all().count(), 0, msg="Event shouldn't be generated")
        self.assertEqual(self.member.actionlogs.all().count(), 0, msg="No actionlog should be generated")


    def test_unapply(self):
        applyee =nation_generator()
        apply(applyee, self.alliance)
        
        result = apply(applyee, self.alliance)
        self.assertTrue(result != '')
        self.assertEqual(self.alliance.applications.all().count(), 0, msg="Application should've been deleted")
        self.assertEqual(self.founder.news.all().count(), 2, msg="Event should be generated")
        self.assertEqual(applyee.actionlogs.all().count(), 2)


        self.alliance.event_on_applicants = False
        self.alliance.save()
        apply(applyee, self.alliance)
        result = apply(applyee, self.alliance)
        self.assertTrue(result != '')
        self.assertEqual(self.alliance.applications.all().count(), 0, msg="Application should've been deleted")
        self.assertEqual(self.founder.news.all().count(), 2, msg="Event shouldn't be generated")
        self.assertEqual(applyee.actionlogs.all().count(), 4)


    def test_depositing(self):
        payload = {'amount': 50}
        self.member.budget = 500
        self.member.save()
        result = deposit(self.member, payload)
        self.check_depositvals(result)

        payload = {'amount': 0}
        result = deposit(self.member, payload)
        self.check_depositvals(result)

        payload = {'amount': -2000}
        result = deposit(self.member, payload)
        self.check_depositvals(result)

        payload = {'amount': 9000}
        result = deposit(self.member, payload)
        self.check_depositvals(result)


    def check_depositvals(self, result):
        self.alliance.bank.refresh_from_db()
        self.assertTrue(result != '')
        self.assertEqual(self.member.budget, 450)
        self.assertEqual(self.member.actionlogs.all().count(), 1)
        self.assertEqual(self.alliance.bank.budget, 50)
        self.assertEqual(self.alliance.bank_logs.all().count(), 1)


    def test_withdrawals(self):
        self.alliance.bank.budget = 1000
        self.alliance.bank.budget_limit = 500
        self.alliance.bank.save()
        self.member.budget = 500
        self.member.save()
        payload = {'amount': 500}
        result = withdraw(self.member, payload)
        self.assertTrue(result != '')
        self.assertEqual(self.member.budget, 500)
        self.assertEqual(self.member.actionlogs.all().count(), 0)
        self.assertEqual(self.alliance.bank.budget, 1000)
        self.assertEqual(self.alliance.bank_logs.all().count(), 0)

        self.founder.budget = 500
        result = withdraw(self.founder, payload)
        self.alliance.bank.refresh_from_db()
        self.assertTrue(result != '')
        self.assertEqual(self.founder.budget, 1000)
        self.assertEqual(self.founder.actionlogs.all().count(), 1)
        self.assertEqual(self.alliance.bank.budget, 500)
        self.assertEqual(self.alliance.bank_logs.all().count(), 1)


        self.member.permissions.template.withdraw = True
        self.member.permissions.template.save()
        result = withdraw(self.member, payload)
        self.alliance.bank.refresh_from_db()
        self.assertTrue(result != '')
        self.assertEqual(self.member.budget, 1000)
        self.assertEqual(self.member.actionlogs.all().count(), 1)
        self.assertEqual(self.alliance.bank.budget, 0)
        self.assertEqual(self.alliance.bank_logs.all().count(), 2)




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
        for member in self.alliance.members.all().exclude(pk=self.founder.pk).values_list('pk', flat=True)[0:6]:
            kickees +=  'member_choice=%s&' % member
        kickees = kickees[:-1]
        payload = QueryDict(kickees)

        result = kick(self.founder, payload)
        self.assertTrue(result != '')
        self.assertEqual(self.alliance.members.all().count(), 20, msg="6 members should've been kicked")


    def test_officer_kick(self):
        kicker = self.alliance.officers.all().order_by('?')[0]

        kickees = 'member_choice=%s&' % self.officers.exclude(pk=kicker.pk).order_by('?')[0].pk
        members = []
        for member in self.officers.values_list('pk', flat=True)[0:6]:
            kickees +=  'member_choice=%s&' % member
            members.append(member)
        kickees = kickees[:-1]
        result = kick(kicker, QueryDict(kickees))
        self.assertTrue(result != '')
        self.assertEqual(self.alliance.members.all().count(), 26, msg="no officers should've been kicked")

        for member in members:
            nation = Nation.objects.get(pk=member)
            self.assertEqual(nation.news.all().count(), 0, msg="Member shouldn't recieve notification that they got kicked")


    def test_officer_kick_members(self):
        kicker = self.officers.order_by('?')[0]
        kickees = 'member_choice=%s&' % self.members.exclude(pk=kicker.pk).order_by('-pk')[0].pk
        members = []
        for member in self.members.values_list('pk', flat=True)[0:5]:
            kickees += 'member_choice=%s&' % member
            members.append(member)
        kickees = kickees[:-1]
        result = kick(kicker, QueryDict(kickees))
        self.assertTrue(result != '')
        self.assertEqual(self.alliance.members.all().count(), 20)

        for member in members:
            nation = Nation.objects.get(pk=member)
            self.assertEqual(nation.news.all().count(), 1, msg="Member should recieve notification that they got kicked")


    def test_mass_comms(self):
        result = masscomm(self.founder, {'masscomm': 'everyone', 'message': 'Test mass comms because lol'})
        self.assertTrue(result != '')
        for member in self.alliance.members.all():
            self.assertEqual(member.comms.all().count(), 1)


    def test_officer_comm(self):
        result = masscomm(self.founder, {'masscomm': 'officers', 'message': 'Test mass comms because lol'})
        self.assertTrue(result != '')
        for member in self.alliance.members.all():
            if member.permissions.template.rank == 5:
                self.assertEqual(member.comms.all().count(), 0, msg="Members don't get officer comms")
            else:
                self.assertEqual(member.comms.all().count(), 1, msg="officers should get officer comms")


    def test_comm_failure(self):
        result = masscomm(self.founder, {'masscomm': 'everyone', 'message': '2s'})
        self.assertEqual(result, 'Message must be between 5 and 500 characters', msg="Should be an error")
        for member in self.alliance.members.all():
            self.assertEqual(member.comms.all().count(), 0)


    def test_declarations(self):
        decs = [self.founder, self.alliance.officers.all()[0]]
        for deccer, x in zip(decs, [1, 2]):
            self.make_declaration(deccer, x)

        payload = {'message': "T"}
        result = declare(self.founder, payload)
        self.assertTrue(result != '')
        self.assertEqual(self.alliance.declarations.all().count(), 2, msg="Too short messages not aloud")

    
    def test_memberdeclaration(self):
        payload = {'message': "This is a declaration"}
        declarer = self.alliance.members.filter(permissions__template__rank=5)[0]
        result = declare(declarer, payload)
        self.assertTrue(result != '')
        self.assertEqual(self.alliance.declarations.all().count(), 0)
        self.assertEqual(declarer.actionlogs.all().count(), 0, msg="no dec, no log")


    def make_declaration(self, declarer, expected):
        payload = {'message': "This is a declaration"}
        result = declare(declarer, payload)
        self.assertTrue(result != '')
        self.assertEqual(self.alliance.declarations.all().count(), expected)
        self.assertEqual(declarer.actionlogs.all().count(), 1, msg="decs should be logged")


    def test_resign_officer(self):
        officer = self.officers.all()[0]
        result = resign(officer)
        self.assertTrue(result != '')
        self.assertEqual(officer.permissions.template.rank, 5)
        self.assertEqual(officer.actionlogs.all().count(), 1)


    def test_resign_founder(self):
        #this tests if new heirs work correctly
        result = resign(self.founder)
        self.assertTrue(result != '')
        self.assertEqual(self.founder.permissions.template.rank, 5)
        self.assertEqual(self.founder.actionlogs.all().count(), 1)

        self.assertEqual(self.alliance.members.filter(permissions__template__rank=0).count(), 1)
        newfounder = self.alliance.members.get(permissions__template__rank=0)
        self.assertEqual(newfounder.news.all().count(), 1, msg="New founder should be notified of the promotion")

    def test_resign_with_heir(self):
        heir = self.alliance.officers.all().order_by('?')[0]
        heir.permissions.heir = True
        heir.permissions.save()
        result = resign(self.founder)
        self.assertTrue(result != '')
        self.assertEqual(self.founder.permissions.template.rank, 5)
        heir.permissions.refresh_from_db()
        self.assertEqual(heir.permissions.template.rank, 0)


class invite_revokage(TestCase):
    def setUp(self):
        self.founder = nation_generator()
        self.alliance = alliance_generator(self.founder, 20, 5)
        self.alliance.event_on_invite = True
        self.invitees = nation_generator(10)
        for x in self.invitees:
            x.invites.create(alliance=self.alliance, inviter=self.founder)

    def test_single_revoke(self):
        invite = self.alliance.outstanding_invites.all()[0]
        payload = {'revoke': invite.pk}
        officer = self.alliance.officers.all()[3]
        result = revoke_invites(officer, payload)
        self.assertTrue(result != '')
        self.assertEqual(self.alliance.outstanding_invites.all().count(), 9, msg="Invite should've been revoked")
        self.assertEqual(invite.nation.news.all().count(), 1, msg="news item should be generated")
        self.assertEqual(self.founder.news.all().count(), 1, msg="news item should be generated")
        self.assertEqual(officer.actionlogs.all().count(), 1, msg="Should be logged")


    def test_single_revoke_failure(self):
        payload = {'revoke': 50012}
        officer = self.alliance.officers.all()[3]
        result = revoke_invites(officer, payload)
        self.assertTrue(result != '')
        self.assertEqual(self.alliance.outstanding_invites.all().count(), 10, msg="Invite should've been revoked")
        self.assertEqual(self.founder.news.all().count(), 0, msg="news item should be generated")
        self.assertEqual(officer.actionlogs.all().count(), 0, msg="Shouldn't be logged")


    def test_single_revoke_without_event(self):
        invite = self.alliance.outstanding_invites.all()[0]
        self.alliance.event_on_invite = False
        payload = {'revoke': invite.pk}
        officer = self.alliance.officers.all()[3]
        result = revoke_invites(officer, payload)
        self.assertTrue(result != '')
        self.assertEqual(self.alliance.outstanding_invites.all().count(), 9, msg="Invite should've been revoked")
        self.assertEqual(invite.nation.news.all().count(), 1, msg="news item should be generated")
        self.assertEqual(self.founder.news.all().count(), 0, msg="news item should be generated")
        self.assertEqual(officer.actionlogs.all().count(), 1, msg="Should be logged")


    def test_all_revokes(self):
        payload = {'revoke': 'all'}
        officer = self.alliance.officers.all()[3]
        result = revoke_invites(officer, payload)
        self.assertEqual(self.alliance.outstanding_invites.all().count(), 0, msg="Invite should've been revoked")
        self.assertEqual(self.founder.news.all().count(), 1)
        self.assertEqual(officer.actionlogs.all().count(), 1, msg="Should be logged")




class applicant_tests(TestCase):
    def setUp(self):
        self.founder = nation_generator()
        self.alliance = alliance_generator(self.founder, 20, 5)
        self.other_alliance = alliance_generator(nation_generator(), 10, 2)
        self.members = self.alliance.members.filter(permissions__template__rank=5)
        self.officers = self.alliance.members.filter(permissions__template__rank=3)
        self.founder.refresh_from_db()

        self.applicants = nation_generator(5)
        for applicant in self.applicants:
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
        self.assertEqual(self.other_alliance.applications.all().count(), 5)


    def test_acceptance(self):
        result = reject_applicants(self.founder, self.applications)
        self.assertTrue(result != '')
        for sucker in self.applicants:
            self.assertEqual(sucker.news.all().count(), 1, msg="Should've recieved a rejection notice")
        self.assertEqual(self.founder.actionlogs.all().count(), 1, msg="Action should be logged")
        self.assertEqual(self.alliance.applications.all().count(), 0)
        self.assertEqual(self.other_alliance.applications.all().count(), 5)


