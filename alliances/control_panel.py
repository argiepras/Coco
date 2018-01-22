from nation.models import Allianceoptions, Nation, Timers, Initiatives, Permissions, Basetemplate
from nation.decorators import alliance_required, nation_required
from .forms import *

from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from nation import news
from .utils import allianceheaders

import random

@login_required
@nation_required
@alliance_required
def view(request):
    nation = Nation.objects.select_related('alliance', 'permissions', 'alliance__bank', 'alliance__initiatives').get(user=request.user)
    if request.is_ajax():
        return post_handler(request)
    permissions = nation.permissions
    alliance = nation.alliance
    if not permissions.panel_access():
        return redirect('alliance:main')

    page = (request.GET['page'] if 'page' in request.GET else 'general')
    context = {'headers': allianceheaders(request), 'page': page}

    
    if page == 'general':
        context.update(general(nation, alliance))
        context.update(notifications(alliance))
    elif page == 'banking':
        context.update(banking(nation, alliance))
    elif page == 'members':
        if request.POST:
            context.update(members_post(request))
        context.update(members(nation, alliance))

    context.update({
        'pages': control_panel_pages(permissions, page),
        'permissions': permissions,
        'alliance': alliance,
        })
    return render(request, 'alliance/control_panel.html', context)


def control_panel_pages(permissions, page):
    pages = []
    iterables = ['general']
    if permissions.has_permission('banking') or permissions.has_permission('taxman'):
        iterables.append('banking')
    for permission in ['promote', 'demote_officer', 'change_officer', 'templating']:
        if permissions.has_permission(permission):
            iterables.append('members')
            break
    for x in iterables:
        pages.append({
                'active': (True if page == x else False),
                'name': x.capitalize(),
                'link': x,
            })
    if len(pages) == 1: 
        #if the officer only has permission to see the generals page
        #there's no need to create the nagivationals
        return False
    return pages


#this here creates new/alters existing permission templates
def change(request):
    nation = request.user.nation
    alliance = request.user.nation.alliance
    if not nation.permissions.has_permission('templating'):
        return redirect('alliance:control_panel')
    if request.method == "POST":
        form = newtemplateform(nation.permissions, request.POST)
        if form.is_valid():
            if request.POST['template'] == 'new':
                template = alliance.templates.create()
                result = "Template successfully created"
            else:
                result = "Template saved"
                try:
                    template = alliance.templates.get(pk=request.POST['template'])
                except:
                    return HttpResponse('Stop editing the html')
            template.from_form(form.cleaned_data)
            template.save()
        return HttpResponse(result)


    if not 'template' in request.GET:
        return redirect('alliance:control_panel')
    context = {}
    if request.GET['template'] == 'new':
        context.update({
            'form': newtemplateform(nation.permissions),
            'new': True,
            })
    else:
        try:
            template = alliance.templates.get(pk=request.GET['template'])
        except:
            return render(request, 'alliance/templates.html', {'error': True})
        context.update({'templatepk': template.pk})
        init = {
            'rank': template.rank,
            'title': template.title
            }
        for field in Basetemplate._meta.fields:
            init.update({field.name: getattr(template, field.name)})
        context.update({'form': newtemplateform(nation.permissions, initial=init)})

    return render(request, 'alliance/templates.html', context)





def post_handler(request):
    alliance = request.user.nation.alliance
    nation = request.user.nation
    if 'save' in request.POST:
        if request.POST['save'] == 'general':
            form = generals_form(request.POST)
            if form.is_valid():
                if nation.permissions.template.rank == 0:
                    hform = heirform(nation, request.POST)
                    if hform.is_valid():
                        heir = hform.cleaned_data['heir']
                        if alliance.permissions.filter(heir=True).exclude(member=heir).exists():
                            alliance.permissions.all().update(heir=False)
                        alliance.permissions.filter(member=heir).update(heir=True)
                alliance.anthem = form.cleaned_data['anthem']
                alliance.flag = form.cleaned_data['flag']
                if form.cleaned_data['description']:
                    alliance.description = form.cleaned_data['description']
                else:
                    alliance.description = "we r alliance, we ar goood at being and alliance. come at us bros. sponsored by the foundation for rehabilitation of rumsodomites"
                alliance.save(update_fields=['description', 'anthem', 'flag'])
            form = membertitleform(request.POST)
            if form.is_valid():
                alliance.templates.filter(rank=5).update(title=form.cleaned_data['title'])


        elif request.POST['save'] == 'banking':
            if nation.permissions.has_permission('banking') and nation.permissions.has_permission('taxman'):
                form = bankingform(request.POST)
            elif nation.permissions.has_permission('banking'):
                form = limitform(request.POST)
            elif nation.permissions.has_permission('taxman'):
                form = taxrateform(request.POST)
            if form.is_valid():
                for field in form.cleaned_data:
                    #sets either taxes or bank limits
                    if hasattr(alliance.bank, field) and nation.permissions.has_permission('banking'):
                        setattr(alliance.bank, field, form.cleaned_data[field])
                    elif nation.permissions.has_permission('taxman'):
                        setattr(alliance.initiatives, field, form.cleaned_data[field])
                alliance.bank.save(update_fields=['budget_limit'])
                alliance.initiatives.save()
            else:
                HttpResponse("Invalid input")

    elif 'toggle' in request.POST:
        field = request.POST['toggle']
        if field == "pk" or field == "id":
            return HttpResponse()
        if hasattr(Timers, field): #when toggling an initiative
            #have to make sure that there isn't an active countdown
            #and that a fresh countdown is set
            if nation.permissions.has_permission('initiatives'):
                initiatives = request.user.nation.alliance.initiatives
                if getattr(initiatives.timers, field) < timezone.now(): #not on a cooldown
                    setattr(initiatives.timers, field, timezone.now() + timezone.timedelta(hours=72))
                    initiatives.timers.save(update_fields=[field])
                    toggle(initiatives, field)

        elif hasattr(Allianceoptions, field):
            toggle(alliance, field)

        elif hasattr(alliance.bank, field):
            if nation.permissions.has_permission('banking'):
                if field == 'limit' or field == 'per_nation':
                    toggle(alliance.bank, field)

        return HttpResponse() #toggles are silent


    return HttpResponse("Settings successfully saved")


