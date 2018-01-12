from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import update_session_auth_hash
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.db import transaction
from django.utils import timezone
#django stuff

#then other stuff
from .models import *
from .forms import *
from .decorators import nation_required, novacation, nonation_required, reset_required
from .turnchange import nation_income
from . import utilities as utils
import news
import intelligence

import datetime as time
from math import sqrt
import random
# Create your views here.

def index(request):
    donors = Donor.objects.all()
    return render(request, 'nation/index.html', {'donors': donors})



#main page
@login_required
@nation_required
def main(request, msg=False):
    #msg is a result string passed from new nation creation
    context = {}
    nation = Nation.objects.select_related('military', 'alliance', 'settings').prefetch_related('offensives', 'defensives').get(user=request.user)
    if msg:
        context.update({'result': msg})
    try:
        attacking = nation.offensives.all().filter(over=False).get().defender
        atk = {
            'army': attacking.military.army,
            'training': attacking.military.training,
            'weapons': attacking.military.weapons,
            'planes': attacking.military.planes,
            'navy': attacking.military.navy,
            'flag': attacking.settings.showflag(),
            'nation': attacking,
        }
        context.update({'offensive': atk, 'atwar': True})
    except:
        pass
    try:
        defending = nation.defensives.all().filter(over=False).get().attacker
        deff = {
            'army': defending.military.army,
            'training': defending.military.training,
            'weapons': defending.military.weapons,
            'planes': defending.military.planes,
            'navy': defending.military.navy,
            'flag': defending.settings.showflag(),
            'nation': defending,
        }
        context.update({'defensive': deff, 'atwar': True})
    except:
        pass
    budgetgain = int(round(nation.gdp/72.0))
    tax = False
    if nation.alliance:
        taxrate = nation.alliance.taxrate(nation)
        try:
            tax = int(round(budgetgain*taxrate))
        except:
            tax = 0
    if nation.military.chems < 10 and nation.military.chems > 0:
        context.update({'chems_progress': nation.military.chems*10})
    context.update({
        'military': nation.military,
        'budgetgain': nation_income(nation),
        'flag': nation.settings.showflag(),
        'avatar': nation.settings.showportrait(),
        'reactor_progress': nation.military.reactor * 5,
    })
    return render(request, 'nation/main.html', context)

@login_required
@nonation_required
def new_nation(request):
    context = {'form': newnationform()}
    if request.method == "POST":
        form = newnationform(request.POST)
        if form.is_valid():
            if 'id' in form.cleaned_data:
                index = form.cleaned_data['id']
            try:
                index = int(index)
            except:
                nationid = ID.objects.get(pk=1)
                while True:
                    if Nation.objects.filter(index=nationid.index).exists():
                        nationid.index += 1
                    else:
                        index = nationid.index
                        nationid.save(update_fields=['index'])
                        break
            nation = Nation.objects.create(user=request.user, 
                index=index,
                name=form.cleaned_data['name'],
                creationip=request.META.get('REMOTE_ADDR'),
                _government=form.cleaned_data['government'],
                _economy=form.cleaned_data['economy'],
                subregion=form.cleaned_data['subregion'])
            Settings.objects.create(nation=nation)
            IP.objects.create(nation=nation, IP=request.META.get('REMOTE_ADDR'))
            Military.objects.create(nation=nation)
            Econdata.objects.create(nation=nation)
            Researchdata.objects.create(nation=nation)
            nation.news.create(event=True, content='newbie_event')
            context.update({'result': "Your nation has been successfully created!"})
        else:
            return render(request, 'nation/newnation.html', {'form': form})
    return render(request, 'nation/newnation.html', context)


@login_required
@reset_required
def reset_nation(request):
    context = {'form': newnationform()}
    if request.method == "POST":
        form = newnationform(request.POST)
        if form.is_valid():
            nation = request.user.nation
            for field in form.cleaned_data:
                if field == 'id':
                    continue
                nation.__dict__[field] = form.cleaned_data[field]
            nation.reset = False
            nation.save()
            return redirect('nation:main')
        else:
            context['form'] = form
    return render(request, 'nation/newnation.html', context)


def declarations(request):
    context = {}
    nation = request.user.nation
    result = ''
    page = (request.GET['page'] if 'page' in request.GET else 1)
    if request.method == 'POST':
        if 'declare' in request.POST:
            form = declarationform(request.POST)
            if form.is_valid():
                if nation.budget < v.declarationcost:
                    result = "You do not have enough money!"
                else:
                    actions = {'budget': {'action': 'subtract', 'amount': v.declarationcost}}
                    nation.declarations.create(region="none", content=form.cleaned_data['message'])
                    utils.atomic_transaction(Nation, nation.pk, actions)
                    request.user.nation.budget -= v.declarationcost
                    result = "Declaration made!"
            else:
                result = form.errors

        if 'delete' in request.POST and nation.settings.mod:
            if deldec(nation, request.POST['delete']) > 0:
                result = "Declaration deleted!"
            else:
                result = "Declaration not found"

    declarations = Declaration.objects.select_related(
        'nation', 
        'nation__settings').filter(
            region='none',
            deleted=False,
            ).order_by('-pk')
    paginator, declist = utils.paginate_me(declarations, 10, page)
    context.update({
        'mod': nation.settings.mod,
        'declarations': declist, 
        'decform': declarationform(),
        'deccost': v.declarationcost,
        'pages': utils.pagination(paginator, declist),
        'result': result,
        })
    return render(request, 'nation/declarations.html', context)


def regionaldeclarations(request):
    nation = request.user.nation
    context = {'region': nation.region()}
    page = (request.GET['page'] if 'page' in request.GET else 1)
    if request.method == 'POST':
        if 'declare' in request.POST:
            form = declarationform(request.POST)
            if form.is_valid():
                if nation.budget < v.declarationcost:
                    result = "You do not have enough money!"
                else:
                    actions = {'budget': {'action': 'subtract', 'amount': v.declarationcost}}
                    nation.declarations.create(region=nation.region(), content=form.cleaned_data['message'])
                    utils.atomic_transaction(Nation, nation.pk, actions)
                    result = "Declaration made!"
            else:
                result = form.errors
            context.update({'result': result})

        elif 'delete' in request.POST and nation.settings.mod:
            if deldec(nation, request.POST['delete']) > 0:
                result = "Declaration deleted!"
            else:
                result = "Declaration not found"

    declarations = Declaration.objects.select_related('nation', 'nation__settings').filter(region=nation.region()).order_by('-pk')
    paginator, declist = utils.paginate_me(declarations, 10, page)
    context.update({
        'mod': nation.settings.mod,
        'declarations': declist, 
        'decform': declarationform(),
        'pages': utils.pagination(paginator, declist)
        })
    return render(request, 'nation/regionaldiscussion.html', context)


def deldec(nation, decpk):
    if Declaration.objects.filter(pk=decpk).exists():
        nation.mod_actions.create(
            action="Deleted declaration",
            reason="",
            reversible=True,
            reverse=decpk,
            )
    return Declaration.objects.filter(pk=decpk).update(
        deleted=True,
        deleter=nation,
        deleted_timestamp=v.now()
        )


