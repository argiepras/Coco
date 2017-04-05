from __future__ import unicode_literals
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from . import variables as v

from django.db import models
from django.db.models import F, Avg
from django.utils import timezone

def latestmarket():
    return Market.objects.latest('pk').pk


# Create your models here.
#alliance first because it goes top to bottom and cries if a model refers to another model declared later
class Alliance(models.Model):
    def __init__(self, *args, **kwargs):
        super(Alliance, self).__init__(*args, **kwargs)
        self.averagegdp = self.members.all().filter(deleted=False, vacation=False, gdp__gt=0).aggregate(avgdp=Avg('gdp'))['avgdp']
    name = models.CharField(max_length=30)
    description = models.CharField(max_length=1000, default="You can change this description in the alliance control panel")
    flag = models.CharField(max_length=100, default="/static/alliance/default.png")
    foibonus = models.IntegerField(default=0)
    comm_on_applicants = models.BooleanField(default=True)
    anthem = models.CharField(max_length=15, default="eFTLKWw542g")
    accepts_applicants = models.BooleanField(default=True)
    icon = models.CharField(max_length=40, default="/static/alliance/defaulticon.png")
    def __unicode__(self):
        return u"%s" % self.name
    def get_absolute_url(self):
        return reverse('alliance:alliance_page', kwargs={'alliancepk': (str(self.pk))})

    def add_member(self, nation):
        Memberstats.objects.create(nation=nation, alliance=self)
        membertemplate = self.templates.get(rank=5)
        p = Permissions(member=nation, alliance=self, template=membertemplate)
        Nation.objects.filter(pk=nation.pk).update(alliance=self)
        p.save()

    def taxrate(self, member):
        if member.gdp/2 > self.averagegdp:
            tax = self.initiatives.wealthy_tax
        elif member.gdp > self.averagegdp:
            tax = self.initiatives.uppermiddle_tax
        elif member.gdp*2 < self.averagegdp:
            tax = self.initiatives.poor_tax
        else:
            tax = self.initiatives.lowermiddle_tax
        if tax == 0:
            return 0
        else:
            return tax/100.0

    def taxtype(self, member):
        if member.gdp/2 > self.averagegdp:
            return "wealthy_tax"
        elif member.gdp > self.averagegdp:
            return "uppermiddle_tax"
        elif member.gdp*2 < self.averagegdp:
            return "poor_tax"
        else:
            return "lowermiddle_tax"

    def kick(self, member):
        member.memberstats.delete()
        member.permissions.delete()
        member.alliance = None
        member.save(update_fields=['alliance'])
        return member

class ID(models.Model):
    index = models.IntegerField(default=1) #used to assign IDs
    turn = models.IntegerField(default=1)
    freeIDs = models.IntegerField(default=50)
    #because overriding primary key values pose all sorts of problems
    #so nation IDs will be simple int fields

