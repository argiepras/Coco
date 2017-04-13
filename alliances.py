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
                result = "invalid form data"
                

        elif 'withdraw' in request.POST and nation.permissions.can_withdraw():
            form = withdrawform(nation, request.POST)
            if form.is_valid():
                if form.cleaned_data['empty']:
                    result = "You can't deposit nothing!"
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
                        news.newapplicant(nation, alliance)
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


@login_required
@nation_required
@alliance_required
def alliancediscussion(request):
    nation = request.user.nation
    context = {}
    try:
        alliance = nation.member.alliance
    except:
        return redirect('nation:main')
    if request.method == "POST":
        if 'post' in request.POST:
            form = declarationform(request.POST)
            if form.is_valid():
                alliance.declarations.create(message=form.cleaned_data['message'], nation=nation)
                result = "Declaration announced!"
            else:
                result = "Your message is too long!"
            context.update({'result': result})

    context.update({'declarations': decs, 'form': declarationform(), 'name': alliance.name})
    decs = alliance.declarations.all().order_by('-pk')
    return render(request, 'alliance/discussions.html', context)


@login_required
@nation_required
@alliance_required
def invites(request):
    context = {}
    result = False
    nation = Nation.objects.select_related('alliance', 'permissions', 'permissions__template').prefetch_related(\
        'alliance__outstanding_invites', 'alliance__outstanding_invites__nation', 'alliance__outstanding_invites__inviter').get(user=request.user)
    alliance = nation.alliance
    permissions = nation.permissions
    if not permissions.panel_access():
        return redirect('alliance:main')
    if not permissions.can_invites():
        return render(request, 'alliance/notallowed.html')

    if request.method == 'POST':
        if 'revoke' in request.POST:
            if request.POST['revoke'] == 'all':
                alliance.outstanding_invites.all().delete()
                result = "All outstanding invites have been revoked!"
            elif request.POST['revoke'] == 'some':
                alliance.outstanding_invites.all().filter(pk__in=request.POST.getlist('ids')).delete()
                result = "Selected invites have been revoked!"
            else:
                invite = alliance.outstanding_invites.all().filter(pk=request.POST['revoke']).get()
                result = "Invite to %s has been revoked!"
                invite.delete()
        if result:
            context.update({'result': result})
    invites = Invite.objects.select_related('nation').filter(alliance=alliance)
    context.update({'invites': invites})
    return render(request, 'alliance/invites.html', context)

@login_required
@nation_required
@alliance_required
def applications(request):
    context = {}
    result = False
    nation = Nation.objects.select_related('alliance', 'permissions', 'permissions__template').prefetch_related(\
        'alliance__applications', 'alliance__applications__nation').get(user=request.user)
    alliance = nation.alliance
    permissions = nation.permissions
    if not permissions.panel_access():
        return redirect('alliance:main')
    if not permissions.can_applicants():
        return render(request, 'alliance/notallowed.html')

    if request.method == 'POST':
        pks = request.POST.getlist('ids')
        applications = alliance.applications.all().filter(pk__in=pks)
        if len(applications) == 0:
            result = "You didn't select any!"
        else:
            if 'accept' in request.POST:
                for applicant in applications:
                    alliance.add_member(applicant.nation)
                    applicant.delete()
                    news.acceptedapplication(applicant.nation, alliance)
                result = "The selected applicants are now members!"
            else:
                for applicant in applications:
                    applicant.delete()
                    news.rejectedapplication(applicant.nation, alliance)
                result = "The selected applicants have been rejected!"
    if result:
        context.update({'result': result})
    applications = Application.objects.select_related('nation').filter(alliance=alliance)
    context.update({
        'applications': applications,
        'alliance': alliance,

    })
    return render(request, 'alliance/applications.html', context)

@login_required
@nation_required
@alliance_required
def stats(request):
    pass

