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
                        nation.actionlogging('invited %s' % target.name)
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
                        if field.name in data:
                            alliance.bank.__dict__[field.name] = data[field.name]
                if data['per_nation'] == 'per_nation':
                    alliance.bank.per_nation = True
                else:
                    alliance.bank.per_nation = False
                alliance.bank.limit = True
                alliance.bank.save()
                result = "New limits have been set!"
                nation.actionlogging('set withdrawal limits')
            else:
                result = "Invalid form data"

        elif 'no_limit' in request.POST and permissions.can_banking():
            alliance.bank.limit = False
            alliance.bank.save()
            nation.actionlogging('removed withdrawal limits')
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
                nation.actionlogging('set alliance flag')
            else:
                result = "Input too long! 100 characters max"

        elif 'setanthem' in request.POST:
            form = anthemform(request.POST)
            if form.is_valid():
                alliance.anthem = form.cleaned_data['anthem']
                alliance.save(update_fields=['anthem'])
                result = "New anthem set!"
                nation.actionlogging('set alliance anthem')
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
                nation.actionlogging('set taxes')
                result = "Tax rates have been updated!"
            else:
                result = "invalid form data"

        elif 'setheir' in request.POST:
            form = heirform(nation, request.POST)
            if form.is_valid():
                alliance.permissions.all().update(heir=False)
                alliance.permissions.filter(member=form.cleaned_data['heir']).update(heir=True)
                result = "%s has been appointed as heir!" % form.cleaned_data['heir'].name
            else:
                result = "Invalid choice"


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
    heirinit = {'heir': (alliance.permissions.get(heir=True).member if alliance.permissions.filter(heir=True).exists() else None)}
    print heirinit
    context.update({
        'result': result,
        'permissions': permissions,
        'alliance': alliance,
        'inviteform': inviteform(),
        'heirform': heirform(nation, initial={'heir': (alliance.permissions.get(heir=True).member if alliance.permissions.filter(heir=True).exists() else None)}),
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
                alliance.bank_logs.filter(pk=request.POST['delete']).update(deleted=True)
                result = "Log entry deleted!"
                nation.actionlogging('deleted banklog')
            except:
                result = "Log entry doesn't exist!"

    paginator = Paginator(alliance.bank_logs.filter(deleted=False).order_by('-pk'), 50)
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



def banklogging(nation, actions, deposit):
    for resource in actions:
        nation.alliance.bank_logs.create(
            nation=nation,
            resource=resource,
            amount=actions[resource]['amount'],
            deposit=deposit
            )