@nation_required
@login_required
def commpage(request):
    nation = request.user.nation
    page = (request.GET['page'] if 'page' in request.GET else 1)
    context = {}
    if request.method == 'POST':
        result = False
        if 'reply' in request.POST:
            ID = int(request.POST['reply'])
            form = commform(request.POST)
            if form.is_valid():
                if Nation.objects.filter(index=ID).exists():
                    recipient = Nation.objects.get(index=request.POST['reply'])
                    recipient.comms.create(message=form.cleaned_data['message'], sender=nation)
                    nation.sent_comms.create(message=form.cleaned_data['message'], recipient=recipient)
                    result = "Reply has been sent!"
                else:
                    result = "That nation no longer exists!"
            else:
                result = "Comm is too long!"
        elif 'delete' in request.POST:
            if request.POST['delete'] == 'all':
                nation.comms.all().delete()
                result = "All comms have been purged!"
            else:
                try:
                    comm = nation.comms.get(pk=request.POST['delete'])
                except:
                    result = "Comm doesn't exist!"
                else:
                    comm.delete()
                    result = "Communique deleted!"
        if result:
            context.update({'result': result})
    paginator, commslist = utils.paginate_me(nation.comms.all().order_by('-pk'), 10, page)
    #clearing unread flag
    pklist = []
    for comm in commslist:
        pklist.append(comm.pk)
    nation.comms.all().filter(pk__in=pklist).update(unread=False)
    #endclearing
    context.update({
        'comms': commslist, 
        'replyform': commform(),
        'pages': utils.pagination(paginator, commslist)
    })
    return render(request, 'nation/comms.html', context)


@nation_required
@login_required
def sentcomms(request):
    nation = request.user.nation
    context = {}
    page = (request.GET['page'] if 'page' in request.GET else 1)
    result = ''
    if request.method == 'POST':
        if 'delete' in request.POST:
            if request.POST['delete'] == 'all':
                nation.sent_comms.all().delete()
                result = "All comms have been purged!"
            else:
                comm = nation.sent_comms.filter(pk=request.POST['delete'])
                if len(comm) > 0:
                    comm.delete()
                    result = "Comm  deleted!"
                else:
                    result = "Comm doesn't exist!"
            context.update({'result': result})
    paginator, comms = utils.paginate_me(nation.sent_comms.all().order_by('-pk'), 10, page)
    context.update({
        'comms': comms, 
        'pages': utils.pagination(paginator, comms)
    })
    return render(request, 'nation/sentcomms.html', context)


def legal(request):
    return render(request, 'nation/legal.html')

def about(request):
    return render(request, 'nation/about.html')


#wrapper for world page view to enable custom urls
def nation_page(request, url):
    try:
        idnumber = Donorurl.objects.get(url=url).index
    except: 
        if Nation.objects.filter(deleted=False, reset=False, index=int(url)).exists():
            return nationpage(request, int(url))
        else:
            return render(request, 'nation/notfound.html', {'item': 'nation'})
    return nationpage(request, idnumber)


def nationpage(request, idnumber):
    context = {}
    result = False
    target = Nation.objects.select_related('military', 'settings').get(index=idnumber)
    if request.user.is_anonymous():
        nation = None
    else:
        nation = Nation.objects.select_related('military').prefetch_related('spies').get(user=request.user)    
        if nation.pk == target.pk:
            return redirect('nation:main')
        try:
            atwar = True
            war = War.objects.filter(Q(attacker=nation, defender=target, over=False)|Q(defender=nation, attacker=target, over=False)).get()
        except:
            atwar = False
            war = False
        warrable, reason = utils.can_attack(nation, target)

        #set up for the wars display
        wars = {}
        try:
            warattacking = target.offensives.all().filter(over=False).get().defender
            wars.update({'attacking': warattacking})
        except:
            pass
        try:
            wardefending = target.defensives.all().filter(over=False).get().attacker
            wars.update({'defending': wardefending})
        except:
            pass

        #set up spy display
        if nation.spies.filter(location=target).count() > 0:
            context.update({'spies': nation.spies.filter(location=target), 'check': True})
            if nation.spies.filter(location=target, specialty='Intelligence').exists():
                context.update({
                    'intel': True,
                    'chemical_progress': target.military.chems * 10,
                    'reactor_progress': target.military.reactor * 5,
                    })
        context.update({'wars': wars})

    #POST handling
    result = ''
    if request.method == "POST" and nation:
        if 'comm' in request.POST:
            form = commform(request.POST)
            if form.is_valid():
                if nation.sent_comms.all().filter(timestamp__gte=v.now()-time.timedelta(seconds=v.delay)).count() > v.commlimit:
                    result = "No spamming!"
                else:
                    target.comms.create(message=form.cleaned_data['message'], sender=nation)
                    nation.sent_comms.create(message=form.cleaned_data['message'], recipient=target)
                    result = "Comm sent!"
            else:
                result = "%s" % form.error


        elif 'infiltrate' in request.POST and not nation.vacation:
            form = spyselectform(nation, request.POST)
            if form.is_valid():
                spy = form.cleaned_data['spy']
                result = intelligence.infiltrate(target, spy)
            else:
                result = "Invalid spy selected!"

        elif 'war' in request.POST and warrable and not nation.vacation:
            if nation.military.weapons < nation.military.army/10:
                result = "You do not have the weaponry to attack!"
            else:
                if nation.protection > timezone.now():
                    Nation.objects.filter(user=request.user).update(protection=timezone.now())
                war = War.objects.create(defender=target, attacker=nation)
                news.wardec(nation, target)
                atwar = True
                result = "Foreign nationals from %s are rounded up and put into internment camps as the war declaration gets drafted and delivered!" % target.name

        elif 'attack' in request.POST and atwar and not nation.vacation:
            if war.has_attacked(nation, 'ground'):
                result = "Your troops need time to reorganize!"
            elif nation.military.army == 0:
                result = "You do not have an army to attack with!"
            elif nation.military.army < 5 and target.military.army > 5:
                result = "Your army has been decimated and refuses to fight!"
            elif nation.military.weapons < nation.military.army/20:
                result = "You do not have the weapons to carry out an attack!"
            else:
                if target.military.army <= 5:
                    return render(request, 'nation/warwin.html', war_win(nation, target, war))
                else:
                    return render(request, 'nation/battle.html', battle(nation, target, war))

        elif 'air' in request.POST and atwar and not nation.vacation:
            action = request.POST['air']
            if nation.military.planes == 0:
                result = "You do not have an air force!"
            elif war.has_attacked(nation, 'air'):
                result = "Your aircraft must refuel before their next attack!"
            elif nation.oil < 1:
                result = "You do not have enough fuel for an air attack!"
            else:
                if action == 'air':
                    if target.military.planes == 0:
                        result = "Enemy nation has no planes to bomb!"
                    else:
                        return render(request, 'nation/air.html', airbattle(nation, target, war))
                elif action == 'econ':
                    return render(request, 'nation/air.html', econbombing(nation, target, war))
                elif action == 'cities':
                    return render(request, 'nation/air.html', citybombing(nation, target, war))
                elif action == 'army':
                    if target.military.army < 2:
                        result = "Enemy military has already been decimated!"
                    else:
                        return render(request, 'nation/air.html', groundbombing(nation, target, war))
                elif action == 'chems':
                    if target.military.chems == 0:
                        result = "Enemy has no chemical weapons! This is pointless!"
                    else:
                        return render(request, 'nation/air.html', chembombing(nation, target, war))
                elif action == 'industry':
                    if target.factories == 0:
                        result = "There is no industry to bomb!"
                    else:
                        return render(request, 'nation/air.html', industrybombing(nation, target, war))
                elif action == 'oil':
                    if target.wells == 0:
                        result = "The enemy doesn't have any oil wells to bomb!"
                    else:
                        return render(request, 'nation/air.html', oilbombing(nation, target, war))
                elif action == 'orange':
                    if nation.military.chems < 10:
                        result = "You do not have the necessary chemical weapons!"
                    elif target.econdata.foodproduction == 0:
                        result = "Enemy is already unable to produce food!"
                    else:
                        return render(request, 'nation/air.html', agentorange(nation, target, war))

        elif 'chem' in request.POST and atwar and not nation.vacation:
            if nation.military.chems < 10:
                result = "You do not have chemical weapons!"
            elif nation.reputation < 10:
                result = "The world already hates us! Using chemical warfare now is a very bad idea!"
            else:
                return render(request, 'nation/chems.html', chems(nation, target, war))

        elif 'peace' in request.POST and atwar and not nation.vacation:
            if war.peace_offers.filter(nation=nation).exists():
                result = "You have already offered peace!"
            else:
                result = "Peace offer is signed and sent! Now we wait and see if they'll reply.."
                war.peace_offers.create(nation=nation)
                if war.peace_offers.count() == 2:
                    result = "Peace in our time."
                    waractions = {
                        'over': {'action': 'set', 'amount': True},
                        'ended': {'action': 'set', 'amount': v.now()},
                        'winner': {'action': 'set', 'amount': 'peace'}
                        }
                    news.peaceaccept(nation, target)
                    utils.atomic_transaction(War, war.pk, waractions)
                    utils.atomic_transaction(Warlog, war.warlog.pk, logactions)
                else:
                    news.peace(nation, target)

        elif 'naval' in request.POST and atwar and not nation.vacation:
            if war.has_attacked(nation, 'naval'):
                result = "Your fleet must reorganize before it can launch another attack!"
            elif target.military.army < 2:
                result = "The enemy  military has already been decimated!"
            else:
                return render(request, 'nation/naval.html', navalstrike(nation, target, war))

        elif 'nuke' in request.POST and atwar and not nation.vacation:
            if nation.military.nukes == 0:
                result = "You do not have any nukes!"
            else:
                return render(request, 'nation/nuked.html', nuked(nation, target))
    init = {}
    if result:
        context.update({'result': result})


    context.update({
        'target': target,
        'targetmilitary': target.military,
        'flag': target.settings.showflag(),
        'avatar': target.settings.showportrait(),
    })

    if nation:
        context.update({
            'aidform': aidform(nation),
            'commform': commform(),
            'warrable': warrable,
            'reason': reason,
            'atwar': atwar,
            'spycount': nation.spies.all().filter(location=nation).count(),
            'spyselectform': spyselectform(nation),
        })
        request.user.nation = nation #rebind original nation instance
    return render(request, 'nation/nation.html', context)


