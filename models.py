from __future__ import unicode_literals
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from . import variables as v


from django.db import models
from django.db.models import F, Q, Avg
from django.utils import timezone

from random import choice

def current_turn():
    return ID.objects.get_or_create()[0].turn #get_or_create to make tests behave

def random_region():
    return choice(v.regionshort.values())

class Allianceoptions(models.Model):
    accepts_applicants = models.BooleanField(
        default=True, 
        verbose_name="Players can apply"
    )
    event_on_incoming = models.BooleanField(
        default=True,
        help_text="This will notify founders and officers with permission to accept/reject applicants when a player applies for membership",
        verbose_name="Notify when players apply"
    )
    event_on_applicants = models.BooleanField(
        default=True,
        help_text="This will notify founders and officers with permission to accept/reject applicants when an officer accepts/rejects an application",
        verbose_name="Notify when an application is accepted/rejected",
    )
    event_on_invite = models.BooleanField(
        default=True,
        help_text="This will notify founders and officers with invite permission when a player accepts/rejects their invite",
        verbose_name="Notify when an invite is accepted/rejected",
    )
     #on rejected/accepted invites
    event_on_leaving = models.BooleanField(
        default=True,
        help_text="This will notify officers when a member leaves the alliance",
        verbose_name="Notify when a member leaves",
    )

    class Meta:
        abstract = True

# Create your models here.
#alliance first because it goes top to bottom and cries if a model refers to another model declared later
class Alliance(Allianceoptions):
    name = models.CharField(max_length=30)
    founder = models.CharField(max_length=30, default="admin")
    description = models.CharField(max_length=1000, default="You can change this description in the alliance control panel")
    flag = models.CharField(max_length=100, default="/static/alliance/default.png")
    foibonus = models.IntegerField(default=0)
    anthem = models.CharField(max_length=15, default="eFTLKWw542g")
    icon = models.CharField(max_length=40, default="/static/alliance/defaulticon.png")

    class Meta:
        ordering = ['pk']

    def _officers(self):
        return self.members.filter(permissions__template__rank__lt=5)
    officers = property(_officers)

    def avgdp(self):
        return self.members.filter(vacation=False, reset=False, deleted=False, gdp__gt=0).aggregate(avgdp=Avg('gdp'))['avgdp']
    averagegdp = property(avgdp)

    def __unicode__(self):
        return u"%s alliance" % self.name

    def get_absolute_url(self):
        return reverse('alliance:alliance_page', kwargs={'alliancepk': (str(self.pk))})

    def notification_squad(self, permissions, anded=False, exclusion=False):
        if type(permissions) != list:
            permissions = [permissions]
        baseq = Q(permissions__template__rank__lt=5)
        var = Q()
        for permission in permissions:
            if not hasattr(Basetemplate, permission):
                raise ValueError
            if anded:
                var&=Q(**{'permissions__template__%s' % permission: True})
            else:
                var|=Q(**{'permissions__template__%s' % permission: True})
        baseq &= var
        squad = self.members.filter(baseq|Q(permissions__template__rank=0)
        #(rank > 5 and permission(s) == True) or rank == 0
        #founder rank overrides other requirements
        )
        if exclusion != False:
            squad = squad.exclude(pk=exclusion)
        return squad

    def add_member(self, nation, founder=False):
        nation.invites.all().delete()
        nation.applications.all().delete()
        Memberstats.objects.create(nation=nation, alliance=self)
        membertemplate = self.templates.get(rank=5)
        self.permissions.create(member=nation, template=membertemplate)
        Nation.objects.filter(pk=nation.pk).update(alliance=self)

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
            tax = "wealthy_tax"
        elif member.gdp > self.averagegdp:
            tax = "uppermiddle_tax"
        elif member.gdp*2 < self.averagegdp:
            tax = "poor_tax"
        else:
            tax = "lowermiddle_tax"
        return tax

    def kick(self, member):
        member.memberstats.delete()
        member.permissions.delete()
        member.alliance = None
        member.save(update_fields=['alliance'])
        if self.members.all().count() == 0:
            self.delete()
        return member

