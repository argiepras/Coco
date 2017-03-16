import django
django.setup()
from celery import shared_task, task
from celery.task.schedules import crontab
from celery.decorators import periodic_task
from django.db.models import Sum, Q, Count, Avg
from django.db import IntegrityError
from django.utils import timezone

import nation.utilities as utils
from nation.models import *
import nation.variables as v
import nation.news as news
from nation.turnchange import *
from math import sqrt
from nation.events import *




@periodic_task(run_every=crontab(minute="0,10,20,30,40,50", hour="*", day_of_week="*"))
def alliance_gain():
    for alliance in Alliance.objects.select_related('bank', 'initiatives').all().iterator():
        bankstats = alliance.bankstats.get_or_create(pk=Market.objects.latest('pk').pk)[0]
        while True:
            try:
                #first off is all incoming and outgoing
                #toss it into a bankstat object for easy charting (at some point)
                budget = alliance.bank.budget
                income = alliance_income(alliance)
                expenditures = alliance_expenditures(alliance)
                total_out = 0
                for cost in expenditures:
                    total_out += expenditures[cost]
                
                alliance.bank.budget += income['total']
                if alliance.bank.budget >= total_out:
                    alliance.bank.budget -= total_out
                else:
                    #not enough bank to keep it all running
                    unaffordable = []
                    fields = []
                    for initiative in expenditures:
                        if alliance.initiatives.__dict__[initiative]:
                            if alliance.bank.budget - expenditures[initiative] > 0:
                                alliance.bank.budget -= expenditures[initiative]
                            else:
                                alliance.initiatives.__dict__[initiative] = False
                                #collecting fields to update on save()
                                fields += [initiative, alliance.initiatives.reset_timer(initiative)]
                                unaffordable.append(v.initiative_loss[initiative])
                    #First we calculated what the alliance in question could afford
                    #now we insert newsitems for the relevant officers
                    #about which initiatives got shut down from lack of funding
                    txt = ''
                    for init in unaffordable:
                        txt += "%s, " % init
                    txt = txt[:-2]
                    alliance.initiatives.save()
                    for officer in alliance.members.filter(Q(permissions__banking=True)|Q(permissions__founder=True)):
                        news.initiative_recalled(officer, txt)
                utils.atomic_transaction(
                    Bank, 
                    alliance.bank.pk, 
                    {'budget': {'action': 'add', 'amount': alliance.bank.budget - budget}}
                )
                #then we set bankstats
                #the reason why bankstats are set after the atomic database commit
                #is to avoid accidentally saving updates twice
                #in case an exception is thrown by the atomic transaction
                income.update(expenditures) #for iterability
                income.pop('total') #not a field in bankstats
                for field in income:
                    bankstats.__dict__[field] += income[field]
                bankstats.save()

            except IntegrityError:
                alliance.bank.refresh_from_db()
                continue
            break
        #end while
    #end for
    return add_budget()


def add_budget():
    #alliance members gets paid first, then regular nations
    for alliance in Alliance.objects.select_related('initiatives').annotate(membercount=Count('members')).filter(membercount__gte=1):
        for member in alliance.members.filter(vacation=False, deleted=False).iterator():
            while True:
                income = nation_income(member)
                if income['income'] != 0:
                    try:
                        utils.atomic_transaction(Nation, member.pk, {
                            'budget': {'action': 'add', 'amount': income['income']}
                        })
                    except IntegrityError: #in case something else is using the member
                        member.refresh_from_db()
                        continue
                break
    #allianceless nations just gets a update query
    Nation.objects.filter(
        vacation=False, 
        deleted=False, 
        alliance=None, 
        budget__lt=F('gdp') * 2,
    ).update(budget=F('budget') + F('gdp') / 72)



#hourly check for vacation-eligible nations and subsequent placing them in it
@periodic_task(run_every=crontab(minute="5", hour="*", day_of_week="*"))
def vaccheck():
    Nation.objects.filter(last_seen__gt=timezone.now() - inactivedelta())



