from celery import shared_task, task
from celery.task.schedules import crontab
from celery.decorators import periodic_task
from django.db.models import Sum, Q, Count, Avg
from django.db import IntegrityError, OperationalError
from django.utils import timezone
from django.core.mail import send_mail
import traceback

import nation.utilities as utils
from nation.models import *
import nation.variables as v
import nation.news as news
from nation.turnchange import *
from math import sqrt
from nation.events import *
from nation.mod.multidetect import cron_detect




@periodic_task(run_every=crontab(minute="0, 10, 20, 30, 40, 50", hour="*", day_of_week="*"))
def money_gain():
    try:
        alliance_gain()
    except:
        from django.conf import settings
        send_mail(
            'Budget generation error', 
            traceback.format_exc(), 
            "admin@coldconflict.com", 
            [email for admin, email in settings.ADMINS]
        )

def alliance_gain():
    for alliance in Alliance.objects.select_related('bank', 'initiatives').all().iterator():
        bankstats = alliance.bankstats.get_or_create(turn=ID.objects.get().turn)[0]
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
                        if alliance.initiatives.__dict__[initiative.split('_')[0]]:
                            if alliance.bank.budget - expenditures[initiative] > 0:
                                alliance.bank.budget -= expenditures[initiative]
                            else:
                                alliance.initiatives.__dict__[initiative.split('_')[0]] = False
                                #collecting fields to update on sav0e()
                                fields += [initiative, alliance.initiatives.reset_timer(initiative.split('_')[0])]
                                unaffordable.append(v.initiative_loss[initiative.split('_')[0]])
                    #First we calculated what the alliance in question could afford
                    #now we insert newsitems for the relevant officers
                    #about which initiatives got shut down from lack of funding
                    txt = ''
                    for init in unaffordable:
                        txt += "%s, " % init
                    txt = txt[:-2]
                    alliance.initiatives.save()
                    for officer in alliance.members.filter(Q(permissions__template__banking=True)|Q(permissions__template__founder=True)):
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

            except OperationalError:
                alliance.bank.refresh_from_db()
                continue
            break
        #end while
    #end for
    return add_budget()



def add_budget():
    #alliance members gets paid first, then regular nations
    for alliance in Alliance.objects.select_related('initiatives').annotate(membercount=Count('members')).filter(membercount__gte=1):
        for member in alliance.members.filter(vacation=False, reset=False, deleted=False).iterator():
            while True:
                income = nation_income(member)
                try:
                    utils.atomic_transaction(Nation, member.pk, {
                        'budget': {'action': 'add', 'amount': income['income'] - income['tax']}
                    })
                except OperationalError: #in case something else is using the member
                    member.refresh_from_db()
                    continue
                break

    for nation in Nation.objects.actives().filter(
        alliance=None, 
        budget__lt=F('gdp') * 2):
        income = nation_income(nation)
        while True:
            try:
                utils.atomic_transaction(Nation, nation.pk, {'budget': {'action': 'add', 'amount': income['income']}})
            except OperationalError:
                nation.refresh_from_db()
                continue
            break


#hourly check for vacation-eligible nations and subsequent placing them in it
@periodic_task(run_every=crontab(minute="5", hour="*", day_of_week="*"))
def vaccheck():
    Nation.objects.actives().filter(last_seen__lt=timezone.now() - v.inactivedelta()).update(vacation=True)



@periodic_task(run_every=crontab(minute="0", hour="0, 12", day_of_week="*"))
def fire_turn():
    try:
        turnchange()
    except:
        from django.conf import settings
        send_mail(
            'Turn error', 
            traceback.format_exc(), 
            "admin@coldconflict.com", 
            [email for admin, email in settings.ADMINS]
        )



def turnchange(debug=False):
    ID.objects.all().update(turn=F('turn') + 1)
    turn = ID.objects.get().turn
    for nation in Nation.objects.actives().select_related('alliance__initiatives').iterator():
        create_snapshot(nation, turn)
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
                if debug:
                    print nation
                utils.atomic_transaction(Nation, nation.pk, actions)
            except OperationalError:
                nation.refresh_from_db()
                continue
            eventhandler.trigger_events(nation)
            trade_balancing(nation)
            break
    return milturn()