@nation_required
@login_required
def newspage(request):
    context = {}
    nation = request.user.nation
    page = (request.GET['page'] if 'page' in request.GET else 1)

    if request.method == "POST":
        if 'delete' in request.POST:
            if nation.news.filter(deletable=True).filter(pk=request.POST['delete']).exists():
                nation.news.filter(deletable=True).filter(pk=request.POST['delete']).delete()
                result = "News item deleted!"
            else:
                result = "That news item doesn't exist!"
        elif 'deleteall' in request.POST:
            nation.news.filter(deletable=True).delete()
            result = "All news items deleted!"
        elif 'event' in request.POST:
            from nation.events import eventhandler
            try:
                event = nation.news.filter(event=True).get(pk=request.POST['event'])
            except:
                result = "You do not have this event!"
            else:
                result = eventhandler.process_event(nation, event.content, request.POST['choice'])
                event.delete()
        context.update({'result': result})

    pager, newsitems = utils.paginate_me(nation.news.all(), 10, page)
    if page == 1:
        nation.news.filter(seen=False).update(seen=True)
    context.update({
        'pages': utils.pagination(pager, newsitems),
        'news': newsitems,
        })
    return render(request, 'nation/news.html', context)


def rankings(request):
    context = {}
    page = (request.GET['page'] if 'page' in request.GET else 1)
    paginator, nationlist = utils.paginate_me(Nation.objects.actives().select_related('settings').order_by('-gdp'), 15, page)
    if 'query' in request.GET:
        context.update(rankingsearch(request))
    context.update({
        'pages': utils.pagination(paginator, nationlist),
        'nations': nationlist,
        'searchform': searchform(),
        })
    return render(request, 'nation/rankings.html', context)


def regionalrankings(request, region):
    try:
        bigregion = v.regionshort[region]
    except:
        return render(request, 'nation/notfound.html', {'item': region})
    context = {}
    page = (request.GET['page'] if 'page' in request.GET else 1)
    if 'query' in request.GET:
        context.update(rankingsearch(request, bigregion))
    nations = Nation.objects.actives().filter(subregion=bigregion).order_by('-gdp')
    paginator, nationlist = utils.paginate_me(nations, 15, page)
    context.update({
        'nations': nationlist,
        'region': bigregion,
        'shortregion': region,
        'pages': utils.pagination(paginator, nationlist),
        'searchform': searchform(),
        })
    return render(request, 'nation/regionalrankings.html', context)


def rankingsearch(request, subregion=False):
    form = searchform(request.GET)
    if form.is_valid():
        query = Nation.objects.actives().filter(
            name__icontains=form.cleaned_data['query']
        )
        if subregion:
            query = query.filter(subregion=subregion)
        if query.count() == 0:
            query = [{'name': 'No nations found matching "%s"' % form.cleaned_data['query']}]
        result = {'results': query}
    else:
        #this may seem retarded
        #but this means there's no need to alter the html template
        #a "list" of dictionary (ies) in lieu of actual objects
        test = Nation(name='No nations found matching "%s"' % form.cleaned_data['query'])
        result = {'results': [test]}
    return result


@nation_required
@login_required
def nation404(request):
    return render(request, 'nation/404.html')


@nation_required
@login_required
@novacation
def research(request):
    import json
    nation = Nation.objects.select_related('researchdata').get(user=request.user)
    context = {}
    cost = researchcost(nation)
    if request.method == 'POST':
        img = "/static/research/"
        if nation.research < cost:
            context.update({'result': "Not enough research has been conducted!"})
        else:
            for field in list(nation.researchdata._meta.fields)[1:]:
                if field.name in request.POST:
                    img += request.POST[field.name] + '.jpg'
                    context.update({'img': img, 'result': v.researchflavor[field.name]})
                    rndactions = {field.name: {'action': 'add', 'amount': 1}}
                    actions = {
                        'research': {'action': 'subtract', 'amount': cost},
                        }
                    utils.atomic_transaction(Nation, nation.pk, actions)
                    utils.atomic_transaction(Researchdata, nation.researchdata.pk, rndactions)
                    nation.actionlogs.create(
                        action='researched %s' % field.name, 
                        cost=json.dumps({'research': cost}))
                    #refresh data
                    request.user.nation.refresh_from_db()
                    nation.researchdata.refresh_from_db()
                    cost = researchcost(nation)
    context.update({'cost': cost, 'research': nation.researchdata})
    return render(request, 'nation/research.html', context)