@periodic_task(run_every=crontab(minute="0", hour="0, 12", day_of_week="*"))
def turnchange(debug=False):
    for nation in Nation.objects.select_related('alliance__initiatives').filter(deleted=False, vacation=False).iterator():
        while True:
            try:
                approval = qol = growth = FI = mg = manpower = research = rebels = 0
                
                #base material gain
                oil = oilgain(nation)
                reserveloss = oilbase(nation)
                rm = rmgain(nation)
                food = foodgain(nation)
                mg = mggain(nation, rm+nation.rm, oil+nation.oil)
                basedecay = mgbase(nation, rm+nation.rm, oil+nation.oil)
                oil -= basedecay
                rm -= basedecay
                ##################
                ## other stuff lol
                ##################
                research = researchgain(nation)
                approval = approvalchange(nation)
                gdpchange = nation.growth
                qol = qolgain(nation)
                FI = FIchanges(nation)
                manpower = manpowergain(nation)
                healthcare = healthcaredecay(nation)
                stability = stabilitygain(nation)
                soviet = sovietgain(nation)
                us = westerngain(nation)
                growth = growthchanges(nation)
                actions = {
                    'gdp': {'action': 'add', 'amount': nation.growth},
                    'growth': {'action': 'add', 'amount': growth},
                    'qol': {'action': 'add', 'amount': utils.attrchange(nation.qol, qol)},
                    'healthcare': {'action': 'add', 'amount': utils.attrchange(nation.healthcare, healthcare)},
                    'literacy': {'action': 'add', 'amount': utils.attrchange(nation.literacy, literacydecay(nation))},
                    'stability': {'action': 'add', 'amount': utils.attrchange(nation.stability, stability)},
                    'approval': {'action': 'add', 'amount': utils.attrchange(nation.approval, approval)},
                    'soviet_points': {'action': 'add', 'amount': utils.attrchange(nation.soviet_points, soviet, -100)},
                    'us_points': {'action': 'add', 'amount': utils.attrchange(nation.us_points, us, -100)},
                    'reputation': {'action': 'add', 'amount': utils.attrchange(nation.reputation, 5)},
                    'rebels': {'action': 'add', 'amount': utils.attrchange(nation.rebels, rebels)},
                    'manpower': {'action': 'add', 'amount': utils.attrchange(nation.manpower, manpower)},
                    'research': {'action': 'add', 'amount': research},
                    'oilreserves': {'action': 'subtract', 'amount': reserveloss},
                    'FI': {'action': 'add', 'amount': FI},
                    'oil': {'action': 'add', 'amount': oil},
                    'rm': {'action': 'add', 'amount': rm},
                    'mg': {'action': 'add', 'amount': mg},
                    'food': {'action': 'add', 'amount': food},
                }
                if nation.gdp + gdpchange > nation.maxgdp:
                    actions.update({'maxgdp': {'action': 'set', 'amount': nation.gdp + gdpchange}})
                utils.atomic_transaction(Nation, nation.pk, actions)
            except IntegrityError:
                nation.refresh_from_db()
                continue
            eventhandler.trigger_events(nation)
            break
    return milturn()


def milturn(debug=False):
    Military.objects.filter(
        nation__vacation=False, 
        nation__deleted=False, 
        training__gt=0).update(training=F('training') - 1)
    return econturn()


def econturn(debug=False):

    Econdata.objects.filter(
        nation__vacation=False, 
        nation__deleted=False,
        ).update(
            labor=1,
            expedition=False,
            nationalize=False,
        )
    Econdata.objects.filter(
        nation__vacation=False, 
        nation__deleted=False,
        nation__subregion__in=v.latin_america,
        ).update(
            drugs=F('drugs') + 1,
        )
    Econdata.objects.filter(
        nation__vacation=False, 
        nation__deleted=False,
        nation__subregion__in=v.africa,
        ).update(
            diamonds=F('diamonds') + 1,
        )
    return allianceturn()