class ID(models.Model):
    index = models.IntegerField(default=1) #used to assign IDs
    turn = models.IntegerField(default=1)
    freeIDs = models.IntegerField(default=50)
    #because overriding primary key values pose all sorts of problems
    #so nation IDs will be simple int fields
    def next(self):
        while True:
            self.index += 1
            if Nation.objects.filter(index=self.index).exists():
                continue
            break 
        self.save(update_fields=['index'])


class Actives(models.Manager):
    def actives(self):
        return self.get_queryset().filter(vacation=False, reset=False, deleted=False)

class Baseattrs(models.Model):
    _approval = models.IntegerField(default=51, verbose_name='approval')
    _stability = models.IntegerField(default=51, verbose_name='stability')
    _literacy = models.IntegerField(default=51, verbose_name='literacy')
    _healthcare = models.IntegerField(default=51, verbose_name='healthcare')
    _qol = models.IntegerField(default=51, verbose_name='quality of life')
    _reputation = models.IntegerField(default=51, verbose_name='reputation')
    _government = models.IntegerField(default=50, verbose_name='government')
    _economy = models.IntegerField(default=50, verbose_name='economy') #0 = commie 100 = capitalist
    _soviet_points = models.IntegerField(default=0, verbose_name='USSR relation points')
    _us_points = models.IntegerField(default=0, verbose_name='US relation points')
    _manpower = models.IntegerField(default=100, verbose_name='manpower')

    #the following code lets us access overflowable attributes and set them freely
    #without risking the actual overflow
    #they'll all go from 0-100 with regular assignments

    def attrsetter(attr):
        def set_any(self, value):
            value = (100 if value > 100 else value)
            value = (0 if value < 0 else value)
            setattr(self, attr, value)
        return set_any

    def attrsetter_negative(attr):
        def set_any(self, value):
            value = (100 if value > 100 else value)
            value = (-100 if value < -100 else value)
            setattr(self, attr, value)
        return set_any

    def attrgetter(attr):
        def get_any(self):
            return self.__dict__[attr]
        return get_any


    approval = property(attrgetter('_approval'), attrsetter('_approval'))
    stability = property(attrgetter('_stability'), attrsetter('_stability'))
    literacy = property(attrgetter('_literacy'), attrsetter('_literacy'))
    healthcare = property(attrgetter('_healthcare'), attrsetter('_healthcare'))
    qol = property(attrgetter('_qol'), attrsetter('_qol'))
    reputation = property(attrgetter('_reputation'), attrsetter('_reputation'))
    government = property(attrgetter('_government'), attrsetter('_government'))
    economy = property(attrgetter('_economy'), attrsetter('_economy'))
    soviet_points = property(attrgetter('_soviet_points'), attrsetter_negative('_soviet_points'))
    us_points = property(attrgetter('_us_points'), attrsetter_negative('_us_points'))
    manpower = property(attrgetter('_manpower'), attrsetter('_manpower'))

    class Meta:
        abstract = True


class Nationattrs(Baseattrs):
    gdp = models.IntegerField(default=300)
    budget = models.IntegerField(default=1000)
    trade_balance = models.IntegerField(default=0)
    growth = models.IntegerField(default=5)
    rebels = models.IntegerField(default=0)
    land = models.IntegerField(default=30000)
    oil = models.IntegerField(default=15)
    rm = models.IntegerField(default=30, verbose_name="raw materials")
    mg = models.IntegerField(default=0, verbose_name="manufactured goods")
    FI = models.IntegerField(default=0, verbose_name="foreign investment")
    food = models.IntegerField(default=100)
    uranium = models.IntegerField(default=0)
    oilreserves = models.IntegerField(default=0)
    mines = models.IntegerField(default=3)
    closed_mines = models.IntegerField(default=0)
    wells = models.IntegerField(default=0)
    closed_wells = models.IntegerField(default=0)
    oilreserves = models.IntegerField(default=0)
    factories = models.IntegerField(default=0)
    closed_factories = models.IntegerField(default=0)
    alignment = models.IntegerField(default=2) #1 2 3 east neu west
    research = models.IntegerField(default=0)
    universities = models.IntegerField(default=0)
    closed_universities = models.IntegerField(default=0)
    class Meta:
        abstract = True