class Nation(models.Model):
    index = models.IntegerField(default=0)
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=30)
    alliance = models.ForeignKey(Alliance, related_name='members', blank=True, null=True, on_delete=models.SET_NULL)
    protection = models.DateTimeField(default=v.initprotection)
    last_seen = models.DateTimeField(default=v.now)
    vacation = models.BooleanField(default=False) #here and not settings to avoid multiple queries
    deleted = models.BooleanField(default=False) #mod deletion makes nation appear as deleted
    reset = models.BooleanField(default=False)
    descriptor = models.CharField(max_length=100, default="")
    description = models.CharField(max_length=500)
    title = models.CharField(max_length=100, default="")
    creationip = models.GenericIPAddressField()
    creationtime = models.DateTimeField(default=v.now)
    subregion = models.CharField(max_length=25, default="Carribean")
    gdp = models.IntegerField(default=300)
    maxgdp = models.IntegerField(default=300)
    budget = models.IntegerField(default=600)
    trade_balance = models.IntegerField(default=0)
    approval = models.IntegerField(default=51)
    stability = models.IntegerField(default=51)
    literacy = models.IntegerField(default=51)
    healthcare = models.IntegerField(default=51)
    qol = models.IntegerField(default=51)
    growth = models.IntegerField(default=5)
    rebels = models.IntegerField(default=0)
    reputation = models.IntegerField(default=51)
    government = models.IntegerField(default=50)
    economy = models.IntegerField(default=50) #0 = commie 100 = capitalist
    land = models.IntegerField(default=30000)
    oil = models.IntegerField(default=15)
    rm = models.IntegerField(default=30)
    mg = models.IntegerField(default=0)
    FI = models.IntegerField(default=0)
    food = models.IntegerField(default=100)
    uranium = models.IntegerField(default=0)
    oilreserves = models.IntegerField(default=0)
    soviet_points = models.IntegerField(default=0)
    us_points = models.IntegerField(default=0)
    mines = models.IntegerField(default=3)
    closed_mines = models.IntegerField(default=0)
    wells = models.IntegerField(default=0)
    closed_wells = models.IntegerField(default=0)
    oilreserves = models.IntegerField(default=0)
    factories = models.IntegerField(default=0)
    closed_factories = models.IntegerField(default=0)
    manpower = models.IntegerField(default=100)
    alignment = models.IntegerField(default=2) #1 2 3 east neu west
    research = models.IntegerField(default=0)
    universities = models.IntegerField(default=0)
    closed_universities = models.IntegerField(default=0)
    def __unicode__(self):
        return u"%s" % self.name


    def farmland(self):
        tot = 0
        for field in v.landcosts:
            tot += self.__dict__[field] * self.landcost(field)
        return int(self.land - tot)

    def landcost(self, buildingtype):
        if self.researchdata.urbantech == 0:
            return v.landcosts[buildingtype]
        else:
            multiplier = (1 - v.researchbonus['urbantech'])**self.researchdata.urbantech
            return int(v.landcosts[buildingtype] * multiplier)

    def region(self):
        for field in v.regions:
            if self.subregion in v.regions[field]:
                return field

    def population(self):
        return (self.factories+self.universities)*100000+self.mines*10000+self.wells*10000+self.farmland()*10

    def show_title(self):
        if self.title:
            return self.title
        return self.government

    def totalfoodconsumption(self):
        return self.milfoodconsumption() + self.civfoodconsumption()

    def milfoodconsumption(self):
        return self.military.army / 5

    def civfoodconsumption(self):
        return self.population() / 13321


    def has_alliance(self):
        if self.alliance == None:
            return False
        else:
            return True

    def show_descriptor(self):
        if self.descriptor:
            return self.descriptor
        return self.government


        #action logging for shit
        #takes the POST data and extracts pertinent data
        #like the action, ie conscription or training
        #and determines the cost
        #and then either modifies an existing database entry
        #that's <= 15 minutes old or creates a new one
        #this is to keep the database entries under control during spamming
        #thanks dmc5
    def policylogging(self, post, actions):  
        policy = "error in logging %s" % post
        for field in post:
            if field in v.policychoices:
                policy = v.policychoices[field]
        if len(policy) > 50:
            policy = policy[:50]
        cost = 0
        othercost = ''
        for resource in v.resources + ['us_points', 'soviet_points']: 
            if resource == 'budget' and resource in actions:
                cost = actions[resource]['amount']
            else:
                if resource in actions:
                    othercost += '%s-%s ' % (actions[resource]['amount'], resource)
        if othercost:
            othercost = othercost[:-1] #strip away trailing space
        if self.actionlogs.filter(
            timestamp__gte=v.now() - timezone.timedelta(minutes=15),
            action=policy,
            ).exists():
            #if we need to modify costs held in a string
            if othercost:
                log = self.actionlogs.get(
                    timestamp__gte=v.now() - timezone.timedelta(minutes=15),
                    action=policy
                    )
                #string held costs are trickier
                #might be easier if it was encoded in uhh
                #that thing
                #i forget what it's called
                newcost = ''
                current = log.total_cost.split(' ')
                toadd = othercost.split(' ')
                for cur, add in zip(current, toadd):
                    x = int(cur.split('-')[0])
                    y = int(add.split('-')[0])
                    newcost += '%s-%s ' % (x+y, cur.split('-')[1])
                newcost = newcost[:-1]#once again we strip the trailing space
                log.total_cost = newcost
                log.cost += cost
                log.timestamp = v.now()
                log.amount += 1
                log.save(update_fields=[
                    'total_cost', 
                    'cost',
                    'timestamp',
                    'amount'])
            else:
                print "regular"
                self.actionlogs.all().filter(
                    timestamp__gte=v.now() - timezone.timedelta(minutes=15),
                    action=policy,
                    ).update(amount=F('amount') + 1,
                            cost=F('cost') + cost)
        else:
            self.actionlogs.create(cost=cost, action=policy, total_cost=othercost)

    #next couple of functions are helpers used for generating URLs
    #throughout the html templates
    #in case you didn't read the docs
    #this means url structures can be changed with little consequences
    #urls will generate properly
    def get_ranking_url(self):
        sub = ''
        for region in v.regionshort:
            if v.regionshort[region] == self.subregion:
                sub = region
        return reverse('regionrankings', kwargs={'region': sub, 'page': 1})

    def get_mod_url(self):
        if self.settings.mod:
            return reverse('mod:mod', kwargs={'modid': (str(self.index))})
        else:
            return self.get_absolute_url()

    def get_modview_url(self):
        return reverse('mod:nation', kwargs={'nation_id': (str(self.index))})

    def get_absolute_url(self):
        try:
            url = self.donorurl.url
            if url: #if url is not empty
                return reverse('nations:nationpage', kwargs={'url': (str(url))})
            else:
                raise ValueError
        except:
            return reverse('nations:nationpage', kwargs={'url': (str(self.index))})