def milturn(debug=False):
    Military.objects.filter(
        nation__vacation=False, 
        nation__deleted=False, 
        nation__reset=False, 
        _training__gt=0).update(_training=F('_training') - 1)
    return econturn()


def econturn(debug=False):
    Econdata.objects.filter(
        nation__vacation=False, 
        nation__deleted=False,
        nation__reset=False, 
        ).update(
            labor=1,
            expedition=False,
            nationalize=False,
        )
    Econdata.objects.filter(
        nation__vacation=False, 
        nation__deleted=False,
        nation__reset=False, 
        nation__subregion__in=v.latin_america,
        ).update(
            drugs=F('drugs') + 1,
        )
    Econdata.objects.filter(
        nation__vacation=False, 
        nation__deleted=False,
        nation__reset=False, 
        nation__subregion__in=v.africa,
        ).update(
            diamonds=F('diamonds') + 1,
        )
    return allianceturn()


def allianceturn(debug=False):
    Memberstats.objects.all().update(budget=0)
    return warcleanup()


def warcleanup(debug=False):
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
    count = Nation.objects.actives().count()

    stats = Nation.objects.actives().aggregate(
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
    for field in stats:
        if field.split('__')[1] == 'sum':
            stats[field] = (stats[field] if stats[field] != None and stats[field] > 0 else 1)
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
    #now double check if the threshold is greater than the lower limit
    #standard is 20
    #and transfer over the price
    for field in v.resources[1:]:
        price = "%sprice" % field
        new_market.__dict__[price] = market.__dict__[price]
        if new_market.__dict__['%s_threshold' % field] < v.min_threshold:
            new_market.__dict__['%s_threshold' % field] = v.min_threshold

    new_market.save()
    return infilgain()


def infilgain():
    for spy in Spy.objects.filter(nation__vacation=False, nation__deleted=False, nation__reset=False).select_related('nation', 'location').iterator():
        Spy.objects.filter(pk=spy.pk).update(infiltration=spy.infiltration + spygain(spy), actioned=False)




def create_snapshot(nation, turn):
    s = Snapshot(nation=nation, turn=turn)
    for field in Nationattrs._meta.fields:
        s.__dict__[field.name] = nation.__dict__[field.name]
    s.save()


#regular ass tasks down here bruh

@shared_task
def meta_processing(agent, ip, userpk, referral=None):
    #part of detecting multis is using metadata
    #like user agents and whether or not referral links are submitted
    #normal users with actual browsers submit referral links most of the time
    nation = Nation.objects.get(user__pk=userpk)
    headermodel, created = Header.objects.get_or_create(nation=nation, user_agent=agent)
    if referral:
        headermodel.empty_referrals += 1
    else:
        headermodel.set_referrals += 1
    headermodel.save()
    IP.objects.get_or_create(nation=nation, IP=ip)
    #since we're doing all this database stuff
    #set the last seen var here as well
    nation.last_seen = timezone.now()
    nation.save(update_fields=['last_seen'])



#check for multis halfway between turns
#why?
#because
@periodic_task(run_every=crontab(minute="0", hour="6, 18", day_of_week="*"))
def multicheck():
    for nation in Nation.objects.actives().filter(cleared=False).iterator():
        cron_detect(nation)
    return clear_nations()


def clear_nations():
    query = Nation.objects.select_related('multimeter').actives().filter(cleared=False)
    for nation in query.iterator():
        if nation.multimeter.total() < 200 and nation.multimeter.highest() < 50:
            nation.cleared = True
            nation.save(update_fields=['cleared'])




def trade_balancing(nation):
    if nation.multimeter.trade_balances.all().count() == 0:
        change = nation.trade_balance
    else:
        old_tb = nation.multimeter.trade_balances.all().latest().trade_balance
        change = nation.trade_balance - old_tb
    nation.multimeter.trade_balances.create(
        trade_balance=nation.trade_balance,
        change=change)