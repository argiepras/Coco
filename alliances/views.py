from django.shortcuts import render, redirect
from django.db.models import Count, Q
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.generic.base import TemplateView
from django.views.generic.list import ListView
from django.db import transaction
from django.contrib.auth.models import User

from nation.models import *
from .forms import *
import nation.news as news
from nation.decorators import alliance_required, nation_required
import nation.utilities as utils
import nation.turnchange as turnchange
from . import memberactions as ma
from . import officeractions as oa
from .utils import allianceheaders
from .control_panel import initiative_display
import nation.turnchange as turnchange


@login_required
@nation_required
@alliance_required
def main(request):
    nation = Nation.objects.select_related('alliance', 'permissions', 'alliance__initiatives', 'alliance__bank').prefetch_related( \
        'alliance__members', 'alliance__permissions').get(user=request.user)
    alliance = nation.alliance
    context = {'headers': allianceheaders(request)}
    context.update(initiative_display(alliance.initiatives))

    if request.method == "POST":
        result = False
        if 'leave' in request.POST:
            result = ma.leave(nation)

        elif 'kick' in request.POST:
            result = oa.kick(nation, request.POST)

        elif 'resign' in request.POST:
            result = oa.resign(nation)

        elif 'invite' in request.POST:
            result = oa.invite_players(nation, request.POST)

        elif 'masscomm' in request.POST:
            result = oa.masscomm(nation, request.POST)

        else:
            with transaction.atomic():
                nation = Nation.objects.select_for_update().get(pk=nation.pk)
                if 'withdraw' in request.POST:
                    result = ma.withdraw(nation, request.POST)
                    alliance.bank.refresh_from_db()

                elif 'deposit' in request.POST:
                    result = ma.deposit(nation, request.POST)
                    alliance.bank.refresh_from_db()

        if not Alliance.objects.filter(pk=alliance.pk).exists():
            return redirect('nation:main')

        if result:
            context.update({'result': result})
    context.update({
        'permissions': nation.permissions,
        'inviteform': inviteform(),
        'alliance': alliance,
        'members': alliance.members.all(),
        'masscommform': masscommform(),
        'depositform': numberform(),
        })
    return render(request, 'alliance/main.html', context)


@login_required
@nation_required
def alliancepage(request, alliancepk, msg=False):
    nation = request.user.nation
    result = False
    context = {}
    #just some boilerplate stuff
    try:
        alliance = Alliance.objects.prefetch_related('members').select_related('initiatives').get(pk=alliancepk)
    except:
        return render(request, 'alliance/alliance404.html')
    try:
        useralliance = nation.alliance
        if useralliance == alliance:
            return redirect('alliance:main')
    except:
        pass

    if request.method == 'POST':
        if 'invite' in request.POST:
            result = ma.invite(nation, alliance, request.POST['action'])
        
        elif 'apply' in request.POST:
            result = ma.apply(nation, alliance)

        elif 'unapply' in request.POST:
            result = ma.apply(nation, alliance)

    context.update(initiative_display(alliance.initiatives))

    if nation.invites.all().filter(alliance=alliance).exists():
        context.update({'invite': True})
    if nation.applications.all().filter(alliance=alliance).exists():
        context.update({'applied': True})
    context.update({
        'members': alliance.members.all(), 
        'alliance': alliance, 
        'result': result, 
    })
    return render(request, 'alliance/alliance.html', context)


def stats(request):
    pass


@login_required
@nation_required
@alliance_required
def bankinterface(request):
    alliance = request.user.nation.alliance
    result = False
    if request.POST:
        if 'delete' in request.POST:
            result = oa.delete_log(request.user.nation, request.POST)
    average = alliance.averagegdp
    context = {
        'result': result,
        'headers': allianceheaders(request),
        'bank': alliance.bank,
        'wealthies': alliance.members.filter(gdp__gte=average*2).count(),
        'poorsies': alliance.members.filter(gdp__lte=average/2).count(),
        'middlelowers': alliance.members.filter(Q(gdp__gt=average/2)&Q(gdp__lte=average)).count(),
        'middleuppers': alliance.members.filter(Q(gdp__gt=average)&Q(gdp__lte=average*2)).count(),
    }
    incomebreakdown = Bankstats()
    incomebreakdown.populate(turnchange.alliancetotal(alliance, display=True))
    page = (request.GET['page'] if 'page' in request.GET else 1)
    pager, logs = utils.paginate_me(alliance.bank_logs.all(), 15, page)
    context.update({
        'pages': utils.pagination(pager, logs),
        'logentries': logs,
        'bankstats': incomebreakdown,
    })
    return render(request, 'alliance/bank.html', context)


