from django.shortcuts import render, redirect
from django.db.models import Count, Q
from django.contrib.auth.decorators import login_required
from django.core.paginator import *
from django.utils import timezone 
from django.db import transaction
from django.contrib.auth.models import User

from .models import *
from .allianceforms import *
import nation.news as news
from .decorators import alliance_required, nation_required
from .forms import declarationform
import nation.utilities as utils
import nation.turnchange as turnchange

@login_required
@nation_required
@alliance_required
def main(request):
    nation = Nation.objects.select_related('alliance', 'permissions', 'alliance__initiatives', 'alliance__bank').prefetch_related( \
        'alliance__members', 'alliance__permissions').get(user=request.user)
    alliance = nation.alliance
    context = {}
    result = ''
    if request.method == 'POST':
        if 'leave' in request.POST:
            alliance.kick(nation)
            result = "You say your goodbyes before being tossed by security."
            if alliance.members.all().count() - 1 == 0:  #member that just left isn't counted
                alliance.delete()                        #for whatever reason
            return alliancepage(request, alliance.pk, result)
        
        elif 'resign' in request.POST:
            if nation.permissions.panel_access():
                if alliance.members.all().count() == 1:
                    alliance.kick(nation)
                    alliance.delete()
                    return redirect('nation:main')
                else:
                    if alliance.permissions.filter(heir=True).count() > 0:
                        heir = alliance.permissions.get(heir=True)
                    elif alliance.permissions.filter(template__rank__gt=5).count() > 0:
                        for n in range(1, 5):
                            if alliance.permissions.filter(template__rank__gt=n).count() > 0:
                                heir = alliance.permissions.filter(template__rank__gt=n).order_by('?')[0]
                                break
                    else:
                        heir = alliance.permissions.all().order_by('?')[0]
                    heir.template = alliance.templates.get(rank=0)
                    heir.save()
                membertemplate = alliance.templates.get(rank=5)
                nation.permissions.template = membertemplate
                nation.permissions.save(update_fields=['template'])
                result = "Resignation gets handed over and you assume the role of an ordinary member"
        
        elif 'deposit' in request.POST:
            form = depositform(nation, request.POST)
            if form.is_valid():
                if form.cleaned_data['empty']:
                    result = "You can't deposit nothing!"
                else:
                    form.cleaned_data.pop('empty')
                    actions = {}
                    depositactions = {}
                    for field in form.cleaned_data:
                        actions.update({field: {'action': 'subtract', 'amount': form.cleaned_data[field]}})
                        depositactions.update({field: {'action': 'add', 'amount': form.cleaned_data[field]}})
                    utils.atomic_transaction(Nation, nation.pk, actions)
                    utils.atomic_transaction(Bank, alliance.bank.pk, depositactions)
                    banklogging(nation, actions, True)
                    result = "Deposited!"
            else:
                result = "Can't deposit that much!"
                

        elif 'withdraw' in request.POST and nation.permissions.can_withdraw():
            form = withdrawform(nation, request.POST)
            if form.is_valid():
                if form.cleaned_data['empty']:
                    result = "You can't withdraw nothing!"
                else:
                    form.cleaned_data.pop('empty')
                    actions = {} #moving to nation
                    withdraws = {} #setting bankstats for limiting
                    withdrawactions = {} #moving from bank
                    for field in form.cleaned_data:
                        actions.update({field: {'action': 'add', 'amount': form.cleaned_data[field]}})
                        withdrawactions.update({field: {'action': 'subtract', 'amount': form.cleaned_data[field]}})
                        withdraws.update({field: F(field) + form.cleaned_data[field]})

                    #atomic transactions for rollback if error happens
                    with transaction.atomic():
                        utils.atomic_transaction(Nation, nation.pk, actions)
                        utils.atomic_transaction(Bank, alliance.bank.pk, withdrawactions)
                        if nation.alliance.bank.limit:
                            if nation.alliance.bank.per_nation:
                                qfilter = {'nation': nation}
                            else:
                                qfilter = {'alliance': nation.alliance}
                            Memberstats.objects.select_for_update().filter(**qfilter).update(**withdraws)
                    banklogging(nation, actions, False)
                    result = "Withdrawal has been made!"
            else:
                result = "You can't withdraw more than your limit!"


        elif 'kick' in request.POST and nation.permissions.kickpeople():
            pks = request.POST.getlist('ids')
            kickees = alliance.members.all().select_related('permissions').filter(pk__in=pks)
            if not nation.permissions.template.kick or not nation.permissions.template.kick_officer:
                result = "You can't kick anyone! Stop this!"
            elif len(kickees):
                result = "You didn't select any members to kick!"
            else:
                tmp = 'But you do not have permission to kick '
                errs = ''
                for kickee in kickees:
                    if nation.permissions.can_kick(kickee):
                        alliance.kick(kickee)
                        news.kicked(kickee, alliance)
                    else:
                        errs += "%s, "
                    result = "Selected members have been purged from our ranks!"
                if errs != '':
                    result +=  tmp + errs[:-2]

        if 'masscomm' in request.POST:
            form = masscommform(request.POST)
            if form.is_valid():
                if request.POST['masscomm'] == 'everyone' and nation.permissions.can_masscomm():
                    members = alliance.members.all()
                    for member in members:
                        member.comms.create(sender=nation, masscomm=True, message=form.cleaned_data['message'])
                    nation.sent_comms.create(masscomm=True, message=form.cleaned_data['message'])
                    result = "Mass comm sent!"
                elif request.POST['masscomm'] == 'leadership' and nation.permissions.can_officercomm():
                    members = alliance.members.all()
                    for member in members:
                        member.comms.create(sender=nation, leadership=True, message=form.cleaned_data['message'])
                    nation.sent_comms.create(leadership=True, message=form.cleaned_data['message'])
                    result = "Leadership comm sent!"
                nation.actionlogging('mass commed')

    context.update({
        'result': result,
        'permissions': nation.permissions,
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
            try:
                invite = alliance.outstanding_invites.all().get(nation=nation)
            except:
                result = "You do not have an invite to this alliance!"
            else:
                if request.POST['invite'] == 'accept':
                    if nation.has_alliance():
                        nation = nation.alliance.kick(nation)
                    alliance.add_member(nation)
                    nation.invites.all().delete()
                    nation.news.filter(content__icontains="We have a recieved an invitation").delete()
                    return redirect('alliance:main')
                else:
                    invite.delete()
                    result = "Invitation refused."

        elif 'apply' in request.POST:
            if alliance.applications.all().filter(nation=nation).exists():
                result = "You have already submitted an application to this alliance!"
            else:
                alliance.applications.create(nation=nation)
                if alliance.comm_on_applicants:
                    for officer in alliance.members.filter(Q(permissions__template__founder=True)|Q(permissions__template__applicants=True)):
                        news.newapplicant(officer, nation)
                result = "Your application has been sent! Now we wait and see if they will accept it."

        elif 'unapply' in request.POST:
            if alliance.applications.all().filter(nation=nation).exists():
                alliance.applications.all().filter(nation=nation).delete()
                result = "Application has been retracted!"
            else:
                result = "You have not applied to become a member of %s!" % alliance.name
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


@login_required
@nation_required
def alliancerankings(request, page):
    #this big chunk retrieves alliances ordered by highest membercount
    context = {}
    alliances = Alliance.objects.annotate(membercount=Count('members')).order_by('-membercount')
    paginator = Paginator(alliances, 10)
    page = int(page)
    try:
        alliancelist = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        alliancelist = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        alliancelist = paginator.page(paginator.num_pages)

    context.update({
        'pages': utils.pagination(paginator, alliancelist),
        'alliances': alliancelist,
        })    
    return render(request, 'alliance/rankings.html', context)