def researchcost(nation):
    research = nation.researchdata.research()*25+25
    research = (research if 0 < research else 15)
    return research


def mapview(request):
    return render(request, 'nation/map.html')


def about(request):
    return render(request, 'nation/about.html')


def statistics(request):
    warquery = War.objects.filter(over=False).order_by('-pk') #newest first
    page = (request.GET['page'] if 'page' in request.GET else 1)
    paginator, wars = utils.paginate_me(warquery, 10, page)
    context = {}
    #generate statistics
    #at some point this will get cached as to reduce server load
    stats = {
        'active1': Nation.objects.filter(last_seen__gte=timezone.now()-timezone.timedelta(hours=1)).count(),
        'active24': Nation.objects.filter(last_seen__gte=timezone.now()-timezone.timedelta(hours=24)).count(),
        'activeweek': Nation.objects.filter(last_seen__gte=timezone.now()-timezone.timedelta(days=7)).count(),
        'active30': Nation.objects.filter(last_seen__gte=timezone.now()-timezone.timedelta(days=30)).count(),
        'total_nations': Nation.objects.all().count(),
        'total_nations24': Nation.objects.filter(creationtime__gte=timezone.now()-timezone.timedelta(hours=24)).count(),
        'total_nations7': Nation.objects.filter(creationtime__gte=timezone.now()-timezone.timedelta(days=30)).count(),
        'reactors': Military.objects.filter(nation__deleted=False, nation__vacation=False, reactor=20).count(),
        'east': Nation.objects.actives().filter(alignment=1).count(),
        'neutral': Nation.objects.actives().filter(alignment=2).count(),
        'west': Nation.objects.actives().filter(alignment=3).count(),
        'activewars': War.objects.filter(over=False).count(),
        'commcount': Comm.objects.filter(timestamp__gte=timezone.now()-timezone.timedelta(hours=24)).count(),
    }
    #looping over the list of stuff instead of writing it out
    wantedstats = ['gdp', 'growth', 'universities', 'factories', 'oilreserves', 'wells', 'oil', 'mines', 'rm', 'food', 'uranium']
    for stat in wantedstats:
        stats.update({stat: Nation.objects.actives().aggregate(Sum(stat))['%s__sum' % stat]})

    wantedmilstats = ['army', 'navy', 'planes', 'weapons', 'nukes']
    for stat in wantedmilstats:
        stats.update({stat: Military.objects.filter(nation__deleted=False, nation__vacation=False).aggregate(Sum(stat))['%s__sum' % stat]})

    commands = Nation.objects.actives().filter(_economy__lte=33).count()
    mixed = Nation.objects.actives().filter(_economy__lte=66).count() - commands
    capitalists = Nation.objects.actives().count() - mixed
    stats.update({'commands': commands, 'mixed': mixed, 'capitalists': capitalists})

    prevgob = -1
    for gob in v.government:
        goober = v.government[gob].lower().replace(' ', '_')
        gob = (gob+1)*20
        stats.update({goober: Nation.objects.filter(_government__gt=prevgob, _government__lte=gob).count()})
        prevgob = gob


    context.update({
        'wars': wars, 
        'decform': declarationform(),
        'pages': utils.pagination(paginator, wars),
        'newstats': stats,
        })
    return render(request, 'nation/globalnews.html', context)



@login_required
@nation_required
def settings(request):
    nation = request.user.nation
    context = {}
    result = ''
    if request.method == "POST":
        if 'set_description' in request.POST:
            form = descriptionform(request.POST)
            if form.is_valid():
                Nation.objects.filter(pk=nation.pk).update(description=form.cleaned_data['description'])
                request.user.nation.description = form.cleaned_data['description']
                result = "Description updated!"
            else:
                result = form.errors

        elif 'setavatar' in request.POST:
            form = portraitform(request.POST)
            if form.is_valid():
                Settings.objects.filter(pk=nation.settings.pk).update(portrait=form.cleaned_data['portrait'], donatoravatar='none')
                nation.settings.portrait=form.cleaned_data['portrait']
                result = "New avatar set!"

            else:
                result = "Invalid choice (stop inspecting element)"

        elif 'setflag' in request.POST:
            form = flagform(request.POST)
            if form.is_valid():
                Settings.objects.filter(pk=nation.settings.pk).update(flag=form.cleaned_data['flag'], donatorflag='none')
                nation.settings.flag=form.cleaned_data['flag']
                result = "New flag set!"
            else:
                result = "Invalid choice (stop inspecting element)"

        elif 'custom' in request.POST:
            form = customavatarform(request.POST)
            if form.is_valid():
                if request.POST['custom'] == 'flag':
                    Settings.objects.filter(pk=nation.settings.pk).update(donatorflag=form.cleaned_data['url'])
                    nation.settings.donatorflag=form.cleaned_data['url']
                    result = "Custom flag set!"
                else:
                    Settings.objects.filter(pk=nation.settings.pk).update(donatoravatar=form.cleaned_data['url'])
                    nation.settings.donatoravatar=form.cleaned_data['url']
                    result = "Custom avatar set!"
            else:
                result = "invalid URL"

        elif 'setanthem' in request.POST:
            form = anthemform(request.POST)
            if form.is_valid():
                Settings.objects.filter(pk=nation.settings.pk).update(anthem=form.cleaned_data['anthem'])
                nation.settings.anthem=form.cleaned_data['anthem']
                result = "New anthem set!"
            else:
                result = "what are you even doing right now"

        elif 'newpassword' in request.POST:
            form = passwordform(request.POST)
            if form.is_valid():
                request.user.set_password(form.cleaned_data['p1'])
                request.user.save()
                update_session_auth_hash(request, request.user)
                result = "New password set!"
            else:
                result = "Both fields must match and be between 5-30 characters!"

        elif 'customurl' in request.POST and nation.settings.donor:
            form = donorurlform(request.POST)
            if form.is_valid():
                nation.donorurl.url = form.cleaned_data['url']
                result = "New url set!"
            else:
                nation.donorurl.url = ''
                result = "Custom URL has been reset and nation reverted back to using ID!"
            nation.donorurl.save()

        elif 'vacation' in request.POST:
            if request.POST['vacation'] == 'exit':
                if nation.vacation:
                    if nation.settings.vacation_timer > v.now():
                        result = "You cannot exit vacation mode yet!"
                    else:
                        Nation.objects.filter(pk=nation.pk).update(vacation=False)
                        nation.vacation=False
                        result = "Your nation resumes the world of the living!"
                else:
                    result = "You are not in vacation mode, you don't have the exit button, cut it out"
            else:
                if nation.vacation:
                    result = "You are already in vacation mode, you can't enter it twice and you don't have the button"
                elif nation.atwar():
                    result = "You can't enter vacation mode when you are at war!"
                else:
                    timer = v.now() + timezone.timedelta(days=7)
                    Settings.objects.filter(pk=nation.settings.pk).update(vacation_timer=timer)
                    Nation.objects.filter(pk=nation.pk).update(vacation=True)
                    nation.vacation = True
                    result = "You are now in vacation mode"

        elif 'customdesc' in request.POST:
            if request.POST['customdesc'] == 'title':
                form = titleform(request.POST)
                if form.is_valid():
                    nation.title = form.cleaned_data['desc']
                    if nation.title:
                        result = "New title set!"
                else:
                    nation.title = ''
                    result = 'Title has been reset to default!'
                nation.save(update_fields=['title'])
            else:
                form = descriptorform(request.POST)
                if form.is_valid():
                    nation.descriptor = form.cleaned_data['desc']
                    result = "New descriptor set!"
                else:
                    nation.descriptor = ''
                    result = "Descriptor has been reset to default!"   
                nation.save(update_fields=['descriptor'])

        elif 'set_autoplay' in request.POST:
            form = autoplayform(request.POST)
            if form.is_valid():
                if form.cleaned_data['autoplay'] == 'on':
                    nation.settings.autoplay = True
                else:
                    nation.settings.autoplay = False
                nation.settings.save()
                nation.settings.refresh_from_db()
                result = "Autoplay setting has been updated"

    if nation.settings.donor:
        donorurl = nation.donorurl.url
        context.update({'donorurlform': donorurlform(initial={'url': donorurl})})

    context.update({
        'result': result,
        'settings': nation.settings,
        'descriptionform': descriptionform(initial={'description': nation.description}),
        'flagform': flagform(initial={'flag': nation.settings.flag}),
        'portraitform': portraitform(initial={'portrait': nation.settings.portrait}),
        'anthemform': anthemform(initial={'anthem': nation.settings.anthem}),
        'customflagform': customavatarform(),
        'customavatarform': customavatarform(),
        'passwordform': passwordform(),
        'autoplayform': autoplayform(initial={'autoplay': ('on' if nation.settings.autoplay else 'off')}),
        'descriptorform': descriptorform(initial={'desc': nation.descriptor}),
        'titleform': titleform(initial={'desc': nation.title}),
        })
    return render(request, 'nation/settings.html', context)