def allianceturn(debug=False):
    for alliance in Alliance.objects.all().iterator():
        try:
            totalgdp = alliance.members.filter(deleted=False, vacation=False).aggregate(Sum('gdp'))['gdp__sum']
            alliance.averagegdp = totalgdp / alliance.members.filter(deleted=False, vacation=False).count()
            alliance.save(update_fields=['averagegdp'])
        except: #nobody in the alliance
            pass
    Memberstats.objects.all().update(oil=0, mg=0, rm=0, food=0, budget=0)
    return warcleanup()


def warcleanup(debug=False):
    War.objects.all().update(attacked=False, defended=False, airattacked=False, airdefended=False, navyattacked=False, navydefended=False)
    War.objects.filter(over=True, timestamp__lte=timezone.now()).delete()
    return marketturn()


def marketturn(debug=False):
    market = Market.objects.latest('pk')
    new_market = Market()
    for field in v.resources[1:]: #inheriting the counters
        new_market.__dict__['%s_counter' % field] = market.__dict__['%s_counter' % field]
    if new_market.pk < 5:
        new_market.change = random.randint(-2, 2)
    else: #calculating the changes in market
        lastbought = Marketlog.objects.filter(turn=market.pk-1, cost__gt=0).aggregate(Sum('cost'))['cost__sum']
        lastsold = Marketlog.objects.filter(turn=market.pk-1, cost__lt=0).aggregate(Sum('cost'))['cost__sum']
        bought = Marketlog.objects.filter(turn=market.pk, cost__gt=0).aggregate(Sum('cost'))['cost__sum']
        sold = Marketlog.objects.filter(turn=market.pk, cost__lt=0).aggregate(Sum('cost'))['cost__sum']
    #setting new thresholds
    count = Nation.objects.filter(vacation=False, deleted=False).count()

    stats = Nation.objects.filter(vacation=False, deleted=False).aggregate(
        Sum('rm'), 
        Sum('mines'),
        Sum('oil'), 
        Sum('wells'),
        Sum('mg'), 
        Sum('factories'),
        Sum('food'),
        Sum('universities'), 
        Sum('land'), #food is more complicated than the rest
        Avg('researchdata__foodtech'),
        Avg('researchdata__urbantech'),
        Avg('econdata__foodproduction'),
    )
    print stats
    for field in stats:
        stats[field] = (stats[field] if stats[field] != None else 1)
    #accurate food production calculations
    available_land = stats['land__sum']
    multiplier = (1 - v.researchbonus['urbantech'])**stats['researchdata__urbantech__avg']
    for field in v.landcosts:
        available_land -= stats['%s__sum' % field] * int(v.landcosts[field] * multiplier)

    for field in v.foodproduction:
        land = field
        gain = v.foodproduction[field]

    food_prod = int((available_land / land) * gain) * stats['researchdata__foodtech__avg']
    food_prod = int(food_prod * stats['econdata__foodproduction__avg'])

    new_market.rm_threshold = (stats['rm__sum'] / float(stats['mines__sum'])) * sqrt(count/2)
    new_market.mg_threshold = (stats['mg__sum'] / float(stats['factories__sum'])) * sqrt(count/2)
    new_market.oil_threshold = (stats['oil__sum'] / float(stats['wells__sum'])) * sqrt(count/2)
    new_market.food_threshold = (stats['food__sum'] / float(food_prod)) * sqrt(count/2)
    print new_market.rm_threshold 
    print new_market.mg_threshold 
    print new_market.oil_threshold 
    print new_market.food_threshold
    #now double check if the threshold is greater than the lower limit
    #standard is 20
    for field in v.resources[1:]:
        print field
        new_market.__dict__['%s_threshold' % field]
        if new_market.__dict__['%s_threshold' % field] < v.min_threshold:
            print market.__dict__['%s_threshold' % field]
            new_market.__dict__['%s_threshold' % field] = v.min_threshold

    new_market.save()
    return infilgain()


def infilgain():
    for spy in Spy.objects.filter(nation__vacation=False, nation__deleted=False).select_related('nation', 'location').iterator():
        Spy.objects.filter(pk=spy.pk).update(infiltration=spy.infiltration + spygain(spy))