class Settings(models.Model):
    nation = models.OneToOneField(Nation, primary_key=True, on_delete=models.CASCADE)
    vacation_timer = models.DateTimeField(default=v.now)
    cleared = models.BooleanField(default=False)
    suspect = models.BooleanField(default=False)
    auto_flagged = models.BooleanField(default=False)
    donor = models.BooleanField(default=False)
    can_report = models.BooleanField(default=True)
    mod = models.BooleanField(default=False)
    head_mod = models.BooleanField(default=False)
    flag = models.CharField(max_length=25, default="goonflag.png")
    portrait = models.CharField(max_length=15, default="tito.gif")
    donatoravatar = models.CharField(max_length=200, default='none')
    donatorflag = models.CharField(max_length=200, default='none')
    anthem = models.CharField(max_length=20, default='')
    autoplay = models.BooleanField(default=False)
    def __unicode__(self):
        return u"%s settings" % self.nation.name

    def showflag(self):
        if self.donatorflag == 'none':
            return '/static/flags/%s' % self.flag
        else:
            return self.donatorflag
    def showportrait(self):
        if self.donatoravatar == 'none':
            return '/static/portraits/%s' % self.portrait
        else:
            return self.donatoravatar

    def can_exit(self):
        if self.nation.vacation:
            if self.vacation_timer < v.now():
                return True
        return False

class Donorurl(models.Model):
    owner = models.OneToOneField(Nation, on_delete=models.CASCADE)
    index = models.IntegerField(default=0) #to avoid extra lookup
    url = models.CharField(max_length=30)
    def __unicode__(self):
        return u"%s custom url - /%s/" % (self.owner.name, self.url)


class IP(models.Model):
    nation = models.ForeignKey(Nation, on_delete=models.CASCADE, related_name="IPs")
    IP = models.GenericIPAddressField()
    timestamp = models.DateTimeField(default=v.now)
    def __unicode__(self):
        return u"%s" % self.IP

class Military(models.Model):
    nation = models.OneToOneField(Nation, primary_key=True, on_delete=models.CASCADE)
    army = models.IntegerField(default=20)
    navy = models.IntegerField(default=0)
    planes = models.IntegerField(default=0)
    training = models.IntegerField(default=50)
    weapons = models.IntegerField(default=10)
    chems = models.IntegerField(default=0) #moves from 0-10
    reactor = models.IntegerField(default=0) #moves from 0 to 20 
    nukes = models.IntegerField(default=0)
    def __unicode__(self):
        return "%ss military data" % self.nation.name

    def to_next(self):
        tiers = []
        for field in v.techlimits:
            tiers.append(field)
        tiers.sort() #because dictionaries are unordered
        for tier in tiers:
            if tier == 2000:
                return 0
            if self.weapons < tier:
                prevtier = tiers[tiers.index(tier)-1]
                required = tier - prevtier
                progress = self.weapons-prevtier
                return progress*100/required


class Researchdata(models.Model):
    nation = models.OneToOneField(Nation, primary_key=True, on_delete=models.CASCADE)
    miningtech = models.IntegerField(default=0)
    oiltech = models.IntegerField(default=0)
    foodtech = models.IntegerField(default=1)
    urbantech = models.IntegerField(default=0)
    industrialtech = models.IntegerField(default=0)
    prospecttech = models.IntegerField(default=0)
    def __unicode__(self):
        return u"%s research data" % self.nation.name

    def research(self):
        tot = -1
        for field in list(self._meta.fields)[1:]: #memes
            tot += self.__dict__[field.name]
        return tot


class Econdata(models.Model):
    nation = models.OneToOneField(Nation, primary_key=True, on_delete=models.CASCADE)
    prospects = models.IntegerField(default=0)
    labor = models.IntegerField(default=1)
    nationalize = models.BooleanField(default=False)
    diamonds = models.IntegerField(default=1)
    drugs = models.IntegerField(default=1)
    expedition = models.BooleanField(default=False)
    cedes = models.IntegerField(default=0)
    foodproduction = models.IntegerField(default=100) #percentage of production
    def __unicode__(self):
        return "%ss econ data" % self.nation.name


class Comm(models.Model):
    message = models.TextField(max_length=1000)
    sender = models.ForeignKey(Nation,blank=True, null=True, on_delete=models.SET_NULL)
    recipient = models.ForeignKey(Nation, related_name='comms',blank=True, null=True, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=v.now)
    leadership = models.BooleanField(default=False)
    globalcomm = models.BooleanField(default=False)
    modcomm = models.BooleanField(default=False)
    masscomm = models.BooleanField(default=False)
    unread = models.BooleanField(default=True)
    def __str__(self):
        return "to %s from %s" % (self.recipient, self.sender)
    def __unicode__(self):
        return u"to %s from %s" % (self.recipient, self.sender)

class Sent_comm(models.Model):
    message = models.TextField(max_length=1000)
    sender = models.ForeignKey(Nation, related_name='sent_comms',blank=True, null=True, on_delete=models.CASCADE)
    recipient = models.ForeignKey(Nation, blank=True, null=True, on_delete=models.SET_NULL)
    timestamp = models.DateTimeField(default=v.now)
    leadership = models.BooleanField(default=False)
    modcomm = models.BooleanField(default=False)
    masscomm = models.BooleanField(default=False)