#############
###BATTLES###
#############


#atomic transaction block
#because we commit quite a bit of data across different tables
#if an error occurs at any point
#nothing is saved
@transaction.atomic
def battle(attacker, defender, war):
    context = {}
    landloss = defender.land/100
    weaponloss = attacker.military.army/20
    attackdmg = (sqrt(attacker.military.army) * \
        sqrt(sqrt(attacker.military.weapons+1) * \
        sqrt(attacker.military.training+1) * sqrt(attacker.military.planes+1)))
    defenddmg  = (sqrt(defender.military.army) * \
        sqrt(sqrt(defender.military.weapons+1) * \
        sqrt(defender.military.training+1) * sqrt(defender.military.planes+1)))

    #first is win
    if attackdmg > defenddmg:
        ratio = (attackdmg - defenddmg) / float(attackdmg) #forces the result to be floating point
        defender_loss = int((((ratio * defender.military.army)+2)*0.75))
        attacker_loss = int((attacker.military.army*5)/(ratio*attacker.military.army))
        if attacker_loss >= defender_loss-2:
            attacker_loss = defender_loss - 10
        if attacker_loss > attacker.military.army:
            attacker_loss = attacker.military.army
        if defender_loss > defender.military.army:
            defender_loss = defender.military.army

        attacker_loss = (attacker_loss if attacker_loss > 0 else 0)
        defender_loss = (defender_loss if defender_loss > 0 else 0)

        if attacker_loss > 0:
            att_loss = "%s thousand" % attacker_loss
        else:
            att_loss = "%s" % attacker_loss
        if defender_loss > 0:
            def_loss = "%s thousand" % defender_loss
        else:
            defender_loss = 1
            def_loss = "%s thousand" % defender_loss
        output = "You won the battle! Your forces have killed %s enemy troops while \
        suffering %s casualties. Your army has occupied %s square kilometers \
        of enemy territory." % (def_loss, att_loss, landloss)
        #setting up dictionaries of actions to be taken in a secure DB transaction
        defactions = {
            'land': {'action': 'subtract', 'amount': landloss},
            'approval': {'action': 'add', 'amount': utils.attrchange(defender.approval, -2)},
            'manpower': {'action': 'add', 'amount': utils.attrchange(defender.manpower, -5)},
        }
        defmilactions = {
            'army': {'action': 'subtract', 'amount': defender_loss}
        }
        atkactions = {
            'land': {'action': 'add', 'amount': landloss},
            'approval': {'action': 'add', 'amount': utils.attrchange(attacker.approval, 2)},
            'manpower': {'action': 'add', 'amount': utils.attrchange(attacker.manpower, -1)},
        }
        atkmilactions = {
            'army': {'action': 'subtract', 'amount': attacker_loss},
            'weapons': {'action': 'subtract', 'amount': weaponloss}
        }
        if defender.alignment == 1: #commie
            atkactions.update({
                'soviet_points': {'action': 'add', 'amount': utils.attrchange(attacker.soviet_points, -5, -100)},
                'us_points': {'action': 'add', 'amount': utils.attrchange(attacker.us_points, 2, -100)},
                })
        elif defender.alignment == 3: #freedom
            atkactions.update({
                'soviet_points': {'action': 'add', 'amount': utils.attrchange(attacker.soviet_points, 2, -100)},
                'us_points': {'action': 'add', 'amount': utils.attrchange(attacker.us_points, -5, -100)},
                })
    #then is loss
    else:
        ratio = (defenddmg - attackdmg) / float(defenddmg)
        attacker_loss = int((((ratio * defender.military.army)+2)*0.75))
        defender_loss = int(attacker.military.army/(ratio*attacker.military.army))
        if defender_loss >= attacker_loss-2:
            defender_loss = attacker_loss-10
        if attacker_loss > attacker.military.army:
            attacker_loss = attacker.military.army

        attacker_loss = (attacker_loss if attacker_loss > 0 else 0)
        defender_loss = (defender_loss if defender_loss > 0 else 0)
        if attacker_loss > 0:
            att_loss = "%s thousand" % attacker_loss
        else:
            attacker_loss = 1
            att_loss = "%s thousand" % attacker_loss
        if defender_loss > 0:
            def_loss = "only %s thousand soldiers" % defender_loss
        else:
            def_loss = "nothing"
        output = "The enemy holds the frontline! You lose %s men \
        while the enemy loses %s!" % (att_loss, def_loss)

        defactions = {
            'approval': {'action': 'add', 'amount': utils.attrchange(defender.approval, 2)},
            'manpower': {'action': 'add', 'amount': utils.attrchange(defender.manpower, -1)},
        }
        defmilactions = {
            'army': {'action': 'subtract', 'amount': defender_loss}
        }
        atkactions = {
            'approval': {'action': 'add', 'amount': utils.attrchange(attacker.approval, -2)},
            'manpower': {'action': 'add', 'amount': utils.attrchange(attacker.manpower, -5)},
        }
        atkmilactions = {
            'army': {'action': 'subtract', 'amount': attacker_loss},
            'weapons': {'action': 'subtract', 'amount': weaponloss},
        }
        if defender.alignment == 1: #commie
            atkactions.update({
                'soviet_points': {'action': 'add', 'amount': utils.attrchange(attacker.soviet_points, -5, -100)},
                'us_points': {'action': 'add', 'amount': utils.attrchange(attacker.us_points, 2, -100)},
                })
        elif defender.alignment == 3: #freedom
            atkactions.update({
                'soviet_points': {'action': 'add', 'amount': utils.attrchange(attacker.soviet_points, 2, -100)},
                'us_points': {'action': 'subtract', 'amount': utils.attrchange(attacker.us_points, -5, -100)},
                })

    attack = war.attacks.create(attacker=attacker, attack_type="ground", lost=attacker_loss)
    attack.kills.create(loss_type="army", amount=defender_loss)
    if 'land' in defactions:
        war.gains.create(resource="land", amount=defactions['land']['amount'])
    #now for logging
    #for the mods and anti cheat shit
    news.groundengagement(attacker, defender, atkmilactions['army']['amount'], defmilactions['army']['amount'])
    #commit data to db
    utils.atomic_transaction(Nation, defender.pk, defactions)
    utils.atomic_transaction(Nation, attacker.pk, atkactions)
    utils.atomic_transaction(Military, defender.military.pk, defmilactions)
    utils.atomic_transaction(Military, attacker.military.pk, atkmilactions)
    context.update({'result': output, 'target': defender})
    return context

