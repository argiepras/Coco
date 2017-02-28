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
def set_avgdp():
    for alliance in Alliance.objects.annotate(membercount=Count('members')).filter(membercount__gte=1).iterator():
        Alliance.objects.filter(pk=alliance.pk).update(averagegdp=alliance.members.all().filter(\
            deleted=False, vacation=False, gdp__gt=0).aggregate(avgdp=Avg('gdp'))['avgdp'])
    return alliance_gain()


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
    for mil in Military.objects.filter(nation__vacation=False, nation__deleted=False).iterator():
        while True:
            try:
                action = {'training': {'action': 'add', 'amount': utils.attrchange(mil.training, -1)}}
                utils.atomic_transaction(Military, mil.pk, action)
            except IntegrityError:
                continue
            break
    return econturn()


def econturn(debug=False):
    for econ in Econdata.objects.filter(nation__vacation=False, nation__deleted=False).iterator():
        while True:
            try:
                action = {
                'nationalize': {'action': 'set', 'amount': False},
                'expedition': {'action': 'set', 'amount': False},
                'labor': {'action': 'set', 'amount': 1},
                'drugs': {'action': 'add', 'amount': utils.attrchange(econ.drugs, 1)},
                'diamonds': {'action': 'add', 'amount': utils.attrchange(econ.diamonds, 1)},
                }
                utils.atomic_transaction(Econdata, econ.pk, action)
            except IntegrityError:
                econ.refresh_from_db()
                continue
            break
    return allianceturn()


def allianceturn(debug=False):
    for alliance in Alliance.objects.all().iterator():
        try:
            totalgdp = alliance.members.filter(deleted=False, vacation=False).aggregate(Sum('gdp'))['gdp__sum']
            alliance.averagegdp = totalgdp / alliance.members.filter(deleted=False, vacation=False).count()
            alliance.save(update_fields=['averagegdp'])
        except: #nobody in the alliance
            pass
    return warcleanup()

def warcleanup(debug=False):
    War.objects.all().update(attacked=False, defended=False, airattacked=False, airdefended=False, navyattacked=False, navydefended=False)
    War.objects.filter(over=True, timestamp__lte=timezone.now()).delete()
    return memberstatsclear()


def memberstatsclear(debug=False):
    Memberstats.objects.all().update(oil=0, mg=0, rm=0, food=0, budget=0)
    return marketturn()


def marketturn(debug=False):
    market = Market.objects.latest('pk')


    return infilgain()

def infilgain():
    for spy in Spy.objects.filter(nation__vacation=False, nation__deleted=False).select_related('nation', 'location').iterator():
        Spy.objects.filter(pk=spy.pk).update(infiltration=spy.infiltration + spygain(spy))