@login_required
@nation_required
def alliancerankings(request):
    #this big chunk retrieves alliances ordered by highest membercount
    page = (request.GET['page'] if 'page' in request.GET else 1)
    alliances = Alliance.objects.annotate(membercount=Count('members')).order_by('-membercount')
    paginator, alliancelist = utils.paginate_me(alliances, 10, page)
    context = {
        'pages': utils.pagination(paginator, alliancelist),
        'alliances': alliancelist,
        }
    
    return render(request, 'alliance/rankings.html', context)

@login_required
@nation_required
def alliancedeclarations(request):
    context = {'declarationform': declarationform()}
    nation = request.user.nation
    if request.method == 'POST':
        context.update({'result': oa.declare(nation, request.POST)})

    page = (request.GET['page'] if 'page' in request.GET else 1)
    declarations = Alliancedeclaration.objects.select_related('nation', 'nation__settings', 'alliance').all().order_by('-pk')
    paginator, declist = utils.paginate_me(declarations, 10, page)

    context.update({
        'pages': utils.pagination(paginator, declist),
        'declarations': declist, 
    })
    return render(request, 'alliance/declarations.html', context)



@alliance_required
def chat(request):
    context = {}
    nation = request.user.nation
    alliance = nation.alliance
    result = False
    if request.method == "POST":
        context.update({'result': ma.post_chat(nation, request.POST)})
    page = (request.GET['page'] if 'page' in request.GET else 1)
    chats = Alliancechat.objects.select_related('nation').filter(alliance=alliance).order_by('-pk')
    paginator, chatslist = utils.paginate_me(chats, 10, page)
    context.update({
        'chatlist': chatslist, 
        'pages': utils.pagination(paginator, chatslist),
        'decform': declarationform(),
        'alliance': alliance,
        })
    return render(request, 'alliance/chat.html', context)



@login_required
@nation_required
def newalliance(request):
    if request.user.nation.has_alliance():
        return redirect('alliance:main')
    context = {}
    if request.POST:
        if 'create' in request.POST:
            with transaction.atomic():
                nation = Nation.objects.get(user=request.user)
                form = newallianceform(request.POST)
                if nation.budget < 150:
                    context.update({'result': "You cannot afford this!"})
                else:
                    if form.is_valid():
                        data = form.cleaned_data
                        if Alliance.objects.filter(name__iexact=form.cleaned_data['name']).exists():
                            result = "There is already an alliance with that name!"
                            return render(request, 'alliance/new.html', {'allianceform': newallianceform(), 'result': result})
                        
                        alliance = Alliance.objects.create(
                            name=form.cleaned_data['name'],
                            description=form.cleaned_data['description'],
                            founder=nation.name)
                        #founder permission set
                        #base officer
                        nation.budget -= 150
                        nation.save(update_fields=['budget'])
                        return redirect('alliance:main')
    form = newallianceform()
    return render(request, 'alliance/new.html', {'allianceform': form})

    return render(request, 'alliance/chat.html', context)



@login_required
@nation_required
@alliance_required
def invites(request):
    context = {'headers': allianceheaders(request)}
    nation = Nation.objects.select_related('alliance', 'permissions', 'permissions__template').prefetch_related(\
        'alliance__outstanding_invites', 'alliance__outstanding_invites__nation', 'alliance__outstanding_invites__inviter').get(user=request.user)
    alliance = nation.alliance
    permissions = nation.permissions
    if not permissions.has_permission('invite'):
        return redirect('alliance:main')

    if request.method == 'POST':
        context.update({'result': oa.revoke_invites(nation, request.POST)})
    invites = Invite.objects.select_related('nation').filter(alliance=alliance)
    context.update({'outstanding_invites': invites, 'alliance': alliance})
    return render(request, 'alliance/invites.html', context)


@login_required
@nation_required
@alliance_required
def applications(request):
    context = {'headers': allianceheaders(request)}
    nation = Nation.objects.select_related('alliance', 'permissions', 'permissions__template').prefetch_related(\
        'alliance__applications', 'alliance__applications__nation').get(user=request.user)
    permissions = nation.permissions
    if not permissions.has_permission('applicants'):
        return redirect('alliance:main')
    if request.method == 'POST':
        context.update({'result': oa.applicants(nation, request.POST)})

    context.update({
        'applications': nation.alliance.applications.select_related('nation').all(),
        'alliance': nation.alliance,
    })
    return render(request, 'alliance/applications.html', context)