@transaction.atomic
def war_win(attacker, defender, war):
    landgain = defender.land/6
    landwin = (landgain if defender.land - landgain > v.minland else defender.land - v.minland)
    atkactions = {
        'land': {'action': 'add', 'amount': landwin},
        'gdp': {'action': 'add', 'amount': defender.gdp/5},
        'rm': {'action': 'add', 'amount': defender.rm/2},
        'oil': {'action': 'add', 'amount': defender.oil/2},
        'mg': {'action': 'add', 'amount': defender.mg/2},
        'factories': {'action': 'add', 'amount': defender.factories/4},
        'universities': {'action': 'add', 'amount': defender.universities/4},
        'food': {'action': 'add', 'amount': defender.food/2},
        'uranium': {'action': 'add', 'amount': defender.uranium},
        'oilreserves': {'action': 'add', 'amount': defender.oilreserves/6},
        'budget': {'action': 'add', 'amount': (defender.budget/2 if defender.budget>0 else 0)},
    }
    defactions = {
        'land': {'action': 'subtract', 'amount': landwin},
        'gdp': {'action': 'subtract', 'amount': defender.gdp/6},
        'rm': {'action': 'subtract', 'amount': defender.rm/2},
        'oil': {'action': 'subtract', 'amount': defender.oil/2},
        'mg': {'action': 'subtract', 'amount': defender.mg/2},
        'factories': {'action': 'subtract', 'amount': defender.factories/4},
        'universities': {'action': 'add', 'amount': defender.universities/4},
        'food': {'action': 'subtract', 'amount': defender.food/2},
        'uranium': {'action': 'subtract', 'amount': defender.uranium},
        'oilreserves': {'action': 'subtract', 'amount': defender.oilreserves/6},
        'budget': {'action': 'subtract', 'amount': (defender.budget/2 if defender.budget>0 else 0)},
        'protection': {'action': 'set', 'amount': timezone.now() + timezone.timedelta(days=2)},
    }
    defmilactions = {
        'army': {'action': 'set', 'amount': 10},
    }
    waractions = {
        'over': {'action': 'set', 'amount': True},
        'ended': {'action': 'set', 'amount': current_turn()},
        'winner': {'action': 'set', 'amount': attacker.name}
    }
    for resource in atkactions:
        war.gains.create(resource=resource, amount=atkactions[resource]['amount'])

    utils.atomic_transaction(Nation, attacker.pk, atkactions)
    utils.atomic_transaction(Nation, defender.pk, defactions)
    utils.atomic_transaction(Military, defender.military.pk, defmilactions)
    utils.atomic_transaction(War, war.pk, waractions)
    news.defeated(defender, attacker, defactions)
    return atkactions


@transaction.atomic
def chems(attacker, defender, war):
    atkactions = {
        'reputation': {'action': 'add', 'amount': utils.attrchange(attacker.reputation, -30)},
    }
    defactions = {
        'manpower': {'action': 'add', 'amount': utils.attrchange(defender.manpower, -11)},
        'gdp': {'action': 'subtract', 'amount': int(round(defender.gdp*v.chems['gdp']))}
    }
    defmilactions = {'army': {'action': 'subtract', 'amount': int(round(defender.military.army*v.chems['army']))}}
    attack = war.attacks.create(attacker=attacker, attack_type="chem")
    utils.atomic_transaction(Nation, attacker.pk, atkactions)
    utils.atomic_transaction(Nation, defender.pk, defactions)
    utils.atomic_transaction(Military, defender.military.pk, defmilactions)
    troops = defmilactions['army']['amount']
    gdp = defactions['gdp']['amount']
    attack.kills.create(loss_type="gdp", amount=gdp)
    attack.kills.create(loss_type="army", amount=troops)
    news.chemmed(attacker, defender, troops, gdp)
    context = {'gdp': gdp, 'troops': troops}
    return context


@transaction.atomic
def navalstrike(attacker, defender, war):
    context = {}
    logactions = {}
    #shore bombardment
    if attacker.military.navy/2 >= defender.military.navy:
        loss = defender.military.army/20
        loss = (loss if loss > 2 else 2)
        attack = war.attacks.create(
            attacker=attacker,
            attack_type="naval")
        attack.kills.create(loss_type="army", amount=loss)
        actions = {'army': {'action': 'subtract', 'amount': loss}}
        context.update({'img': 'war/bombardment.jpg', 'loss': loss})
        news.navalbombardment(attacker, defender, loss)
        img = 'war/bombardment.jpg'
        result = "You have bombarded their military positions, killing %s thousand soldiers." % loss
    #naval battle
    else:
        if attacker.military.navy > defender.military.navy:
            atkloss = 0
            defloss = defender.military.navy/15
            defloss = (defloss if defloss > 0 else 1)
            if attacker.military.weapons > defender.military.weapons:
                defloss += 1
            else:
                atkloss = 1
            if defloss > defender.military.navy:
                defloss = defender.military.navy
            result = "<p>You sink %s of the enemy ships</p>" % defloss
            if atkloss > 0:
                result += "<p>But they also sink %s of your ships</p>" % atkloss
            img = 'war/navy.jpg'
        else:
            defloss = 0
            atkloss = attacker.military.navy/15
            atkloss = (atkloss if atkloss > 0 else 1)
            if attacker.military.weapons < defender.military.weapons:
                atkloss += 1
            else:
                defloss = 1
            if atkloss > attacker.military.navy:
                atkloss = attacker.military.navy
            if defloss > 0:
                result = "<p>You sink %s of the enemy ships</p>" % defloss
            else:
                result = "<p>Your navy didn't manage to sink any enemy ships</p>"
            if atkloss > 0:
                result += "<p>But they also sink %s of your ships</p>" % atkloss
            img = 'war/navy2.jpg'
        news.navalengage(attacker, defender, atkloss, defloss)
        if atkloss > 0:
            atkactions = {'navy': {'action': 'subtract', 'amount': atkloss}}
            utils.atomic_transaction(Military, attacker.military.pk, atkactions)

        actions = {'navy': {'action': 'subtract', 'amount': defloss}}
        context.update({'kills': defloss, 'losses': atkloss})
        attack = war.attacks.create(attacker=attacker, attack_type="naval", lost=atkloss)
        attack.kills.create(loss_type="navy", amount=defloss)

    #commit dat data
    utils.atomic_transaction(Military, defender.military.pk, actions)
    context.update({'result': result, 'img': img})
    return context


