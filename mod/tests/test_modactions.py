from nation.models import *
from nation.testutils import *
from nation.mod.actions import *
import nation.variables as v
from django.test import TestCase
from django.db.models import Q

class Actiontests(TestCase):
    @classmethod
    def setUpTestData(cls):
        q = Nation.objects.create(index=1)
        Settings.objects.create(mod=True, nation=q)
        Military.objects.create(nation=q)
        Econdata.objects.create(nation=q)
        Researchdata.objects.create(nation=q)
        cls.mod = q
        q = Nation.objects.create(index=2)
        Settings.objects.create(nation=q)
        Military.objects.create(nation=q)
        Econdata.objects.create(nation=q)
        Researchdata.objects.create(nation=q)
        cls.pleb = q
        ID.objects.get_or_create()
        cls.pleb.reports.create(reported=cls.mod)


    def test_donor_actions(self):
        give_donor(self.mod, self.pleb, 'giving donor')
        self.pleb.settings.refresh_from_db()
        self.assertEqual(self.pleb.settings.donor, True)
        self.assertEqual(self.mod.mod_actions.filter(
            action__icontains='donor',
            reason='giving donor').exists(), True)

        revoke_donor(self.mod, self.pleb, 'revoking donor')
        self.pleb.settings.refresh_from_db()
        self.assertEqual(self.pleb.settings.donor, False)
        self.assertEqual(self.mod.mod_actions.filter(
            action__icontains='revoked', 
            reason='revoking donor').exists(), True)


    def test_vacation_actions(self):
        expected = v.vacationtimer()
        enter_vacation(self.mod, self.pleb, 'placing in vacation')
        self.pleb.settings.refresh_from_db()
        self.pleb.refresh_from_db()
        self.assertEqual(self.pleb.vacation, True)
        self.assertEqual(self.pleb.settings.vacation_timer > expected, True)
        self.assertEqual(self.mod.mod_actions.filter(
            action__icontains='vacation',
            reason='placing in vacation').exists(), True)

        exit_vacation(self.mod, self.pleb, 'removing from vacation')
        self.pleb.refresh_from_db()
        expected = v.now()
        self.pleb.settings.refresh_from_db()
        self.assertEqual(self.pleb.vacation, False)
        self.assertEqual(self.pleb.settings.vacation_timer < expected, True)
        self.assertEqual(self.mod.mod_actions.filter(
            action__icontains='vacation',
            reason='removing from vacation').exists(), True)

    def test_id_assignment(self):
        current = self.pleb.index
        assign_id(self.pleb, 500)
        self.pleb.refresh_from_db()
        self.assertEqual(self.pleb.index, 500)
        self.assertEqual(Nation.objects.filter(index=500).count(), 1)


    def test_id_assignment_taken(self):
        current = self.mod.index
        target = Nation.objects.all().exclude(index=current)[0]
        reference = target.index
        assign_id(self.mod, target.index)
        self.mod.refresh_from_db()
        target.refresh_from_db()
        self.assertNotEqual(current, self.mod.index)
        self.assertNotEqual(reference, target.index)
        self.assertEqual(reference, self.mod.index)
        self.assertEqual(Nation.objects.filter(index=self.mod.index).count(), 1)
        self.assertEqual(Nation.objects.filter(index=target.index).count(), 1)

    def test_shadowban_report(self):
        #ban, unban and ban & delete
        report_ban(self.pleb)
        self.pleb.settings.refresh_from_db()
        self.assertEqual(self.pleb.settings.can_report, False)
        self.assertEqual(Report.objects.filter(reporter=self.pleb).exists(), True)

        report_unban(self.pleb)
        self.pleb.settings.refresh_from_db()
        self.assertEqual(self.pleb.settings.can_report, True)

        report_ban(self.pleb, True)
        self.pleb.settings.refresh_from_db()
        self.assertEqual(self.pleb.settings.can_report, False)
        self.assertEqual(Report.objects.filter(reporter=self.pleb).exists(), False)