@login_required
@nation_required
@alliance_required
def control_panel(request):
    context = {}
    nation = Nation.objects.select_related('alliance', 'permissions', 'alliance__bank', 'alliance__initiatives').get(user=request.user)
    permissions = nation.permissions
    alliance = nation.alliance
    result = ''
    if not permissions.panel_access():
        return redirect('alliance:main')
    if request.method == "POST":
        if 'setdescription' in request.POST:
            form = descriptionform(request.POST)
            if form.is_valid():
                Alliance.objects.filter(pk=alliance.pk).update(description=form.cleaned_data['content'])
                result = "Description updated!"
            else:
                result = "Description too long!"

        if 'invite' in request.POST:
            form = inviteform(request.POST)
            if form.is_valid():
                target = utils.get_active_player(form.cleaned_data['name'])
                if target:
                    if alliance.outstanding_invites.all().filter(nation=target).exists():
                        result = "This nation has already recieved an invitation!"
                    else:
                        if target.has_alliance():
                            result = "%s is already a member of an alliance!" % target.name
                        target.invites.create(alliance=alliance, inviter=nation)
                        news.invited(target, alliance)
                        result = "Invitation sent!"
                else:
                    result = "That nation doesn't exist!"
            else:
                result = "Name too long! (max 30 characters)"

        elif 'bankingset' in request.POST and permissions.can_banking():
            form = bankingform(request.POST)
            if form.is_valid():
                data = form.cleaned_data
                for field in alliance.bank._meta.fields: #MEMES
                    if len(field.name.split('_')) == 1:
                        continue
                    if field.name.split('_')[1] == 'limit':
                        alliance.bank.__dict__[field.name] = data[field.name]
                if data['per_nation'] == 'per_nation':
                    alliance.bank.per_nation = True
                else:
                    alliance.bank.per_nation = False
                alliance.bank.limit = True
                alliance.bank.save()
                result = "New limits have been set!"
            else:
                result = "Invalid form data"

        elif 'no_limit' in request.POST and permissions.can_banking():
            alliance.bank.limit = False
            alliance.bank.save()
            result = "Limits on withdrawals have been removed!"


        elif 'initiativechange' in request.POST:
            initiative = request.POST['initiative']
            timer = v.now() + timezone.timedelta(days=3)
            if request.POST['initiativechange'] == 'on':
                if alliance.initiatives.__dict__[initiative]:
                    result = "This initiative is already enacted!"
                elif alliance.initiatives.__dict__["%s_timer" % initiative] > timezone.now():
                    result = "This initiative can't be changed so early!"
                else:
                    alliance.initiatives.__dict__[initiative] = True
                    alliance.initiatives.__dict__["%s_timer" % initiative] = timer
                    alliance.initiatives.save(update_fields=[initiative, "%s_timer" % initiative])
                    result = "Initiative has been enacted!"
            else:
                if not alliance.initiatives.__dict__[initiative]:
                    result = "This initiative has not been enacted!"
                elif alliance.initiatives.__dict__["%s_timer" % initiative] > timezone.now():
                    result = "This initiative can't be changed so early!"
                else:
                    alliance.initiatives.__dict__[initiative] = False
                    alliance.initiatives.__dict__["%s_timer" % initiative] = timer
                    alliance.initiatives.save(update_fields=[initiative, "%s_timer" % initiative])
                    result = "Initiative has been recalled!"

        elif 'promote' in request.POST and permissions.can_promote():
            form = promoteform(nation, request.POST)
            if form.is_valid():
                member = form.cleaned_data['member']
                template = form.cleaned_data['template']
                member.permissions.template = template
                member.permissions.save(update_fields=['template'])
                result = "%s has been promoted to %s!" % (member.name, template.title)
            else:
                result = "invalid form data"

        elif 'demote' in request.POST and permissions.can_demote():
            form = demoteform(nation, request.POST)
            if form.is_valid():
                officer = form.cleaned_data['officer']
                membertemplate = alliance.templates.all().get(rank=5)
                officer.permissions.template = membertemplate
                officer.permissions.save(update_fields=['template'])
                result = "%s has been demoted!" % officer.name
            else:
                result = "invalid form data"

        elif 'change' in request.POST and permissions.can_change():
            form = changeform(nation, request.POST)
            if form.is_valid():
                officer = form.cleaned_data['officer']
                newtemplate = form.cleaned_data['template']
                
                result = "%ss permissions have been changed!" % officer.name
            else:
                result = "invalid form data"

        elif 'membertitle' in request.POST and permissions.can_manage():
            form = membertitleform(request.POST)
            if form.is_valid():
                newtitle = form.cleaned_data['title']
                alliance.templates.filter(rank=5).update(title=newtitle)
                result = "New title has been set!"
            else:
                result = "Titles have to be between 2 and 30 characters!"

        elif 'setapplicants' in request.POST and permissions.can_applicants():
            form = applicantsetform(request.POST)
            if form.is_valid():
                choice = form.cleaned_data['choice']
                if choice == 'on' and alliance.accepts_applicants:
                    result = "We already accept applicants!"
                elif choice == 'off' and not alliance.accepts_applicants:
                    result = "We already reject applicants!"
                else:
                    choice = (True if choice == 'on' else False)
                    alliance.accepts_applicants = choice #to correctly set the form initial data
                    Alliance.objects.filter(pk=alliance.pk).update(accepts_applicants=choice)
                    verb = ('accept' if choice else 'reject')
                    result = "We now %s applicants!" % verb

        elif 'setcommapplicants' in request.POST and permissions.can_applicants():
            form = applicantcommform(request.POST)
            if form.is_valid():
                choice = form.cleaned_data['choice']
                if choice == 'on' and alliance.comm_on_applicants:
                    result = "We already notify on new applicants!"
                elif choice == 'off' and not alliance.comm_on_applicants:
                    result = "We don't notify on new applicants as it is!"
                else:
                    choice = (True if choice == 'on' else False)
                    alliance.comm_on_applicants = choice
                    alliance.save(update_fields=['comm_on_applicants'])
                    if choice:
                        result = "We now notify officers when nations apply!"
                    else:
                        result = "We no longer notify officers when nations apply!"

        elif 'setflag' in request.POST:
            form = flagform(request.POST)
            if form.is_valid():
                alliance.flag = form.cleaned_data['flag']
                alliance.save(update_fields=['flag'])
                result = "New flag set!"
            else:
                result = "Input too long! 100 characters max"

        elif 'setanthem' in request.POST:
            form = anthemform(request.POST)
            if form.is_valid():
                alliance.anthem = form.cleaned_data['anthem']
                alliance.save(update_fields=['anthem'])
                result = "New anthem set!"
            else:
                result = "Input too long! 15 characters max"

        elif 'taxes' in request.POST and permissions.is_taxman():
            form = taxrateform(request.POST)
            if form.is_valid():
                updates = []
                for field in form.cleaned_data:
                    alliance.initiatives.__dict__[field] = form.cleaned_data[field]
                    updates.append(field)
                alliance.initiatives.save(update_fields=updates)
                result = "Tax rates have been updated!"
            else:
                result = "invalid form data"


    #setting initial data for banking form
    bankinginit = {}
    if alliance.bank.limit:
        for field in alliance.bank._meta.fields: #MEMES
            if len(field.name.split('_')) == 1:
                continue
            if field.name.split('_')[1] == 'limit':
                bankinginit.update({field.name: alliance.bank.__dict__[field.name]})
        if alliance.bank.per_nation:
            bankinginit.update({'per_nation': 'per_nation'})
        else:
            bankinginit.update({'per_nation': 'total'})
    #initial data for the tax forum
    taxinit =  {}
    for field in alliance.initiatives._meta.fields:
        try:
            if field.name.split('_')[1] == 'tax':
                bracket = field.name
            else:
                continue
        except: #continue if not a tax rate
            continue
        taxinit.update({bracket: alliance.initiatives.__dict__[bracket]})
    membertemplate = alliance.templates.get(rank=5)
    acceptapplicant = {'choice': ('on' if alliance.accepts_applicants else 'off')}
    commapplicant = {'choice': ('on' if alliance.comm_on_applicants else 'off')}
    context.update({
        'result': result,
        'permissions': permissions,
        'alliance': alliance,
        'inviteform': inviteform(),
        'heirform': heirform(nation),
        'descriptionform': descriptionform(initial={'content': alliance.description}),
        'initiatives': initiative_display(alliance.initiatives),
        'bankingform': bankingform(initial=bankinginit),
        'promoteform': promoteform(nation),
        'changeform': changeform(nation),
        'demoteform': demoteform(nation),
        'membertitleform': membertitleform(initial={'title': membertemplate.title}),
        'applicantsetform': applicantsetform(initial=acceptapplicant),
        'taxrateform': taxrateform(initial=taxinit),
        'templatesform': templatesform(nation),
        'anthemform': anthemform(initial={'anthem': alliance.anthem}),
        'flagform': flagform(initial={'flag': alliance.flag}),
        'applicantcommform': applicantcommform(initial=commapplicant),
        })
    return render(request, 'alliance/control_panel.html', context)

