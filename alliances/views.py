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
from .control_panel import initiative_display


@login_required
@nation_required
@alliance_required
def main(request):
    nation = Nation.objects.select_related('alliance', 'permissions', 'alliance__initiatives', 'alliance__bank').prefetch_related( \
        'alliance__members', 'alliance__permissions').get(user=request.user)
    alliance = nation.alliance
    context = {}

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

                elif 'deposit' in request.POST:
                    result = ma.deposit(nation, request.POST)


        if result:
            context.update({'result': result})


    context.update({
        'overview': 'activetab',
        'permissions': nation.permissions,
        'inviteform': inviteform(),
        'alliance': alliance,
        'members': alliance.members.all(),
        'masscommform': masscommform(),
        'initiatives': initiative_display(alliance.initiatives),
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

    initiatives = [] #initiative display, less html
    for init in v.initiativedisplay:
        initiatives.append({'status': alliance.initiatives.__dict__[init], 'txt': v.initiativedisplay[init]})

    if nation.invites.all().filter(alliance=alliance).exists():
        context.update({'invite': True})
    if nation.applications.all().filter(alliance=alliance).exists():
        context.update({'applied': True})
    context.update({
        'members': alliance.members.all(), 
        'alliance': alliance, 
        'result': result, 
        'initiatives': initiative_display(alliance.initiatives),
    })
    return render(request, 'alliance/alliance.html', context)


def stats(request):
    pass

def bankinterface(request):
    pass

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
    context = {'invites': 'activetab'}
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
    context = {'applicants': 'activetab'}
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