class deletiontest(TestCase):

    @classmethod
    def setUpTestData(cls):
        from django.contrib.auth.models import User
        """
            Generate 7 test subjects
            3 with an alliance and 1 being founder
            2 being regular nations and 1 being a mod
            2 being at war
            to test if it properly removes members/wars upon deletion
        """
        from random import randint
        l = []
        for x in ['a', 'b', 'c', 'd', 'e', 'f', 'g']:
            q = Nation.objects.create(user=User.objects.create(username=x))
            # generates a variable length list of IPs to be used for banning tests
            # using pythons list concatenation magics
            IPs = [IP(nation=q, IP='%s.%s.%s.%s' % tuple([randint(0, 255) for x in range(4)])) for x in range(1, 50)]
            q.IPs.bulk_create(IPs)
            Settings.objects.create(nation=q)
            Military.objects.create(nation=q)
            Econdata.objects.create(nation=q)
            Researchdata.objects.create(nation=q)
            l.append(q)
        cls.a = l[0] #alliance founder
        cls.b = l[1] #alliance member
        cls.c = l[2] #mod
        cls.d = l[3] #regular normal guy
        cls.e = l[4] #regular normal guy
        cls.f = l[5] #at war with g
        cls.g = l[6] #at war with f and alliance member

        #alliance boilerplate crap, to be delegated to alliance creation functions later
        Alliance.objects.create()
        alliance = Alliance.objects.create(
            name='test alliance',
            description='test alliance')
        Initiatives.objects.create(alliance=alliance)
        Bank.objects.create(alliance=alliance)
        Bankstats.objects.create(alliance=alliance, turn=10)
        #founder permission set
        founder = Permissiontemplate.objects.create(alliance=alliance, title='founder_title', 
            founder=True, officer=True, rank=0)
        founder.founded()
        #base officer
        alliance.templates.create(title='officer', officer=True,
            kick=True, mass_comm=True, invite=True, applicants=True, rank=3, promote=True)
        #member template
        alliance.templates.create(rank=5, title='member_title')

        alliance.add_member(cls.a, founder=True)
        alliance.add_member(cls.b)
        alliance.add_member(cls.g)

        for x in range(10):
            cls.g.offers.create()



        Settings.objects.filter(nation=cls.c).update(mod=True)
        War.objects.create(attacker=cls.f, defender=cls.g)


    def test_delete_quick(self):
        delete(self.c, self.d, 'testing reg deletion')
        ref = Nation.objects.actives().count()
        self.d.user.refresh_from_db()
        self.d.refresh_from_db()
        self.assertEqual(self.d.user.is_active, False)
        self.assertEqual(self.d.deleted, True)
        self.assertEqual(Nation.objects.actives().filter(pk=self.d.pk).exists(), False)
        self.assertEqual(self.c.mod_actions.filter(reason='testing reg deletion').exists(), True)



    def test_base_deletion(self):
        #testing deletion with an alliance member
        #at war with someone else
        #should add spies
        subject = self.g
        delete_nation(subject)
        subject.refresh_from_db()
        subject.user.refresh_from_db()
        self.assertEqual(Nation.objects.actives().filter(pk=subject.pk).exists(), False)
        self.assertEqual(subject.user.is_active, False)
        self.assertEqual(subject.deleted, True)
        #wars
        self.assertEqual(
            War.objects.filter(
                    Q(attacker=subject)|Q(defender=subject), 
                    over=False
                        ).exists(), 
            False)
        #market offers
        self.assertEqual(subject.offers.all().exists(), False)

        #spy tests
        self.assertEqual(subject.spies.exclude(location=subject).exists(), False)
        self.assertEqual(Spy.objects.filter(
                location=subject).exclude(
                    nation=subject).exists(), 
            False)
        self.assertEqual(Extradition_request.objects.filter(Q(target=subject)|Q(nation=subject)).exists(), False)

        self.assertEqual(subject.declarations.filter(deleted=False).exists(), False)
        self.assertEqual(subject.has_alliance(), False)


    def test_quickbanning(self):
        ban(self.c, self.e, 'testing quickban')

        self.assertEqual(Ban.objects.filter(IP=self.e.IPs.all().latest('pk').IP).exists(), True)
        self.assertEqual(self.c.mod_actions.filter(reason='testing quickban').exists(), True)


    def test_banning(self):
        #tests whether banning players puts them on the ban list
        #expected behaviour is adding the offending IP(s) to the banlist
        #and that they don't exist before being added
        self.assertEqual(Ban.objects.filter(IP__in=self.b.IPs.all().values_list('IP', flat=True)).exists(), False)
        ban_nation(self.b)
        expected = self.b.IPs.all().latest('pk').IP
        self.assertEqual(Ban.objects.filter(IP=expected).exists(), True)

        ban_nation(self.b, True)
        expected = self.b.IPs.all().values_list('IP', flat=True)
        self.assertEqual(
            Ban.objects.filter(IP__in=expected).count(),
            self.b.IPs.all().count()
            )



class bulk_operations(TestCase):
    def setUp(self):
        n = nation_generator(50)
        for x in n:
            for ip in ip_generator(5):
                x.IPs.create(IP=ip)
        s = Settings.objects.latest('pk')
        s.mod = True
        s.save()

    def test_bulk_deletion(self):
        q = Nation.objects.all().exclude(settings__mod=True)
        mod = Nation.objects.get(settings__mod=True)
        actioncount = mod.mod_actions.all().count()
        nationcount = q.count()
        bulk_delete(q, mod, 'testing bulk deletion')
        self.assertEqual(Nation.objects.actives().exclude(settings__mod=True).count(), 0)
        self.assertEqual(actioncount + 1, mod.mod_actions.all().count())
        action = mod.mod_actions.filter(reason='testing bulk deletion')
        self.assertEqual(action.exists(), True)

    def test_bulk_banning(self):
        q = Nation.objects.all().exclude(settings__mod=True)
        mod = Nation.objects.get(settings__mod=True)
        ipcount = bulk_ban(q, mod, 'testing bulk banning')
        self.assertEqual(ipcount, q.count() * 6)
        self.assertEqual(mod.mod_actions.filter(reason='testing bulk banning').exists(), True)
        self.assertEqual(Nation.objects.actives().count(), 1) #mod remains 