class Nation(Nationattrs):
    index = models.IntegerField(default=0)
    cleared = models.BooleanField(default=False) #cleared means no longer a subject for multi checks
    #set as safe so auto reports won't be generated
    #mostly for when someone creates fake multis to generate reports against a player
    safe = models.BooleanField(default=False)
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
    creationip = models.GenericIPAddressField(default="127.0.0.1") #default only used for testing
    creationtime = models.DateTimeField(default=v.now)
    subregion = models.CharField(max_length=25, default=random_region)
    objects = Actives()
    
    class Meta:
        ordering = ['gdp', 'pk']

    def __unicode__(self):
        return u"%s" % self.name

    def atwar(self):
        return self.offensives.filter(over=False).exists() or self.defensives.filter(over=False).exists()

    def farmland(self):
        tot = 0
        for field in v.landcosts:
            tot += self.__dict__[field] * self.landcost(field)
        return int(self.land - tot)

    def landcost(self, buildingtype):
        if self.researchdata.urbantech == 0 or buildingtype not in v.landresearchbonus:
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
                self.actionlogs.all().filter(
                    timestamp__gte=v.now() - timezone.timedelta(minutes=15),
                    action=policy,
                    ).update(amount=F('amount') + 1,
                            cost=F('cost') + cost)
        else:
            self.actionlogs.create(cost=cost, action=policy, total_cost=othercost)

    #for easier logging
    def actionlogging(self, action, extra=False):
        if self.actionlogs.filter(
            timestamp__gte=v.now() - timezone.timedelta(minutes=15),
            action=action,
                ).exists():
            self.actionlogs.filter(
            timestamp__gte=v.now() - timezone.timedelta(minutes=15),
            action=action,
                ).update(amount=F('amount') + 1)
        else:
            args = {'action': action, 'policy': False}
            if extra:
                args.update({'extra': extra})
            self.actionlogs.create(**args)


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
                break
        return reverse('rankings') + "?region=%s" % sub

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
    autoplay = models.BooleanField(default=True)

    class Meta:
        ordering = ['pk']

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

    def get_absolute_modurl(self):
        return reverse('mod:ip_view', kwargs={'ip': self.IP})


class Militarybase(models.Model):
    army = models.IntegerField(default=20)
    navy = models.IntegerField(default=0)
    planes = models.IntegerField(default=0)
    _training = models.IntegerField(default=50)
    weapons = models.IntegerField(default=10)
    chems = models.IntegerField(default=0) #moves from 0-10
    reactor = models.IntegerField(default=0) #moves from 0 to 20 
    nukes = models.IntegerField(default=0)
    class Meta:
        abstract = True


class Military(Militarybase):
    nation = models.OneToOneField(Nation, primary_key=True, on_delete=models.CASCADE)
    def __unicode__(self):
        return "%ss military data" % self.nation.name

    def attrsetter(attr):
        def set_any(self, value):
            value = (100 if value > 100 else value)
            value = (0 if value < 0 else value)
            setattr(self, attr, value)
        return set_any

    def attrsetter_negative(attr):
        def set_any(self, value):
            value = (100 if value > 100 else value)
            value = (-100 if value < -100 else value)
            setattr(self, attr, value)
        return set_any

    def attrgetter(attr):
        def get_any(self):
            return self.__dict__[attr]
        return get_any

    training = property(attrgetter('_training'), attrsetter('_training'))

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
    nationalize = models.IntegerField(default=0)
    diamonds = models.IntegerField(default=1)
    drugs = models.IntegerField(default=1)
    expedition = models.IntegerField(default=0)
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

    class Meta:
        ordering = ['-timestamp']

class Sent_comm(models.Model):
    message = models.TextField(max_length=1000)
    sender = models.ForeignKey(Nation, related_name='sent_comms',blank=True, null=True, on_delete=models.CASCADE)
    recipient = models.ForeignKey(Nation, blank=True, null=True, on_delete=models.SET_NULL)
    timestamp = models.DateTimeField(default=v.now)
    leadership = models.BooleanField(default=False)
    modcomm = models.BooleanField(default=False)
    masscomm = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']

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

    class Meta:
        ordering = ['-timestamp']

    def __unicode__(self):
        return "%s declaration in %s" % (self.nation.name, self.region)