@login_required
@nation_required
@alliance_required
def bankinterface(request, page):
    context = {}
    nation = Nation.objects.select_related('alliance', 'permissions', 'permissions__template', 'alliance__bank').get(user=request.user)
    permissions = nation.permissions
    alliance = nation.alliance
    result = ''
    if not permissions.can_banking(): #needs officer :DDDDD
        return redirect('alliance:main')
    #############
    ## log part
    #############
    if request.POST:
        if 'delete' in request.POST and permissions.logchange:
            try:
                alliance.bank_logs.all().get(pk=request.POST['delete']).delete()
                result = "Log entry deleted!"
            except:
                result = "Log entry doesn't exist!"

    paginator = Paginator(alliance.bank_logs.all().order_by('-pk'), 50)
    page = int(page)
    try:
        logentries = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        logentries = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        logentries = paginator.page(paginator.num_pages)

    ############3########
    ## info display part
    ###########
    #using a bankstats object for the member functions
    #easy to total
    #also means there's no need to fill out 0s when a field isn't added
    incomebreakdown = Bankstats()
    incomebreakdown.populate(turnchange.alliancetotal(alliance, display=True))

    context.update({
        'bankstats': incomebreakdown,
        'bank': alliance.bank,
        'result': result,
        'logentries': logentries,
        'pages': utils.pagination(paginator, logentries)
    })
    return render(request, 'alliance/bank.html', context)