class War(models.Model):
    attacker = models.ForeignKey(Nation, on_delete=models.CASCADE, related_name="offensives")
    defender = models.ForeignKey(Nation, on_delete=models.CASCADE, related_name="defensives")
    attackerpeace = models.BooleanField(default=False)
    defenderpeace = models.BooleanField(default=False)
    timestamp = models.DateTimeField(default=v.now)
    attacked = models.BooleanField(default=False)
    defended = models.BooleanField(default=False)
    airattacked = models.BooleanField(default=False)
    airdefended = models.BooleanField(default=False)
    navyattacked = models.BooleanField(default=False)
    navydefended = models.BooleanField(default=False)
    over = models.BooleanField(default=False)
    def __unicode__(self):
        return u"%s attacking %s" % (self.attacker.name, self.defender.name)
    def peace(self):
        if self.attackerpeace and self.defenderpeace:
            return True
        return False


class Donor(models.Model):
    name = models.CharField(max_length=30)


class Declaration(models.Model):
    nation = models.ForeignKey(Nation, related_name="declarations")
    region = models.CharField(max_length=15)
    timestamp = models.DateTimeField(default=v.now)
    content = models.CharField(max_length=500)
    deleted = models.BooleanField(default=False)
    deleter = models.ForeignKey(Nation, related_name="deleted_declarations", on_delete=models.SET_NULL, null=True, blank=True)
    deleted_timestamp = models.DateTimeField(default=v.now)
    def __unicode__(self):
        return "%s declaration in %s" % (self.nation.name, self.region)


class Event(models.Model):
    nation = models.ForeignKey(Nation, related_name='news', on_delete=models.CASCADE)
    event = models.BooleanField(default=False)
    deletable = models.BooleanField(default=True)
    content = models.TextField()    
    timestamp = models.DateTimeField(default=v.now)
    seen = models.BooleanField(default=False)


class Eventhistory(models.Model):
    nation = models.ForeignKey(Nation, related_name="event_history", on_delete=models.CASCADE)
    event = models.CharField(max_length=50)
    choice = models.CharField(max_length=50)
    timestamp = models.DateTimeField(default=v.now)

#######################
###### MOD STUFF ######
#######################

#player reports
class Report(models.Model):
    reporter = models.ForeignKey(Nation, related_name="reports", on_delete=models.CASCADE)
    reported = models.ForeignKey(Nation, related_name="reported", on_delete=models.CASCADE)
    investigator = models.ForeignKey(Nation, related_name="investigated", on_delete=models.CASCADE, null=True, blank=True)
    investigated = models.BooleanField(default=False)
    guilty = models.BooleanField(default=False)
    conclusion = models.CharField(max_length=500)
    reason = models.CharField(max_length=100, default="multi")
    comment = models.CharField(max_length=500, default="none")
    timestamp = models.DateTimeField(default=v.now)
    mod_timestamp = models.DateTimeField(default=v.now)

    def __unicode__(self):
        return u"report of %s by %s" % (self.reported.name, self.reporter.name)

    def open(self):
        if self.investigator == None:
            return True
        return False

    def get_absolute_url(self):
        return reverse('mod:report', kwargs={'report_id': self.pk})

#automatically generated reports
class Suspected(models.Model):
    suspect = models.ForeignKey(Nation, on_delete=models.CASCADE)
    reason = models.CharField(max_length=200)
    checked = models.BooleanField(default=False)
    timestamp = models.DateTimeField(default=v.now)


#what mods do, visible to admins and head mod
class Modaction(models.Model):
    mod = models.ForeignKey(Nation, related_name="mod_actions", on_delete=models.CASCADE)
    action = models.CharField(max_length=150)
    reason = models.CharField(max_length=500)
    reversible = models.BooleanField(default=False)
    reverse = models.CharField(max_length=300)
    timestamp = models.DateTimeField(default=v.now)



#for detecting mod abuse
class Modview(models.Model):
    mod = models.ForeignKey(Nation, related_name="mod_views", on_delete=models.CASCADE)
    nation = models.ForeignKey(Nation, on_delete=models.CASCADE)
    page = models.CharField(max_length=30, default="overview")
    timestamp = models.DateTimeField(default=v.now)


#simple ban for now
class Ban(models.Model):
    IP = models.GenericIPAddressField()
    def __unicode__(self):
        return u"%s" % self.IP

###################
####MARKET SHIT####
###################

class Market(models.Model):
    rm_threshold = models.IntegerField(default=30)
    rm_counter = models.IntegerField(default=15)
    rmprice = models.IntegerField(default=50)
    oil_threshold = models.IntegerField(default=30)
    oil_counter = models.IntegerField(default=15)
    oilprice = models.IntegerField(default=60)
    mg_threshold = models.IntegerField(default=30)
    mg_counter = models.IntegerField(default=51)
    mgprice = models.IntegerField(default=300)
    food_threshold = models.IntegerField(default=30)
    food_counter = models.IntegerField(default=15)
    foodprice = models.IntegerField(default=30)
    change = models.IntegerField(default=0) #change in market activity
    def __unicode__(self):
        return u'Market data for turn %s' % self.pk