class Event(models.Model):
    nation = models.ForeignKey(Nation, related_name='news', on_delete=models.CASCADE)
    event = models.BooleanField(default=False)
    deletable = models.BooleanField(default=True)
    content = models.TextField()    
    timestamp = models.DateTimeField(default=v.now)
    seen = models.BooleanField(default=False)
    class Meta:
        get_latest_by = "timestamp"
        ordering = ['-event', '-timestamp']



class Eventhistory(models.Model):
    nation = models.ForeignKey(Nation, related_name="event_history", on_delete=models.CASCADE)
    event = models.CharField(max_length=50)
    choice = models.CharField(max_length=50)
    timestamp = models.DateTimeField(default=v.now)

    class Meta:
        ordering = ['-timestamp']


class War(models.Model):
    attacker = models.ForeignKey(Nation, on_delete=models.SET_NULL, related_name="offensives", blank=True, null=True)
    defender = models.ForeignKey(Nation, on_delete=models.SET_NULL, related_name="defensives", blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    timestamp_end = models.DateTimeField(auto_now_add=True)
    begun = models.IntegerField(default=current_turn)
    ended = models.IntegerField(default=0)
    over = models.BooleanField(default=False)
    winner = models.CharField(max_length=50)

    class Meta:
        ordering = ['-timestamp']

    def __unicode__(self):
        return u"%s attacking %s" % (self.attacker.name, self.defender.name)

    def has_attacked(self, nation, attack_type):
        return self.attacks.filter(attacker=nation, attack_type=attack_type, turn=current_turn()).exists()

    def get_mod_url(self):
        return reverse('mod:war', kwargs={'war_id': self.pk})

class Peace(models.Model):
    war = models.ForeignKey(War, on_delete=models.CASCADE, related_name="peace_offers")
    nation = models.ForeignKey(Nation, on_delete=models.CASCADE, related_name="peace_offers")
    timestamp = models.DateTimeField(auto_now_add=True)


class Attack(models.Model):
    war = models.ForeignKey(War, on_delete=models.CASCADE, related_name="attacks")
    attacker = models.ForeignKey(Nation, on_delete=models.SET_NULL, related_name="attacks", blank=True, null=True)
    attack_type = models.CharField(max_length=10) #ground, naval, air, chem, nuke
    lost = models.IntegerField(default=0)
    turn = models.IntegerField(default=current_turn)
    timestamp = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-pk', '-turn']

class Loss(models.Model):
    attack = models.ForeignKey(Attack, on_delete=models.CASCADE, related_name="kills")
    loss_type = models.CharField(max_length=15)
    amount = models.IntegerField(default=0)


class Wargains(models.Model): #for log purposes
    war = models.ForeignKey(War, on_delete=models.CASCADE, related_name="gains")
    resource = models.CharField(max_length=15)
    amount = models.IntegerField(default=0)
    turn = models.IntegerField(default=current_turn)


#######################
###### MOD STUFF ######
#######################

#player reports
class Report(models.Model):
    reporter = models.ForeignKey(Nation, related_name="reports", on_delete=models.CASCADE, blank=True, null=True)
    reported = models.ForeignKey(Nation, related_name="reported", on_delete=models.CASCADE)
    investigator = models.ForeignKey(Nation, related_name="investigated", on_delete=models.CASCADE, null=True, blank=True)
    closed = models.BooleanField(default=False)
    guilty = models.BooleanField(default=False)
    conclusion = models.CharField(max_length=500)
    reason = models.CharField(max_length=100, default="multi")
    automatic = models.BooleanField(default=False)
    comment = models.CharField(max_length=500, default="none")
    timestamp = models.DateTimeField(default=v.now)
    mod_timestamp = models.DateTimeField(default=v.now)

    class Meta:
        ordering = ['-closed', '-timestamp']

    def __unicode__(self):
        return u"report of %s by %s" % (self.reported.name, self.reporter.name)

    def open(self):
        if self.investigator == None:
            return True
        return False

    def get_absolute_url(self):
        return reverse('mod:report', kwargs={'report_id': self.pk})


class Modnote(models.Model):
    nation = models.ForeignKey(Nation, on_delete=models.CASCADE, related_name='notes')
    note = models.CharField(max_length=100, default="default")
    auto_type = models.CharField(max_length=50, default="manual")
    def __unicode__(self):
        return "Note on %s" % self.nation.name


#what mods do, visible to admins and head mod
class Modaction(models.Model):
    mod = models.ForeignKey(Nation, related_name="mod_actions", on_delete=models.CASCADE)
    action = models.CharField(max_length=150)
    reason = models.CharField(max_length=500)
    reversible = models.BooleanField(default=False)
    reverse = models.TextField()
    timestamp = models.DateTimeField(default=v.now)

    class Meta:
        ordering = ['-timestamp']



#for detecting mod abuse
class Modview(models.Model):
    mod = models.ForeignKey(Nation, related_name="mod_views", on_delete=models.CASCADE)
    nation = models.ForeignKey(Nation, on_delete=models.CASCADE)
    page = models.CharField(max_length=30, default="overview")
    timestamp = models.DateTimeField(default=v.now)

    class Meta:
        ordering = ['-timestamp']

#simple ban for now
class Ban(models.Model):
    IP = models.GenericIPAddressField(unique=True)
    def __unicode__(self):
        return u"%s" % self.IP


## specifically for multi stuff
#likeliness meters of sort
#ranging from 0 to 100
#higher is higher chance of being a multi
#new nations are continually assessed and the values will tick up or down
#depending on behaviour, below a point the cleared flag is set
#and they no longer get assessed
class Multimeter(models.Model):
    nation = models.OneToOneField(Nation, primary_key=True, on_delete=models.CASCADE)
    aid = models.IntegerField(default=50)
    trade_balance = models.IntegerField(default=50)
    comms = models.IntegerField(default=50)
    IP = models.IntegerField(default=50)
    actions = models.IntegerField(default=50)
    meta = models.IntegerField(default=50)
    logins =  models.IntegerField(default=50)
    logouts = models.IntegerField(default=50)
    
    def __unicode__(self):
        return "multimeter for %s" % self.nation.name

    def total(self):
        x = 0
        for field in ['aid', 'comms', 'IP', 'actions', 'meta', 'logins', 'logouts']:
            x += getattr(self, field)
        return x

    def average(self):
        return self.highest() / 8

    def highest(self):
        x = 0
        for field in ['aid', 'comms', 'IP', 'actions', 'meta', 'logins', 'logouts']:
            value = getattr(self, field)
            x = (x if x > value else value)
        return x

class Trade_balance(models.Model):
    multimeter = models.ForeignKey(Multimeter, on_delete=models.CASCADE, related_name='trade_balances')
    trade_balance = models.IntegerField(default=0)
    change = models.IntegerField(default=0)
    turn = models.IntegerField(default=current_turn)
    class Meta:
        ordering = ['-turn']
        get_latest_by = 'turn'


class Aidcheck(models.Model):
    multimeter = models.ForeignKey(Multimeter, on_delete=models.CASCADE, related_name='aidchecks')
    turn = models.IntegerField(default=current_turn)
    increment = models.IntegerField(default=0)

    class Meta:
        ordering = ['-turn']


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
    last_updated = models.IntegerField(default=0)
    turn = models.IntegerField(default=current_turn)

    class Meta:
        get_latest_by = "turn"
    def __unicode__(self):
        return u'Market data for turn %s' % self.pk

    def prices(self):
        r = {}
        for stuff in v.units:
            try: #craps out with research
                r[stuff] = self.__dict__['%sprice' % stuff]
            except:
                continue
        return r

    def changed(self):
        from time import time
        self.last_updated = int(time())

#to preventing gaming the market by buying and selling to increase the sold/bought volumes
class Marketlog(models.Model):
    nation = models.ForeignKey(Nation, on_delete=models.CASCADE, related_name="market_logs")
    resource = models.CharField(max_length=4) #mg rm oil food
    volume = models.IntegerField(default=0)
    cost = models.IntegerField(default=0) #positive for buys negative for sells
    turn = models.IntegerField(default=current_turn) #set to market.pk
    def __unicode__(self):
        return 'Turn %s market log for %s' % (self.turn, self.nation.name)


class Marketoffer(models.Model):
    nation = models.ForeignKey(Nation, related_name="offers", on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=v.now)
    offer = models.CharField(max_length=10)
    offer_amount = models.IntegerField(default=1)
    request = models.CharField(max_length=10)
    request_amount = models.IntegerField(default=1)
    allow_tariff = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']

    def __unicode__(self):
        return u"%s is selling %s %s" % (self.nation.name, self.offer_amount, self.offer)

    def from_form(self, form):
        for field in form:
            self.__dict__[field] = form[field]

    def approved(self, buyer):
        if self.offer in self.nation.__dict__:
            seller = (True if self.offer_amount <= self.nation.__dict__[self.offer] else False)
        else: #weapons are contained in the military model
            seller = (True if self.offer_amount <= self.nation.military.__dict__[self.offer] - 10 else False)

        if self.request in self.nation.__dict__:
            buyer = (True if self.request_amount <= buyer.__dict__[self.request] else False)
        else: #weapons are contained in the military model
            buyer = (True if self.request_amount <= buyer.military.__dict__[self.request] - 10 else False)
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
    unitprice = models.IntegerField(default=0) #unit price in cash money for easier comparisons
    
    class Meta:
        ordering = ['-timestamp']

    def __unicode__(self):
        return u"%s bought from %s" % (self.buyer.name, self.seller.name)



########################
#### ALLIANCE STUFF ####
########################

class Initiatives(models.Model):
    alliance = models.OneToOneField(Alliance, on_delete=models.CASCADE)
    focus = models.CharField(max_length=4)
    healthcare = models.BooleanField(default=False)
    literacy = models.BooleanField(default=False)
    open_borders = models.BooleanField(default=False)
    freedom = models.BooleanField(default=False)
    redistribute = models.BooleanField(default=False)
    alignment = models.IntegerField(default=0) #same as nation alignment
    weapontrade = models.BooleanField(default=False)
    wealthy_tax = models.IntegerField(default=0)
    uppermiddle_tax = models.IntegerField(default=0)
    lowermiddle_tax = models.IntegerField(default=0)
    poor_tax = models.IntegerField(default=0)

    def __unicode__(self):
        return u"initiatives for %s" % self.alliance.name

    def reset_timer(self, initiative):
        setattr(self.timers, initiative, timezone.now() + timezone.timedelta(hours=v.initiative_timer))

class Timers(models.Model):
    initiatives = models.OneToOneField(Initiatives, on_delete=models.CASCADE)
    healthcare = models.DateTimeField(default=v.now)
    literacy = models.DateTimeField(default=v.now)
    open_borders = models.DateTimeField(default=v.now)
    freedom = models.DateTimeField(default=v.now)
    redistribute = models.DateTimeField(default=v.now)
    weapontrade = models.DateTimeField(default=v.now)
    def __unicode__(self):
        return u"Initiative timers for %s" % self.initiatives.alliance.name

class Memberstats(models.Model):
    nation = models.OneToOneField(Nation, on_delete=models.CASCADE)
    alliance = models.ForeignKey(Alliance, related_name="memberstats", on_delete=models.CASCADE)
    budget = models.IntegerField(default=0)
    timestamp = models.DateTimeField(default=v.now) #functions as join time

    class Meta:
        ordering = ['-timestamp']

#limits are either total or per nation

class Bank(models.Model):
    alliance = models.OneToOneField(Alliance, on_delete=models.CASCADE)
    budget_limit = models.IntegerField(default=0)
    budget = models.IntegerField(default=0)
    limit = models.BooleanField(default=True)
    per_nation = models.BooleanField(default=True)



class Banklog(models.Model):
    alliance = models.ForeignKey(Alliance, related_name="bank_logs", on_delete=models.CASCADE)
    nation = models.ForeignKey(Nation, related_name="alliancelog_entries", on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.IntegerField(default=0)
    deposit = models.BooleanField(default=True)
    timestamp = models.DateTimeField(default=v.now)
    deleted = models.BooleanField(default=False)

    class Meta:
        get_latest_by = "timestamp"
        ordering = ['-timestamp']

    def display(self):
        return "$%sk" % self.amount

    def __unicode__(self):
        if self.deposit:
            return u"%s deposited %s %s in %ss bank" % (self.nation.name, self.amount, self.display(), self.alliance.name)
        return u"%s withdrew %s %s in %ss bank" % (self.nation.name, self.amount, self.display(), self.alliance.name)
        

#used for recording turnly income and expenditures
class Bankstats(models.Model):
    alliance = models.ForeignKey(Alliance, on_delete=models.CASCADE, related_name="bankstats")
    turn = models.IntegerField(default=current_turn)
    wealthy_tax = models.IntegerField(default=0)
    uppermiddle_tax = models.IntegerField(default=0)
    lowermiddle_tax = models.IntegerField(default=0)
    poor_tax = models.IntegerField(default=0)
    healthcare_cost = models.IntegerField(default=0)
    literacy_cost = models.IntegerField(default=0)
    open_borders_cost = models.IntegerField(default=0)
    freedom_cost = models.IntegerField(default=0)
    weapontrade_cost = models.IntegerField(default=0)

    class Meta:
        get_latest_by = "turn"

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
    
    class Meta:
        ordering = ['-timestamp']

    def __unicode__(self):
        return "Alliance declaration from %s - %s alliance" % (self.nation.name, self.alliance.name)
#I know it's the exact same but is less clutter with dec/chat tables

class Alliancechat(models.Model):
    nation = models.ForeignKey(Nation, related_name="alliance_chats")
    alliance = models.ForeignKey(Alliance, related_name="chat")
    timestamp = models.DateTimeField(default=v.now)
    content = models.CharField(max_length=500)

    class Meta:
        ordering = ['-timestamp']


class Application(models.Model):
    alliance = models.ForeignKey(Alliance, related_name="applications", on_delete=models.CASCADE)
    nation = models.ForeignKey(Nation, related_name="applications", on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=v.now)
    resume = models.CharField(max_length=300, default="")

    class Meta:
        ordering = ['-timestamp']

    def __unicode__(self):
        return u"%ss application to %s" % (self.nation.name, self.alliance.name)


class Basetemplate(models.Model):
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
    invite = models.BooleanField(default=False)
    banking = models.BooleanField(default=False)
    initiatives = models.BooleanField(default=False)
    applicants = models.BooleanField(default=False)
    taxman = models.BooleanField(default=False)
    templating = models.BooleanField(default=False)
    class Meta:
        abstract = True

class Permissiontemplate(Basetemplate):
    alliance = models.ForeignKey(Alliance, related_name="templates", on_delete=models.CASCADE)
    title = models.CharField(max_length=30, default="member")
    rank_choices = (
        (0, 0), #rank is the numerical, hiercihcal (spelling) representatio
        (1, 1), #0 is founder, 1 through 4 is officer
        (2, 2), #and finnaly 
        (3, 3),#YES I KNOW IT SAYS 4 NEXT TO 5
        (4, 4),#5 is regular member
        (5, 5)) #rank is to establish hierarchy, also lower ranks can't delete higher ranks
    rank = models.IntegerField(default=5, choices=rank_choices)
    def __unicode__(self):
        return u"%s template" % self.title

    def from_form(self, formdata):
        founder = False
        for field in formdata:
            if field == 'permset':
                if formdata[field] == 'founder':
                    founder = True
                    break
            else:
                self.__dict__[field] = formdata[field]
        if founder:
            for field in Basetemplate._meta.fields:
                setattr(self, field.name, True)
                self.rank = 0

    def save(self, *args, **kwargs):
        if self.alliance.templates.all().count() == 0:
            for field in Basetemplate._meta.fields:
                setattr(self, field.name, True)
            self.rank = 0
            self.title = 'Founder'
        super(Permissiontemplate, self).save(*args, **kwargs)


class Permissions(models.Model):
    alliance = models.ForeignKey(Alliance, related_name="permissions", on_delete=models.CASCADE)
    member = models.OneToOneField(Nation, on_delete=models.CASCADE)
    template = models.ForeignKey(Permissiontemplate, related_name="users", on_delete=models.CASCADE, blank=True, null=True)
    heir = models.BooleanField(default=False)#takes over if founder goes AWOL

    class Meta:
        get_latest_by = 'pk'
        ordering = ['-pk']

    def __str__(self):
        return "%s, rank %s" % (self.template.title, self.template.rank)

    def __unicode__(self):
        return u"%s, rank %s" % (self.template.title, self.template.rank)

    
    def can_kick(self, member):
        if self.member.pk == member.pk:
            return False #can't kick yourself
        elif self.template.rank == 0:
            return True #founders can kick everyone
        elif self.template.rank < 5 and member.permissions.template.rank < 5:
            if self.template.kick_officer:
                if self.template.rank < member.permissions.template.rank:
                    return True
        elif self.template.rank < 5 and self.template.kick:
            return True
        return False #not officer or can't kick

    def has_permission(self, permission):
        if not hasattr(Basetemplate, permission):
            raise ValueError('Invalid permission')
        if self.template.rank == 0:
            return True
        return getattr(self.template, permission)

    def panel_access(self):
        return self.template.rank < 5



##############
#### LOGS ####
##############


class Snapshot(Nationattrs, Militarybase):
    #snapshot of the state of a nation during a given turn
    nation = models.ForeignKey(Nation, related_name="snapshots", on_delete=models.CASCADE)
    turn = models.IntegerField(default=current_turn)
    alliance = models.ForeignKey(Alliance, related_name="member_snapshots", null=True, blank=True, on_delete=models.SET_NULL)
    
    class Meta:
        ordering = ['-turn']

    def __unicode__(self):
        return u"snapshot of %s from turn %s" % (self.nation.name, self.turn)


#primarily for multi detection and other such protection
class Loginbase(models.Model):
    timestamp = models.DateTimeField(default=v.now)
    IP = models.GenericIPAddressField()
    turn = models.IntegerField(default=current_turn)
    header = models.CharField(max_length=200, default="")
    class Meta:
        abstract = True


class Loginlog(Loginbase):
    nation = models.ForeignKey(Nation, on_delete=models.CASCADE, related_name="login_times")
    def __unicode__(self):
        return u"%s logged in at %s" % (self.nation.name, self.timestamp)

class Logoutlog(Loginbase):
    nation = models.ForeignKey(Nation, on_delete=models.CASCADE, related_name="logout_times")
    def __unicode__(self):
        return u"%s logged out at %s" % (self.nation.name, self.timestamp)



class Actionlog(models.Model):
    nation = models.ForeignKey(Nation, on_delete=models.CASCADE, related_name="actionlogs")
    action = models.CharField(max_length=50)
    amount = models.IntegerField(default=1)
    cost = models.TextField() #json encoded cost
    extra = models.TextField() #Field for extra comments, should they be necessary
    policy = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now=True)
    turn = models.IntegerField(default=current_turn) #for easier comparisons

    class Meta:
        ordering = ['-timestamp']

#might seem redundant
#but first one is used for the total amount going in or out and is displayed in the mod interface
#and second part is used to prevent spam
#so if more than n database entries within a given timeframe

class Aidlog(models.Model):
    sender = models.ForeignKey(Nation, related_name="outgoing_aid", on_delete=models.SET_NULL, null=True, blank=True)
    reciever = models.ForeignKey(Nation, related_name="incoming_aid", on_delete=models.SET_NULL, null=True, blank=True)
    resource = models.CharField(max_length=20)
    amount = models.IntegerField(default=0)
    value = models.IntegerField(default=0)
    timestamp = models.DateTimeField(default=v.now)
    turn = models.IntegerField(default=current_turn)
    class Meta:
        get_latest_by = "timestamp"
        ordering = ['-timestamp']


class Aid(models.Model):
    sender = models.ForeignKey(Nation, related_name="outgoing_aidspam", on_delete=models.SET_NULL, null=True, blank=True)
    reciever = models.ForeignKey(Nation, related_name="incoming_aidspam", on_delete=models.SET_NULL, null=True, blank=True)
    resource = models.CharField(max_length=20)
    amount = models.IntegerField(default=0)
    timestamp = models.DateTimeField(default=v.now)
    turn = models.IntegerField(default=current_turn)


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



#############################
##### meta stuff
####################

class Header(models.Model):
    nation = models.ForeignKey(Nation, related_name='seen_headers', on_delete=models.CASCADE)
    user_agent = models.CharField(max_length=200)
    set_referrals = models.IntegerField(default=0)
    empty_referrals = models.IntegerField(default=0) #bots don't submit referral fields; probably
    timestamp = models.DateTimeField(auto_now_add=True)



    





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



#legocy

marketpk = None
latestmarket = None