@login_required
@nation_required
@alliance_required
def change(request):
    if not request.POST:
        return redirect('alliance:control_panel')
    nation = request.user.nation
    founder =(True if nation.permissions.template.founder else False)
    context = {'founder': founder}
    if 'new' in request.POST:
        context.update({
            'form': newtemplateform(nation.permissions),
            'new': True,
            })
        return render(request, 'alliance/templates.html', context)
    elif 'createnew' in request.POST:
        form = newtemplateform(nation.permissions, request.POST)
        if form.is_valid():
            data = form.cleaned_data
            template = Permissiontemplate()
            template.from_form(data)
            template.alliance = nation.alliance
            template.save()
            return render(request, 'alliance/templatesuccess.html')
        else:
            context.update({'result': form.errors})
            return render(request, 'alliance/templates.html', context)
    elif 'alter' in request.POST:
        form = templatesform(nation, request.POST)
        if form.is_valid():
            template = form.cleaned_data['template']
            init = {}
            for field in template._meta.fields[7:]:
                init.update({field.name: template.__dict__[field.name]})
            perm = ('founder' if template.founder else 'officer')
            init.update({
                'rank': template.rank,
                'title': template.title,
                })
            context.update({'form': newtemplateform(nation.permissions, initial=init), 'tmpk': template.pk,})
            return render(request, 'alliance/templates.html', context)
        else:
            result = form.errors
            context.update({'form': form, 'result': result})
            return render(request, 'alliance/templates.html', context)

    elif 'commitchange' in request.POST:
        form = newtemplateform(nation.permissions, request.POST)
        if form.is_valid():
            pk = request.POST['commitchange']
            try:
                template =nation.alliance.templates.get(pk=request.POST['commitchange'])
            except:
                return redirect('alliance:aa')
            templatename = template.title
            template.from_form(form.cleaned_data)
            template.save()
            context.update({'header': 'Template successfully change!'})
            return render(request, 'alliance/templatesuccess.html', context)
        else:
            context.update({'result': form.errors, 'form': form})
            return render(request, 'alliance/templates.html', context)
    return redirect('alliance:main')


