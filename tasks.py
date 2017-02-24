import django
django.setup()
from celery import shared_task, task
from celery.task.schedules import crontab
from celery.decorators import periodic_task
from django.db.models import Sum, Q
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
def add_budget():
    for alliance in Alliance.objects.select_related('initiatives', 'bankstats').prefetch_related('members').all().iterator():
        initiatives = alliance.initiatives
        totalgdp = alliance.members.filter(deleted=False, vacation=False).aggregate(Sum('gdp'))['gdp__sum']
        try:
            alliance.averagegdp = totalgdp / alliance.members.filter(deleted=False, vacation=False).count()
            alliance.save(update_fields=['averagegdp'])
        except:
            continue #empty alliance
        alliancegain = 0
        for member in alliance.members.filter(vacation=False, deleted=False).iterator():
            if utils.vaccheck(member):
                continue
            while True:
                if member.budget > member.gdp*2:
                    break
                try:
                    taxrate = alliance.taxrate(member)
                    gain = int(round(member.gdp/72.0))
                    try:
                        tax = int(round(gain*float(taxrate)))
                    except:
                        tax = 0
                    budgetgain = gain-tax
                    tax = gain-budgetgain
                    alliancegain += tax
                    action = {'budget': {'action': 'add', 'amount': budgetgain}}
                    utils.atomic_transaction(Nation, member.pk, action)
                except IntegrityError: #in case something else is using the member
                    member.refresh_from_db()
                    continue
                break

        while True:
            try:
                action = {'budget': {'action': 'add', 'amount': alliancegain}}
                utils.atomic_transaction(Bank, alliance.bank.pk, action)
            except IntegrityError:
                continue
            break

    for nation in Nation.objects.filter(vacation=False, deleted=False, alliance=None).iterator():
        if utils.vaccheck(member):
            continue
        while True:
            if nation.budget > nation.gdp*2:
                break
            try:
                gain = round(nation.gdp/72.0)
                action = {'budget': {'action': 'add', 'amount': gain}}
                utils.atomic_transaction(Nation, nation.pk, action)
            except IntegrityError:
                nation.refresh_from_db()
                continue
            break
    return allianceloss()


def allianceloss():
    for alliance in Alliance.objects.select_related('bank', 'bankstats', 'initiatives').all().iterator():
        bankstats = alliance.bankstats
        while True:
            try:
                cost = 0
                healthcost = foicost = litcost = wepcost = 0
                membercount = alliance.members.filter(deleted=False, vacation=False).count()
                total_gdp = alliance.averagegdp * membercount
                unaffordable = []
                if alliance.initiatives.literacy:
                    litcost = round(total_gdp/72/25.0)
                    cost += litcost
                    bankstats.literacy_cost = litcost
                    if alliance.bank.budget < cost:
                        cost -= litcost
                        alliance.initiatives.literacy = False
                        alliance.initiatives.literacy_timer = timezone.now() + timezone.timedelta(hours=72)
                        unaffordable.append('literacy')

                if alliance.initiatives.healthcare:
                    healthcost = round(total_gdp/72/25.0)
                    bankstats.healthcare_cost = healthcost
                    cost += healthcost
                    if alliance.bank.budget < cost:
                        cost -= healthcost
                        alliance.initiatives.healthcare = False
                        alliance.initiatives.healthcare_timer = timezone.now() + timezone.timedelta(hours=72)
                        unaffordable.append('healthcare')

                if alliance.initiatives.freedom:
                    totlit = alliance.members.filter(deleted=False, vacation=False).aggregate(Sum('literacy'))['literacy__sum']
                    foicost = round(totlit/50.0)
                    cost += foicost
                    bankstats.freedom_cost = foicost
                    if alliance.bank.budget < cost:
                        cost -= foicost
                        alliance.initiatives.freedom = False
                        alliance.initiatives.freedom_timer = timezone.now() + timezone.timedelta(hours=72)
                        unaffordable.append('freedom of information')

                if alliance.initiatives.weapontrade:
                    totweps = alliance.members.filter(deleted=False, vacation=False).aggregate(Sum('military__weapons'))['military__weapons__sum']
                    wepcost = round(totweps/100.0)
                    cost += wepcost
                    bankstats.weapontrade_cost = wepcost
                    if alliance.bank.budget < cost:
                        cost -= wepcost
                        alliance.initiatives.weapontrade = False
                        alliance.initiatives.weapontrade_timer = timezone.now() + timezone.timedelta(hours=72)
                        unaffordable.append('weapon trading')

                if unaffordable:
                    txt = ''
                    for init in unaffordable:
                        txt += "%s, " % init
                    txt = txt[:-2]
                    alliance.initiatives.save()
                    for officer in alliance.members.filter(Q(permissions__banking=True)|Q(permissions__founder=True)):
                        news.initiative_recalled(officer, txt)
                action = {'budget': {'action': 'subtract', 'amount': cost}}
                utils.atomic_transaction(Bank, alliance.bank.pk, action)
                alliance.bankstats.healthcare_cost = healthcost
                alliance.bankstats.literacy_cost = litcost
                alliance.bankstats.freedom_cost = foicost
                alliance.bankstats.weapontrade_cost = wepcost
                alliance.bankstats.save()
            except IntegrityError:
                continue
            break




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