def marketpk():
    return ID.objects.get().turn

#to preventing gaming the market by buying and selling to increase the sold/bought volumes
class Marketlog(models.Model):
    nation = models.ForeignKey(Nation, on_delete=models.CASCADE, related_name="market_logs")
    resource = models.CharField(max_length=4) #mg rm oil food
    volume = models.IntegerField(default=0)
    cost = models.IntegerField(default=0) #positive for buys negative for sells
    turn = models.IntegerField(default=latestmarket) #set to market.pk
    def __unicode__(self):
        'Turn %s market log for %s' % (self.turn, self.nation.name)


class Marketoffer(models.Model):
    nation = models.ForeignKey(Nation, related_name="offers", on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=v.now)
    offer = models.CharField(max_length=10)
    offer_amount = models.IntegerField(default=1)
    request = models.CharField(max_length=10)
    request_amount = models.IntegerField(default=1)
    allow_tariff = models.BooleanField(default=False)

    def __unicode__(self):
        return u"%s is selling %s %s" % (self.nation.name, self.offer_amount, self.offer)

    def from_form(self, form):
        for field in form:
            self.__dict__[field] = form[field]

    def approved(self, buyer):
        if self.offer in self.nation.__dict__:
            seller = (True if self.offer_amount < self.nation.__dict__[self.offer] else False)
        else: #weapons are contained in the military model
            seller = (True if self.offer_amount < self.nation.military.__dict__[self.offer] - 10 else False)

        if self.request in self.nation.__dict__:
            buyer = (True if self.request_amount < buyer.__dict__[self.request] else False)
        else: #weapons are contained in the military model
            buyer = (True if self.request_amount < buyer.military.__dict__[self.request] - 10 else False)
        return buyer, seller

class Marketofferlog(models.Model):
    buyer = models.ForeignKey(
        Nation, 
        related_name="market_buys", 
        on_delete=models.SET_NULL, 
        null=True,
        blank=True)
    seller = models.ForeignKey(
        Nation, 
        related_name="market_sells", 
        on_delete=models.SET_NULL, 
        null=True,
        blank=True)
    sold = models.CharField(max_length=10)
    bought = models.CharField(max_length=10)
    sold_amount = models.IntegerField(default=0)
    bought_amount = models.IntegerField(default=0)
    posted = models.DateTimeField(default=v.now) #when the offer was posted
    timestamp = models.DateTimeField(default=v.now) #and when it was accepted
    def __unicode__(self):
        return u"%s bought from %s" % (self.buyer.name, self.seller.name)



#######################
#### ALLIANCE SHIT ####
#######################


class Initiatives(models.Model):
    alliance = models.OneToOneField(Alliance, on_delete=models.CASCADE)
    focus = models.CharField(max_length=4)
    healthcare = models.BooleanField(default=False)
    healthcare_timer = models.DateTimeField(default=v.now)
    literacy = models.BooleanField(default=False)
    literacy_timer = models.DateTimeField(default=v.now)
    open_borders = models.BooleanField(default=False)
    open_borders_timer = models.DateTimeField(default=v.now)
    freedom = models.BooleanField(default=False)
    freedom_timer = models.DateTimeField(default=v.now)
    redistribute = models.BooleanField(default=False)
    redistribute_timer = models.DateTimeField(default=v.now)
    alignment = models.IntegerField(default=0) #same as nation alignment
    weapontrade = models.BooleanField(default=False)
    weapontrade_timer = models.DateTimeField(default=v.now)
    wealthy_tax = models.IntegerField(default=0)
    uppermiddle_tax = models.IntegerField(default=0)
    lowermiddle_tax = models.IntegerField(default=0)
    poor_tax = models.IntegerField(default=0)

    def __unicode__(self):
        return u"initiatives for %s" % self.alliance.name

    def reset_timer(self, initiative):
        field = '%s_timer' % initiative
        self.__dict__[field] = timezone.now() + timezone.timedelta(hours=v.initiative_timer)
        return field

class Memberstats(models.Model):
    nation = models.OneToOneField(Nation, on_delete=models.CASCADE)
    alliance = models.ForeignKey(Alliance, related_name="memberstats", on_delete=models.CASCADE)
    budget = models.IntegerField(default=0)
    oil = models.IntegerField(default=0)
    rm = models.IntegerField(default=0)
    mg = models.IntegerField(default=0)
    food = models.IntegerField(default=0)
    timestamp = models.DateTimeField(default=v.now) #functions as join time

#limits are either total or per nation

class Bank(models.Model):
    alliance = models.OneToOneField(Alliance, on_delete=models.CASCADE)
    budget_limit = models.IntegerField(default=0)
    budget = models.IntegerField(default=0)
    oil_limit = models.IntegerField(default=0)
    oil = models.IntegerField(default=0)
    rm_limit = models.IntegerField(default=0)
    rm = models.IntegerField(default=0)
    mg_limit = models.IntegerField(default=0)
    mg = models.IntegerField(default=0)
    food_limit = models.IntegerField(default=0)
    food = models.IntegerField(default=0)
    research = models.IntegerField(default=0)
    per_nation = models.BooleanField(default=True)