@login_required
@nation_required
def alliancedeclarations(request, page):
    context = {}
    nation = request.user.nation
    result = ''
    if request.method == 'POST':
        if not nation.has_alliance():
            result = "You need to be in an alliance to post here!"
        if 'declare' in request.POST and result == '':
            if nation.permissions.is_officer():
                form = declarationform(request.POST)
                if form.is_valid():
                    if nation.budget > 100:
                        nation.alliance.declarations.create(content=form.cleaned_data['message'], nation=nation)
                        result = "Declaration made!"
                        utils.atomic_transaction(Nation, nation.pk, {'budget': {'action': 'subtract', 'amount': 100}})
                    else:
                        result = "You do not have enough money!"
                else:
                    result = form.errors
            else:
                result = "You need to be an officer to make alliance declarations"
            context.update({'result': result})
    declarations = Alliancedeclaration.objects.select_related('nation', 'nation__settings', 'alliance').all().order_by('-pk')
    paginator = Paginator(declarations, 10)
    page = int(page)
    try:
        declist = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        declist = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        declist = paginator.page(paginator.num_pages)

    if result:
        context.update({'result': result})
    context.update({
        'pages': utils.pagination(paginator, declist),
        'declarations': declist, 
        'declarationform': declarationform()
    })
    return render(request, 'alliance/declarations.html', context)

@login_required
@nation_required
def newalliance(request):
    if request.user.nation.has_alliance():
        return redirect('alliance:main')
    context = {}
    if request.POST:
        if 'create' in request.POST:
            nation = request.user.nation
            form = newallianceform(request.POST)
            if nation.budget < 150:
                context.update({'result': "You cannot afford this!"})
            else:
                if form.is_valid():
                    data = form.cleaned_data
                    if Alliance.objects.filter(name__iexact=form.cleaned_data['name']).exists():
                        result = "There is already an alliance with that name!"
                        return render(request, 'alliance/new.html', {'allianceform': newallianceform(), 'result': result})
                    
                    alliance = Alliance.objects.create(name=form.cleaned_data['name'],
                        description=form.cleaned_data['description'])
                    Initiatives.objects.create(alliance=alliance)
                    Memberstats.objects.create(alliance=alliance, nation=nation)
                    Bank.objects.create(alliance=alliance)
                    Bankstats.objects.create(alliance=alliance)
                    #founder permission set
                    founder = Permissiontemplate.objects.create(alliance=alliance, title=form.cleaned_data['founder_title'], 
                        founder=True, officer=True, rank=0)
                    founder.founded()
                    #base officer
                    Permissiontemplate.objects.create(alliance=alliance, title='officer', officer=True,
                        kick=True, mass_comm=True, invite=True, applicants=True, rank=3, promote=True)
                    #member template
                    alliance.templates.create(rank=5, title=form.cleaned_data['member_title'])
                    Permissions.objects.create(member=nation, alliance=alliance, template=founder)
                    Nation.objects.filter(pk=nation.pk).update(alliance=alliance)
                    action = {'budget': {'action': 'subtract', 'amount': 150}}
                    utils.atomic_transaction(Nation, nation.pk, action)
                    return redirect('alliance:main')
    form = newallianceform()
    return render(request, 'alliance/new.html', {'allianceform': form})

@alliance_required
def chat(request, page):
    context = {}
    nation = request.user.nation
    alliance = nation.alliance
    result = False
    if request.method == "POST":
        if "post" in request.POST:
            form = declarationform(request.POST)
            if form.is_valid():
                alliance.chat.create(nation=nation, content=form.cleaned_data['message'])
                result = "Message posted!"
            else:
                result = form.errors
    if result:
        context.update({'result': result})

    chats = Alliancechat.objects.select_related('nation').filter(alliance=alliance).order_by('-pk')
    paginator = Paginator(chats, 10)
    page = int(page)
    try:
        chatslist = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        chatslist = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        chatslist = paginator.page(paginator.num_pages)
    context.update({
        'chatlist': chatslist, 
        'decform': declarationform(),
        'alliance': alliance,
        })
    return render(request, 'alliance/chat.html', context)


def initiative_display(initiatives):
    inits = [] #initiative display, less html
    for init in v.initiativedisplay:
        app = {
            'status': initiatives.__dict__[init], 
            'txt': v.initiativedisplay[init]['display'],
            'tooltip': v.initiativedisplay[init]['tooltip'],
            'initiative': init,
            }
        if initiatives.__dict__['%s_timer' % init] > timezone.now():
            app.update({'timer': initiatives.__dict__['%s_timer' % init] - timezone.now()})
        else:
            app.update({'timer': False})
        inits.append(app)
    return inits



def banklogging(nation, actions, deposit):
    for resource in actions:
        nation.alliance.bank_logs.create(
            nation=nation,
            resource=resource,
            amount=actions[resource]['amount'],
            deposit=deposit
            )