def toggle(model, field):
    if getattr(model, field) == False:
        setattr(model, field, True)
    else:
        setattr(model, field, False)
    model.save(update_fields=[field])


#POSTS frrom the member management stuff is regular POST, not ajax
#so it's handled in a different function
#just because
def members_post(request):
    nation = request.user.nation
    result = ''
    if 'promote' in request.POST and nation.permissions.has_permission('promote'):
        form = promoteform(nation, request.POST)
        if form.is_valid():
            news.promoted(form.cleaned_data['member'], form.cleaned_data['template'].rank)
            Permissions.objects.filter(member=form.cleaned_data['member']).update(template=form.cleaned_data['template'])
            result = "%s has been promoted" % form.cleaned_data['member'].name
    
    elif 'demote' in request.POST and nation.permissions.has_permission('demote_officer'):
        form = demoteform(nation, request.POST)
        if form.is_valid():
            member_template = nation.alliance.templates.get(rank=5)
            form.cleaned_data['officer'].permissions.template = member_template
            form.cleaned_data['officer'].permissions.save(update_fields=['template'])
            news.demoted(form.cleaned_data['officer'])
            result = "%s has been demoted to a regular member" % form.cleaned_data['officer'].name

    elif 'change' in request.POST and nation.permissions.has_permission('change_officer'):
        form = changeform(nation, request.POST)
        if form.is_valid():
            news.changed(form.cleaned_data['officer'], form.cleaned_data['template'].rank)
            Permissions.objects.filter(member=form.cleaned_data['officer']).update(template=form.cleaned_data['template'])
            result = "%ss rank has been changed" % form.cleaned_data['officer'].name

    if not result:
        result = "No can do cap'n"
    return {'result': result}

########
## context providing functions
######

def general(nation, alliance):
    membertitle = alliance.templates.values('title').get(rank=5)['title']
    x = {
        'generals': generals_form(initial={'anthem': alliance.anthem, 'flag': alliance.flag, 'description': alliance.description}),
        'membertitleform': membertitleform(initial={'title': membertitle}),
    }
    if nation.permissions.template.rank == 0:
        x.update({'heirform': heirform(nation, initial={'heir': (alliance.permissions.get(heir=True).member if alliance.permissions.filter(heir=True).exists() else None)})})
    if nation.permissions.has_permission('initiatives'):
        x.update(initiative_display(alliance.initiatives))
    return x


def banking(nation, alliance):
    context = {'bankingform': bankingform(initial={'budget_limit': alliance.bank.budget_limit})}
    if nation.permissions.has_permission('taxman'):
        #initial data for the tax form
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
        context.update({'taxrateform': taxrateform(initial=taxinit)})
    return context


def members(nation, alliance):
    context = {
        'promoteform': promoteform(nation),
        'changeform': changeform(nation),
        'demoteform': demoteform(nation),
        'templatesform': templatesform(nation),
    }
    return context


def notifications(alliance):
    options = []
    for field in Allianceoptions._meta.fields:
        options.append(
            {
                'tooltip': alliance._meta.get_field(field.name).help_text,
                'field': field.name,
                'text': alliance._meta.get_field(field.name).verbose_name,
                'checked': ('checked' if getattr(alliance, field.name) else ''),
            }
        )
    return {'options': options}


def initiative_display(initiatives):
    inits = [] #initiative display, less html
    cooldowns = False
    for init in v.initiativedisplay:
        app = {
            'status': initiatives.__dict__[init], 
            'txt': v.initiativedisplay[init]['display'],
            'tooltip': v.initiativedisplay[init]['tooltip'],
            'initiative': init,
            }
        if getattr(initiatives.timers, init) > timezone.now():
            app.update({
                'timer': getattr(initiatives.timers, init) - timezone.now(),
                'locked': True,
            })
            cooldowns = True
        else:
            app.update({'timer': False})
        inits.append(app)
    return {'initiatives': inits, 'cooldowns': cooldowns}