class Banklog(models.Model):
    alliance = models.ForeignKey(Alliance, related_name="bank_logs", on_delete=models.CASCADE)
    nation = models.ForeignKey(Nation, related_name="alliancelog_entries", on_delete=models.SET_NULL, null=True, blank=True)
    resource = models.CharField(max_length=10)
    amount = models.IntegerField(default=0)
    deposit = models.BooleanField(default=True)
    timestamp = models.DateTimeField(default=v.now)
    def display(self):
        if self.resource == 'budget':
            return "$%sk" % self.amount
        else:
            return "%s %s" % (self.amount, v.depositchoices[self.resource])
    def __unicode__(self):
        if self.deposit:
            return u"%s deposited %s %s in %ss bank" % (self.nation.name, self.amount, self.resource, self.alliance.name)


class Bankstats(models.Model):
    alliance = models.ForeignKey(Alliance, on_delete=models.CASCADE, related_name="bankstats")
    turn = models.IntegerField(default=marketpk)
    wealthy_tax = models.IntegerField(default=0)
    uppermiddle_tax = models.IntegerField(default=0)
    lowermiddle_tax = models.IntegerField(default=0)
    poor_tax = models.IntegerField(default=0)
    healthcare_cost = models.IntegerField(default=0)
    literacy_cost = models.IntegerField(default=0)
    open_borders_cost = models.IntegerField(default=0)
    freedom_cost = models.IntegerField(default=0)
    weapontrade_cost = models.IntegerField(default=0)
    def __unicode__(self):
        return u"%s bankstats" % self.alliance.name
    def total(self):
        tot = 0
        for field in self._meta.fields:
            if field.name[-3:] == 'tax':
                tot += self.__dict__[field.name]
            elif field.name[-4:] == 'cost':
                tot -= self.__dict__[field.name]
        return tot

    def clear(self):
        for field in self._meta.fields[2:]:
            self.__dict__[field.name] = 0

    def populate(self, stats):
        for field in stats:
            self.__dict__[field] = stats[field]


                


class Invite(models.Model):
    nation = models.ForeignKey(Nation, related_name='invites', on_delete=models.CASCADE)
    inviter = models.ForeignKey(Nation, null=True, blank=True, on_delete=models.SET_NULL)
    alliance = models.ForeignKey(Alliance, related_name="outstanding_invites", on_delete=models.CASCADE)
    def __unicode__(self):
        return u"Invitation to %s from %s" % (self.nation.name, self.alliance.name)

class Alliancedeclaration(models.Model):
    nation = models.ForeignKey(Nation, related_name="alliance_declarations")
    alliance = models.ForeignKey(Alliance, related_name="declarations", on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=v.now)
    content = models.CharField(max_length=500)
    deleted = models.BooleanField(default=False)
    deleter = models.ForeignKey(Nation, related_name="deleted_alliancedecs", on_delete=models.SET_NULL, null=True, blank=True)
    deleted_timestamp = models.DateTimeField(default=v.now)
    def __unicode__(self):
        return "Alliance declaration from %s - %s alliance" % (self.nation.name, self.alliance.name)
#I know it's the exact same but is less clutter with dec/chat tables

class Alliancechat(models.Model):
    nation = models.ForeignKey(Nation, related_name="alliance_chats")
    alliance = models.ForeignKey(Alliance, related_name="chat")
    timestamp = models.DateTimeField(default=v.now)
    content = models.CharField(max_length=500)

class Application(models.Model):
    alliance = models.ForeignKey(Alliance, related_name="applications", on_delete=models.CASCADE)
    nation = models.ForeignKey(Nation, related_name="applications", on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=v.now)
    resume = models.CharField(max_length=300, default="")
    def __unicode__(self):
        return u"%ss application to %s" % (self.nation.name, self.alliance.name)


class Permissiontemplate(models.Model):
    alliance = models.ForeignKey(Alliance, related_name="templates", on_delete=models.CASCADE)
    title = models.CharField(max_length=30, default="member")
    officer = models.BooleanField(default=False)
    founder = models.BooleanField(default=False)
    rank_choices = (
        (0, 0),
        (1, 1),
        (2, 2),
        (3, 3),#YES I KNOW IT SAYS 4 NEXT TO 5
        (4, 4),#5 is regular member
        (5, 5)) #rank is to establish hierarchy, also lower ranks can't delete higher ranks
    rank = models.IntegerField(default=5, choices=rank_choices)
    call_for_election = models.BooleanField(default=False)
    kick = models.BooleanField(default=False)
    kick_officer = models.BooleanField(default=False)
    promote = models.BooleanField(default=False)#promoting peon members, from template or new
    demote_officer = models.BooleanField(default=False)#demoting underling to peon
    change_officer = models.BooleanField(default=False)#changing permissions of underlings, new template
    withdraw = models.BooleanField(default=False) #from bank   ##^ or edit current permissions
    mass_comm = models.BooleanField(default=False)
    officer_comm = models.BooleanField(default=False)
    see_stats = models.BooleanField(default=False)
    delete_log = models.BooleanField(default=False)
    founder = models.BooleanField(default=False)#if true, treats everything as true
    invite = models.BooleanField(default=False)
    banking = models.BooleanField(default=False)
    initiatives = models.BooleanField(default=False)
    applicants = models.BooleanField(default=False)
    taxman = models.BooleanField(default=False)
    create_template = models.BooleanField(default=False)
    change_template = models.BooleanField(default=False)
    delete_template = models.BooleanField(default=False)
    def __unicode__(self):
        return u"%s template" % self.title

    def from_form(self, formdata):
        for field in formdata:
            if field == 'permset':
                if formdata[field] == 'founder':
                    self.founder = True
                self.officer= True
            else:
                self.__dict__[field] = formdata[field]
        if not formdata.has_key('permset'):
            self.officer = True

    def founded(self):
        for field in self._meta.fields[7:]:
            self.__dict__[field.name] = True
        self.save()