@transaction.atomic
def airbattle(nation, target, war):
    img = 'war/bomb.jpg'
    success = airratio(nation.military, target.military)
    attack = war.attacks.create(attacker=nation, attack_type="air")
    nationactions = {'oil': {'action': 'subtract', 'amount': 1}}
    chance = random.randint(1, 10)
    if success > chance:
        attack.kills.create(loss_type="plane", amount=1)
        targetactions = {'planes': {'action': 'subtract', 'amount': 1}}
        result = "You have successfully bombed their airbases, reducing their airforce's strength."
        utils.atomic_transaction(Military, target.military.pk, targetactions)
    else:
        attack.lost = 1
        attack.save(update_fields=['lost'])
        nationmilactions = {'planes': {'action': 'subtract', 'amount': 1}}
        result = "Your airforce has been defeated over the enemy's skies! Your airforce has been weakened."
        utils.atomic_transaction(Military, nation.military.pk, nationmilactions)
    utils.atomic_transaction(Nation, nation.pk, nationactions)
    news.airbattle(nation, target, success > chance)
    return {'result': result, 'img': img}


@transaction.atomic
def econbombing(nation, target, war):
    img = 'war/bomb.jpg'
    loss = False
    attack = war.attacks.create(attacker=nation, attack_type="air")
    success = airratio(nation.military, target.military)
    nationactions = {'oil': {'action': 'subtract', 'amount': 1}}
    if success > random.randint(1, 10):
        loss = round(target.gdp/100.0)
        targetactions = {'gdp': {'action': 'subtract', 'amount': loss}, 'growth': {'action': 'subtract', 'amount': 5}}
        attack.kills.create(loss_type="gdp", amount=loss)
        attack.kills.create(loss_type="growth", amount=5)
        utils.atomic_transaction(Nation, target.pk, targetactions)
        result = "You have bombed their economic infrastructure, reducing growth by $5 million and their GDP by $%s million." % loss
    else:
        attack.lost = 1
        attack.save(update_fields=['lost'])
        nationmilactions = {'planes': {'action': 'subtract', 'amount': 1}}
        result = "Your airforce has been defeated over the enemy's skies! Your airforce has been weakened."
        utils.atomic_transaction(Military, nation.military.pk, nationmilactions)
    utils.atomic_transaction(Nation, nation.pk, nationactions)
    news.econbombing(nation, target, loss)
    return {'result': result, 'img': img}


@transaction.atomic
def groundbombing(nation, target, war):
    img = 'war/bomb.jpg'
    success = airratio(nation.military, target.military)
    attack = war.attacks.create(attacker=nation, attack_type="air")
    nationactions = {'oil': {'action': 'subtract', 'amount': 1}}
    loss = 0
    if success > random.randint(1, 10):
        loss = round(target.military.army/20.0)
        loss = (loss if loss > 2 else 2)
        attack.kills.create(loss_type="army", amount=loss)
        targetactions = {'army': {'action': 'subtract', 'amount': loss}}
        utils.atomic_transaction(Military, target.military.pk, targetactions)
        result = "You have bombed their military positions, killing %s thousand soldiers." % loss
    else:
        attack.lost = 1
        attack.save(update_fields=['lost'])
        nationmilactions = {'planes': {'action': 'subtract', 'amount': 1}}
        result = "Your airforce has been defeated over the enemy's skies! Your airforce has been weakened."
        utils.atomic_transaction(Military, nation.military.pk, nationmilactions)
    utils.atomic_transaction(Nation, nation.pk, nationactions)
    news.groundbombing(nation, target, loss)
    return {'result': result, 'img': img}


@transaction.atomic
def citybombing(nation, target, war):
    img = 'war/bomb.jpg'
    success = airratio(nation.military, target.military)
    attack = war.attacks.create(attacker=nation, attack_type="air")
    nationactions = {
        'oil': {'action': 'subtract', 'amount': 1}, 
        'reputation': {'action': 'add', 'amount': utils.attrchange(nation.reputation, -15)},
    }
    chance = random.randint(1, 10)
    if success > chance:
        targetactions = {
            'manpower': {'action': 'add', 'amount': utils.attrchange(target.manpower, -10)}, 
            'qol': {'action': 'add', 'amount': utils.attrchange(target.qol, -10)}
        }
        utils.atomic_transaction(Nation, target.pk, targetactions)
        attack.kills.create(loss_type="manpower", amount=10)
        attack.kills.create(loss_type="qol", amount=10)
        result = "You have bombed their civilian centers, reducing their quality of life and manpower. This atrocity has been condemned by many, and your reputation has dropped."
    else:
        attack.lost = 1
        attack.save(update_fields=['lost'])
        nationmilactions = {'planes': {'action': 'subtract', 'amount': 1}}
        result = "Your airforce has been defeated over the enemy's skies! Your airforce has been weakened."
        utils.atomic_transaction(Military, nation.military.pk, nationmilactions)
    utils.atomic_transaction(Nation, nation.pk, nationactions)
    news.citybombing(nation, target, success > chance)
    return {'result': result, 'img': img}

@transaction.atomic
def navalbombing(nation, target, war):
    img = 'war/navy2.jpg'
    success = airratio(nation.military, target.military)
    attack = war.attacks.create(attacker=nation, attack_type="air")
    nationactions = {'oil': {'action': 'subtract', 'amount': 1}}
    chance = random.randint(1, 10)
    if success > chance:
        targetactions = {'navy': {'action': 'subtract', 'amount': 1}}
        attack.kills.create(loss_type="navy", amount=1)
        result = "You have successfully bombed their navy, reducing their navys's strength."
        utils.atomic_transaction(Military, target.military.pk, targetactions)
    else:
        attack.lost = 1
        attack.save(update_fields=['lost'])
        nationmilactions = {'planes': {'action': 'subtract', 'amount': 1}}
        result = "Your airforce has been defeated over the enemy's naval base! Your airforce has been weakened."
        utils.atomic_transaction(Military, nation.military.pk, nationmilactions)
    utils.atomic_transaction(Nation, nation.pk, nationactions)
    news.navalbombing(nation, target, success > chance)
    return {'result': result, 'img': img}

