from django.test import TestCase, Client
from django.contrib.auth.models import User


from nation.models import Nation, Spy, Market, Alliance
from nation.testutils import nation_generator, alliance_generator
from nation.variables import regionshort
"""
Basic tests of urls, mostly checking that they are redirecting when they should
and they don't return 500 errors
pages to test:
index/
api?
nations/<index>
main/
    comms/
    comms/sent/
    foreign/
    economic/
    military/
    domestic/
    intelligence/
    intelligence/<spy id>
    intelligence/discovered       ?
    settings/
    news/
    new/
    reset/
modcenter/
    stuff here
market/
    offers/
alliances/
    /rankings
    /main
    /new
    /main/chat
    /main/statistics
    /<alliance id>
    /main/bank
    /main/control_panel
    /main/control_panel/change
    /main/applications
    /main/invites
register/
logout/
login/
map/
recover/
rankings/
rankings/<region>
declarations/
regiondiscussion/
chat/
legal/
about/
news/
"""


class logged_out(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = Client()
        nation_generator(10)
        alliance_generator()

    def test_valid_loggin(self):
        subject = nation_generator()
        username = subject.user.username
        password = "password"
        subject.user.set_password(password)
        subject.user.save()
        client = Client()
        payload = {'username': username, 'password': password}
        response = client.post('/login/', payload)
        self.assertEqual(response.status_code, 302, msg="valid logins should redirect to /main/")
        response = client.get('/main/')
        self.assertEqual(response.status_code, 200)

    def test_invalid_login(self):
        subject = nation_generator()
        username = subject.user.username
        password = "totallythewrongpassword"
        client = Client()
        payload = {'username': username, 'password': password}
        response = client.post('/login/', payload)
        self.assertEqual(response.status_code, 200, msg="invalid logins should just return error")

    def test_news(self):
        response = self.client.get('/news/')
        self.assertEqual(response.status_code, 200)

    def test_about(self):
        response = self.client.get('/about/')
        self.assertEqual(response.status_code, 200)

    def test_legal(self):
        response = self.client.get('/legal/')
        self.assertEqual(response.status_code, 200)

    def test_map(self):
        response = self.client.get('/map/')
        self.assertEqual(response.status_code, 200)

    def test_chat(self):
        response = self.client.get('/chat/')
        self.assertEqual(response.status_code, 301)

    def test_regional_discusses(self):
        response = self.client.get('/regiondiscussion/')
        #it uses the associated nations region to fetch the dicussions
        #so wouldn't work without a login
        self.assertEqual(response.status_code, 302, msg="Need to have a nation to go here")

    def test_declarations(self):
        response = self.client.get('/declarations/')
        self.assertEqual(response.status_code, 200)

    def test_regional_rankings(self):
        for region in regionshort.keys():
            response = self.client.get('/rankings/?region=%s' % region)
            self.assertEqual(response.status_code, 200, msg=response.content)

        reponse = self.client.get('/rankings/notarealregion')
        self.assertEqual(response.status_code, 404)

    def test_rankings(self):
        response = self.client.get('/rankings/')
        self.assertEqual(response.status_code, 200)

    def test_recover(self):
        response = self.client.get('/recover/')
        self.assertEqual(response.status_code, 200)

    def test_register(self):
        response = self.client.get('/register/')
        self.assertEqual(response.status_code, 200)

    def test_index(self):
        response = self.client.get('/index/')
        self.assertEqual(response.status_code, 200)

    def test_market(self):
        response = self.client.get('/market/')
        self.assertEqual(response.status_code, 302)

    def test_market_offers(self):
        response = self.client.get('/market/offers/')
        self.assertEqual(response.status_code, 302)

    def test_nationpage(self):
        response = self.client.get('/nations/1')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/nations/100000')
        self.assertEqual(response.status_code, 404)





    def test_alliances_main(self):
        response = self.client.get('/alliances/main/')
        self.assertEqual(response.status_code, 302)

    def test_alliances_new(self):
        response = self.client.get('/alliances/new/')
        self.assertEqual(response.status_code, 302)

    def test_alliances_mainchat(self):
        response = self.client.get('/alliances/main/chat/')
        self.assertEqual(response.status_code, 302)

    def test_alliances_mainstats(self):
        response = self.client.get('/alliances/main/statistics/')
        self.assertEqual(response.status_code, 302)

    def test_alliance_bank(self):
        response = self.client.get('/alliances/main/bank/')
        self.assertEqual(response.status_code, 302)

    def test_alliance_cp(self):
        response = self.client.get('/alliances/main/control_panel/')
        self.assertEqual(response.status_code, 302)

    def test_alliance_cpchange(self):
        response = self.client.get('/alliances/main/control_panel/change/')
        self.assertEqual(response.status_code, 302)

    def test_alliance_applications(self):
        response = self.client.get('/alliances/main/applications/')
        self.assertEqual(response.status_code, 302)

    def test_alliance_invites(self):
        response = self.client.get('/alliances/main/invites/')
        self.assertEqual(response.status_code, 302)

    def test_alliances(self):
        response = self.client.get('/alliances/1/')
        self.assertEqual(response.status_code, 302)

    def test_alliance_rankings(self):
        response = self.client.get('/alliances/rankings/')
        self.assertEqual(response.status_code, 302)




    def test_main(self):
        response = self.client.get('/main/')
        self.assertEqual(response.status_code, 302)

    def test_comms(self):
        response = self.client.get('/main/comms/')
        self.assertEqual(response.status_code, 302)

    def test_sent_comms(self):
        response = self.client.get('/main/comms/sent/')
        self.assertEqual(response.status_code, 302)

    def test_policies(self):
        for policy in ['foreign', 'military', 'economic', 'domestic']:
            response = self.client.get('/main/%s/' % policy)
            self.assertEqual(response.status_code, 302)

    def test_settings(self):
        response = self.client.get('/main/settings/')
        self.assertEqual(response.status_code, 302)

    def test_nation_news(self):
        response = self.client.get('/main/news/')
        self.assertEqual(response.status_code, 302)

    def test_new_nation(self):
        response = self.client.get('/main/new/')
        self.assertEqual(response.status_code, 302)

    def test_nation_reset(self):
        response = self.client.get('/main/reset/')
        self.assertEqual(response.status_code, 302)

    def test_intelligence(self):
        response = self.client.get('/main/intelligence/')
        self.assertEqual(response.status_code, 302)

    def test_aspy(self):
        response = self.client.get('/main/intelligence/1')
        self.assertEqual(response.status_code, 302)




class alliance_less_nation(TestCase):
    def setUp(cls):
        c = Client()
        Market.objects.create()
        q = User.objects.create_user('aaaa', 'aaa@aaa.aa', 'password')
        a = Nation.objects.create(user=q)
        nation_generator(15)
        alliance_generator()
        a.spies.create(location=a)
        cls.subject = a
        c.force_login(q)
        cls.client = c

    def test_news(self):
        response = self.client.get('/news/')
        self.assertEqual(response.status_code, 200)

    def test_about(self):
        response = self.client.get('/about/')
        self.assertEqual(response.status_code, 200)

    def test_legal(self):
        response = self.client.get('/legal/')
        self.assertEqual(response.status_code, 200)

    def test_map(self):
        response = self.client.get('/map/')
        self.assertEqual(response.status_code, 200)

    def test_chat(self):
        response = self.client.get('/chat/')
        self.assertEqual(response.status_code, 301)

    def test_regional_discusses(self):
        response = self.client.get('/regiondiscussion/')
        #it uses the associated nations region to fetch the dicussions
        #so wouldn't work without a login
        self.assertEqual(response.status_code, 200)

    def test_declarations(self):
        response = self.client.get('/declarations/')
        self.assertEqual(response.status_code, 200)

    def test_regional_rankings(self):
        for region in regionshort:
            response = self.client.get('/rankings/%s' % region)
            self.assertEqual(response.status_code, 200)

        reponse = self.client.get('/rankings/notarealregion')
        self.assertEqual(response.status_code, 404)

    def test_rankings(self):
        response = self.client.get('/rankings/')
        self.assertEqual(response.status_code, 200)

    def test_recover(self):
        response = self.client.get('/recover/')
        self.assertEqual(response.status_code, 302)

    def test_register(self):
        response = self.client.get('/register/')
        self.assertEqual(response.status_code, 302)

    def test_index(self):
        response = self.client.get('/index/')
        self.assertEqual(response.status_code, 200)

    def test_market(self):
        response = self.client.get('/market/')
        self.assertEqual(response.status_code, 200)

    def test_market_offers(self):
        response = self.client.get('/market/offers/')
        self.assertEqual(response.status_code, 200)

    def test_nationpage(self):
        index = Nation.objects.all().exclude(pk=self.subject.pk).order_by('?')[0].index
        response = self.client.get('/nations/%s' % index)
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/nations/100000')
        self.assertEqual(response.status_code, 404)


    #alliance related tests


    def test_alliances_main(self):
        response = self.client.get('/alliances/main/')
        self.assertEqual(response.status_code, 302)

    def test_alliances_new(self):
        response = self.client.get('/alliances/new/')
        self.assertEqual(response.status_code, 200)

    def test_alliances_mainchat(self):
        response = self.client.get('/alliances/main/chat/')
        self.assertEqual(response.status_code, 302)

    def test_alliances_mainstats(self):
        response = self.client.get('/alliances/main/statistics/')
        self.assertEqual(response.status_code, 302)

    def test_alliance_bank(self):
        response = self.client.get('/alliances/main/bank/')
        self.assertEqual(response.status_code, 302)

    def test_alliance_cp(self):
        response = self.client.get('/alliances/main/control_panel/')
        self.assertEqual(response.status_code, 302)

    def test_alliance_cpchange(self):
        response = self.client.get('/alliances/main/control_panel/change/')
        self.assertEqual(response.status_code, 302)

    def test_alliance_applications(self):
        response = self.client.get('/alliances/main/applications/')
        self.assertEqual(response.status_code, 302)

    def test_alliance_invites(self):
        response = self.client.get('/alliances/main/invites/')
        self.assertEqual(response.status_code, 302)

    def test_alliances(self):
        response = self.client.get('/alliances/1/')
        self.assertEqual(response.status_code, 200)

    def test_alliance_rankings(self):
        response = self.client.get('/alliances/rankings/')
        self.assertEqual(response.status_code, 200)


    #main nation pages


    def test_main(self):
        response = self.client.get('/main/')
        self.assertEqual(response.status_code, 200)

    def test_comms(self):
        response = self.client.get('/main/comms/')
        self.assertEqual(response.status_code, 200)

    def test_sent_comms(self):
        response = self.client.get('/main/comms/sent/')
        self.assertEqual(response.status_code, 200)

    def test_policies(self):
        for policy in ['foreign', 'military', 'economic', 'domestic']:
            response = self.client.get('/main/%s/' % policy)
            self.assertEqual(response.status_code, 200)

    def test_settings(self):
        response = self.client.get('/main/settings/')
        self.assertEqual(response.status_code, 200)

    def test_nation_news(self):
        response = self.client.get('/main/news/')
        self.assertEqual(response.status_code, 200)

    def test_new_nation(self):
        response = self.client.get('/main/new/')
        self.assertEqual(response.status_code, 302)

    def test_nation_reset(self):
        response = self.client.get('/main/reset/')
        self.assertEqual(response.status_code, 302)

    def test_intelligence(self):
        response = self.client.get('/main/intelligence/')
        self.assertEqual(response.status_code, 200)

    def test_aspy(self):
        pk = self.subject.spies.get().pk
        response = self.client.get('/main/intelligence/%s' % pk)
        self.assertEqual(response.status_code, 200)



class allianced_player(TestCase):
    def setUp(self):
        c = Client()
        Market.objects.create()
        q = User.objects.create_user('aaaa', 'aaa@aaa.aa', 'password')
        a = Nation.objects.create(user=q)
        nation_generator(15)
        alliance = alliance_generator(members=10, officers=2)
        alliance_generator(members=10, officers=2)
        alliance.add_member(a)
        c.force_login(q)
        self.client = c
        a.refresh_from_db()
        self.subject = a

    def test_has_alliance(self):
        self.assertTrue(self.subject.has_alliance())

    def test_alliances_main(self):
        response = self.client.get('/alliances/main/')
        self.assertEqual(response.status_code, 200)

    def test_alliances_new(self):
        response = self.client.get('/alliances/new/')
        self.assertEqual(response.status_code, 302)

    def test_alliances_mainchat(self):
        response = self.client.get('/alliances/main/chat/')
        self.assertEqual(response.status_code, 200)

    def test_alliances_mainstats(self):
        response = self.client.get('/alliances/main/statistics/')
        self.assertEqual(response.status_code, 302)

    def test_alliance_bank(self):
        response = self.client.get('/alliances/main/bank/')
        self.assertEqual(response.status_code, 302)

    def test_alliance_cp(self):
        response = self.client.get('/alliances/main/control_panel/')
        self.assertEqual(response.status_code, 302)

    def test_alliance_cpchange(self):
        response = self.client.get('/alliances/main/control_panel/change/')
        self.assertEqual(response.status_code, 302)

    def test_alliance_applications(self):
        response = self.client.get('/alliances/main/applications/')
        self.assertEqual(response.status_code, 302)

    def test_alliance_invites(self):
        response = self.client.get('/alliances/main/invites/')
        self.assertEqual(response.status_code, 302)

    def test_alliances(self):
        response = self.client.get('/alliances/2/')
        self.assertEqual(response.status_code, 200)

    def test_alliance_rankings(self):
        response = self.client.get('/alliances/rankings/')
        self.assertEqual(response.status_code, 200)



class alliance_founder(TestCase):
    def setUp(self):
        c = Client()
        Market.objects.create()
        q = User.objects.create_user('aaaa', 'aaa@aaa.aa', 'password')
        a = Nation.objects.create(user=q)
        nation_generator(15)
        alliance = alliance_generator(founder=a, members=10, officers=2)
        alliance_generator(members=10, officers=2)
        c.force_login(q)
        self.client = c
        a.refresh_from_db()
        self.founder = a

    def test_isfounder(self):
        alliance = Alliance.objects.get(pk=1)
        self.assertEqual(alliance.founder, self.founder.name)

    def test_alliances_main(self):
        response = self.client.get('/alliances/main/')
        self.assertEqual(response.status_code, 200)

    def test_alliances_new(self):
        response = self.client.get('/alliances/new/')
        self.assertEqual(response.status_code, 302)

    def test_alliances_mainchat(self):
        response = self.client.get('/alliances/main/chat/')
        self.assertEqual(response.status_code, 200)

    def test_alliances_mainstats(self):
        response = self.client.get('/alliances/main/statistics/')
        self.assertEqual(response.status_code, 200)

    def test_alliance_bank(self):
        response = self.client.get('/alliances/main/bank/')
        self.assertEqual(response.status_code, 200)

    def test_alliance_cp(self):
        response = self.client.get('/alliances/main/control_panel/')
        self.assertEqual(response.status_code, 200)

    def test_alliance_cpchange(self):
        response = self.client.get('/alliances/main/control_panel/change/?template=new')
        self.assertEqual(response.status_code, 200)

    def test_alliance_applications(self):
        response = self.client.get('/alliances/main/applications/')
        self.assertEqual(response.status_code, 200)

    def test_alliance_invites(self):
        response = self.client.get('/alliances/main/invites/')
        self.assertEqual(response.status_code, 200)

    def test_alliances(self):
        response = self.client.get('/alliances/2/')
        self.assertEqual(response.status_code, 200)

    def test_alliance_rankings(self):
        response = self.client.get('/alliances/rankings/')
        self.assertEqual(response.status_code, 200)