class Permissions(models.Model):
    alliance = models.ForeignKey(Alliance, related_name="permissions", on_delete=models.CASCADE)
    member = models.OneToOneField(Nation, on_delete=models.CASCADE)
    template = models.ForeignKey(Permissiontemplate, related_name="users", on_delete=models.CASCADE, blank=True, null=True)
    heir = models.BooleanField(default=False)#takes over if founder goes AWOL
    def __str__(self):
        return "%s, rank %s" % (self.template.title, self.template.rank)

    def __unicode__(self):
        return u"%s, rank %s" % (self.template.title, self.template.rank)

    def panel_access(self):
        return self.template.founder or self.template.officer

    def can_withdraw(self):
        return self.template.founder or (self.template.officer and self.template.withdraw)

    def kickpeople(self):
        return self.template.founder or (self.template.officer and (self.template.kick or self.template.kick_officer))

    def can_kick(self, member):
        if self.member.pk == member.pk:
            return False
        elif self.template.founder:
            return True
        elif self.template.officer and member.template.officer:
            if self.template.kick_officer:
                if self.template.rank > member.template.rank:
                    return True
                else:
                    return False
            else:
                return False
        elif self.template.officer and self.template.kick:
            return True
        return False #not officer or can't kick


    def can_invite(self):
        return self.template.founder or self.template.invite

    def can_banking(self): #retarded name but whatever
        return self.template.founder or self.template.banking

    def can_withdraw(self):
        return self.template.withdraw or self.template.founder

    def can_invites(self):
        return self.template.founder or (self.template.invite and self.template.officer)

    def can_initiatives(self):
        return self.template.founder or (self.template.initiatives and self.template.officer)

    def can_manage(self):
        return self.template.founder or  (self.template.officer and \
            (self.template.promote or self.template.demote_officer or self.template.change_officer))

    def can_manage_permissions(self):
        return self.template.founder or (self.template.officer and \
            (self.template.create_template or self.template.change_template or self.template.delete_template))

    def can_promote(self):
        return self.template.founder or (self.template.officer and self.template.promote)

    def can_change(self): #change officer permissions
        return self.template.founder or (self.template.officer and self.template.change_officer)

    def can_demote(self):
        return self.template.founder or (self.template.officer and self.template.demote_officer)

    def can_applicants(self):
        return self.template.founder or (self.template.officer and self.template.applicants)

    def is_taxman(self):
        return self.template.founder or (self.template.officer and self.template.taxman)

    def can_masscomm(self):
        return self.template.founder or (self.template.officer and self.template.mass_comm)

    def can_officercomm(self):
        return self.template.founder or (self.template.officer and self.template.officer_comm)


##############
#### LOGS ####
##############
#primarily for multi detection and other such protection

class Loginlog(models.Model):
    nation = models.ForeignKey(Nation, on_delete=models.CASCADE, related_name="login_times")
    timestamp = models.DateTimeField(default=v.now)
    IP = models.GenericIPAddressField()
    def __unicode__(self):
        return u"%s seen at %s" % (self.nation.name, self.timestamp)



class Actionlog(models.Model):
    nation = models.ForeignKey(Nation, on_delete=models.CASCADE, related_name="actionlogs")
    action = models.CharField(max_length=50)
    amount = models.IntegerField(default=1)
    cost = models.IntegerField(default=0) #for pure budget cost
    total_cost = models.CharField(max_length=50) #for multiple cost types
    timestamp = models.DateTimeField(default=v.now)


class Aidlog(models.Model):
    sender = models.ForeignKey(Nation, related_name="outgoing_aid", on_delete=models.SET_NULL, null=True, blank=True)
    reciever = models.ForeignKey(Nation, related_name="incoming_aid", on_delete=models.SET_NULL, null=True, blank=True)
    resource = models.CharField(max_length=7)
    amount = models.IntegerField(default=0)
    timestamp = models.DateTimeField(default=v.now)