@transaction.atomic
def industrybombing(nation, target, war):
    img = 'war/bomb.jpg'
    attack = war.attacks.create(attacker=nation, attack_type="air")
    success = airratio(nation.military, target.military)
    nationactions = {'oil': {'action': 'subtract', 'amount': 1}}
    chance = random.randint(1, 10)
    if success > chance:
        targetactions = {'factories': {'action': 'subtract', 'amount': 1}}
        utils.atomic_transaction(Nation, target.pk, targetactions)
        result = "You have bombed a factory, destroying it."
    else:
        nationactions.update({'reputation': {'action': 'add', 'amount': utils.attrchange(nation.reputation, -20)}})
        result = "Your bombing run missed the enemy's factory, and instead struck civilian housing killing thousands of innocents. You have been condemned throughout the world as a war criminal, dropping your reputation significantly."
    utils.atomic_transaction(Nation, nation.pk, nationactions)
    news.industrybombing(nation, target, success > chance)
    return {'result': result, 'img': img}

@transaction.atomic
def oilbombing(nation, target, war):
    img = 'war/oil.jpg'
    attack = war.attacks.create(attacker=nation, attack_type="air")
    success = airratio(nation.military, target.military)
    nationactions = {'oil': {'action': 'subtract', 'amount': 1}}
    chance = random.randint(1, 10)
    if success > chance:
        targetactions = {'wells': {'action': 'subtract', 'amount': 1}}
        attack.kills.create(loss_type="well", amount=1)
        utils.atomic_transaction(Nation, target.pk, targetactions)
        result = "You have bombed an oil well, destroying it."
    else:
        attack.lost = 1
        attack.save(update_fields=['lost'])
        nationmilactions = {'planes': {'action': 'subtract', 'amount': 1}}
        result = "Your airforce has been defeated over the enemy's skies! Your airforce has been weakened."
        utils.atomic_transaction(Military, nation.military.pk, nationmilactions)
    utils.atomic_transaction(Nation, nation.pk, nationactions)
    news.oilbombing(nation, target, success > chance)
    return {'result': result, 'img': img}

@transaction.atomic
def chembombing(nation, target, war):
    img = 'war/bomb.jpg'
    attack = war.attacks.create(attacker=nation, attack_type="air")
    success = airratio(nation.military, target.military)
    nationactions = {'oil': {'action': 'subtract', 'amount': 1}}
    chance = random.randint(1, 10)
    if success > chance:
        attack.kills.create(loss_type="chems", amount=1)
        targetactions = {'chems': {'action': 'subtract', 'amount': (2 if 1 < target.military.chems else 1)}}
        utils.atomic_transaction(Military, target.military.pk, targetactions)
        result = "You have bombed their chemical weapons storage facilities, reducing their chemical capabilities."
    else:
        attack.lost = 1
        attack.save(update_fields=['lost'])
        nationmilactions = {'planes': {'action': 'subtract', 'amount': 1}}
        utils.atomic_transaction(Military, nation.military.pk, nationmilactions)
        result = "Your airforce has been defeated over the enemy's skies! Your airforce has been weakened."
    utils.atomic_transaction(Nation, nation.pk, nationactions)
    news.chembombing(nation, target, success > chance)
    return {'result': result, 'img': img}

@transaction.atomic
def agentorange(nation, target, war):
    img = 'war/bomb.jpg'
    attack = war.attacks.create(attacker=nation, attack_type="air")
    success = airratio(nation.military, target.military)
    nationactions = {'oil': {'action': 'subtract', 'amount': 1}}
    chance = random.randint(1, 10)
    if success > chance:
        loss = (target.econdata.foodproduction/2 if target.econdata.foodproduction > 200 else 100)
        targetactions = {'foodproduction': {'action': 'subtract', 'amount': loss}}
        nationactions.update({'reputation': {'action': 'add', 'amount': utils.attrchange(nation.reputation, -10)}})
        utils.atomic_transaction(Econdata, target.econdata.pk, targetactions)
        result = "You have bombed their fields with agent orange, reducing their agriculture production."
    else:
        attack.lost = 1
        attack.save(update_fields=['lost'])
        nationmilactions = {'planes': {'action': 'subtract', 'amount': 1}}
        utils.atomic_transaction(Military, nation.military.pk, nationmilactions)
        result = "Your airforce has been defeated over the enemy's skies! Your airforce has been weakened."
    utils.atomic_transaction(Nation, nation.pk, nationactions)
    #inserting newsitem to target
    news.agentorange(nation, target, success > chance)
    return {'result': result, 'img': img}


def airratio(nationmil, targetmil):
    ratio = nationmil.planes - targetmil.planes
    if targetmil.planes == 0:
        return 11
    if ratio < 0:
        return 2
    elif ratio == 0:
        return 5
    elif ratio == 1:
        return 7
    elif ratio == 2:
        return 8
    elif ratio == 3:
        return 9
    return 11




#all effects of getting nuked, including global ones reside here
def nuked(nation, target):
    nukeractions = {
        'reputation': {'action': 'add', 'amount': utils.attrchange(nation.reputation, -75)},
    }
    nukermilactions = {
        'nukes': {'action': 'subtract', 'amount': 1},
    }
    manpower = target.manpower
    actions = {
        'gdp': {'action': 'set', 'amount': target.gdp/2},
        'growth': {'action': 'subtract', 'amount': 100},
        'factories': {'action': 'set', 'amount': target.factories/2},
        'manpower': {'action': 'subtract', 'amount': manpower}
    }
    reactor = target.military.reactor
    if reactor > 0:
        if random.randint(1, 2) == 1:
            reactor = 0

    nukes = target.military.nukes
    if nukes > 0:
        for nuke in range(nukes):
            if random.randint(1, 2) == 1:
                nukes -= 1
    milactions = {
        'army': {'action': 'set', 'amount': target.military.army * 0.25},
        'navy': {'action': 'set', 'amount': target.military.navy * 0.5},
        'planes': {'action': 'set', 'amount': target.military.planes * 0.5},
        'reactor': {'action': 'set', 'amount': reactor},
        'nukes': {'action': 'set', 'amount': nukes},
    }
    result = "A nuclear weapon has been detonated in %s! Economic development \
    in %s is hampered from the shock of such a weapon being unleashed, and the\
    radioactive fallout spreads across the planet, impacting the quality of life of billions!" \
    % (target.subregion, target.subregion)
    #global effects
    base_query = Nation.objects.actives().exclude(pk=nation.pk)
    growth_query = base_query.filter(subregion=target.subregion).exclude(pk=target.pk)
    growth_query.update(growth=F('growth') - 10)
    base_query.update(_qol=F('_qol') - 5)
    #cleaning up so qol can't go below 0
    base_query.filter(_qol__lt=0).update(_qol=0)

    #inserting news items
    for n in base_query.iterator():
        news.global_nuked(n, target.subregion)

    utils.atomic_transaction(Nation, nation.pk, nukeractions)
    utils.atomic_transaction(Military, nation.military.pk, nukermilactions)

    utils.atomic_transaction(Nation, target.pk, actions)
    utils.atomic_transaction(Military, target.military.pk, milactions)
    news.nuked(target, nation)
    return {'region': target.subregion, 'target': target.name}