class Warlog(models.Model):
    war = models.OneToOneField(War, blank=True, null=True, on_delete=models.SET_NULL)
    attacker = models.ForeignKey(Nation, on_delete=models.SET_NULL, blank=True, null=True, related_name="offensive_warlogs")
    defender = models.ForeignKey(Nation, on_delete=models.SET_NULL, blank=True, null=True, related_name="defensive_warlogs")
    winner = models.ForeignKey(Nation, on_delete=models.SET_NULL, blank=True, null=True, related_name="warlog_wins")
    timestart = models.DateTimeField(default=v.now)
    timeend = models.DateTimeField(default=v.now)
    attacker_armystart = models.IntegerField(default=0)
    attacker_armyend = models.IntegerField(default=0)
    attacker_techstart = models.IntegerField(default=0)
    attacker_techend = models.IntegerField(default=0)
    attacker_groundattacks = models.IntegerField(default=0)
    attacker_groundloss = models.IntegerField(default=0)
    attacker_airattacks = models.IntegerField(default=0)
    attacker_airloss = models.IntegerField(default=0)
    attacker_navyattacks = models.IntegerField(default=0)
    attacker_navyloss = models.IntegerField(default=0)
    attacker_chemmed = models.IntegerField(default=0)
    attacker_factoryloss = models.IntegerField(default=0)

    defender_armystart = models.IntegerField(default=0)
    defender_armyend = models.IntegerField(default=0)
    defender_techstart = models.IntegerField(default=0)
    defender_techend = models.IntegerField(default=0)
    defender_groundattacks = models.IntegerField(default=0)
    defender_groundloss = models.IntegerField(default=0)
    defender_airattacks = models.IntegerField(default=0)
    defender_airloss = models.IntegerField(default=0)
    defender_navyattacks = models.IntegerField(default=0)
    defender_navyloss = models.IntegerField(default=0)
    defender_chemmed = models.IntegerField(default=0)
    defender_factoryloss = models.IntegerField(default=0)
    def __unicode__(self):
        return u'%s against %s war log' % (self.attacker.name, self.defender.name)

    def get_absolute_url(self):
        return reverse('mod:war', kwargs={'war_id': (str(self.pk))})


class Lastattack(models.Model):
    log = models.ForeignKey(Warlog, related_name='last_attacks', on_delete=models.CASCADE)
    nation = models.ForeignKey(Nation, on_delete=models.SET_NULL, null=True)
    killed = models.IntegerField(default=0)
    lost = models.IntegerField(default=0)
    timestamp = models.DateTimeField(default=v.now)


class Lastaction(models.Model):
    log = models.ForeignKey(Warlog, related_name='last_actions', on_delete=models.CASCADE)
    nation = models.ForeignKey(Nation, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50, default="none")
    outcome = models.CharField(max_length=100, default="none")
    timestamp = models.DateTimeField(default=v.now)



###########
###SPAHS###
###########


class Spy(models.Model):
    nation = models.ForeignKey(Nation, on_delete=models.CASCADE, related_name="spies")
    name = models.CharField(max_length=10)
    actioned = models.BooleanField(default=False)
    deploytime = models.IntegerField(default=0)
    experience = models.IntegerField(default=0)
    infiltration = models.IntegerField(default=0)
    specialty = models.CharField(max_length=20)
    arrested = models.BooleanField(default=False)
    discovered = models.BooleanField(default=False)
    discovered_timestamp = models.DateTimeField(default=v.now)
    surveillance = models.BooleanField(default=False)
    portrait = models.CharField(max_length=20, default="spies/1.png")
    surveilling = models.OneToOneField('Spy', blank=True, null=True, on_delete=models.SET_NULL)
    location = models.ForeignKey(Nation, on_delete=models.SET_NULL, null=True, blank=True, related_name="infiltrators")
    def __unicode__(self):
        return u"Agent %s - %s" % (self.name, self.specialty)

    def get_absolute_url(self):
        return reverse('nation:spy', kwargs={'spyid': (str(self.pk))})

    def move_home(self):
        self.location = self.nation
        self.actioned = True
        self.arrested = False
        self.discovered = False
        if self.surveillance:
            Spy.objects.filter(surveilling=self).update(surveilling=None)
        self.surveillance = False
        self.deploytime = 0
        self.save()

class Extradition_request(models.Model):
    target = models.ForeignKey(Nation, related_name="pending_requests", on_delete=models.CASCADE)
    nation = models.ForeignKey(Nation, related_name="outgoing_requests", on_delete=models.CASCADE)
    spy = models.OneToOneField(Spy, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=v.now)
    def __unicode__(self):
        return "Extradition request for agent %s, from %s to %s" % (self.spy.name, self.nation.name, self.target.name)










#############################33
######## registration stuff
########################################


def reg_generator():
    import random
    import string
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(50))


class Confirm(models.Model):
    code = models.CharField(max_length=50, default=reg_generator)
    email = models.EmailField()
    regtime = models.DateTimeField(auto_now_add=True)

    def get_absolute_url(self):
        from django.core.urlresolvers import reverse
        return reverse('registration_activation_complete', kwargs={'reg_id': (str(self.code))})

class Recovery(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=50, default=reg_generator)
    regtime = models.DateTimeField(auto_now_add=True)