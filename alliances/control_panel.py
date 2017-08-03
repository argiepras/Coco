from nation.models import Allianceoptions, Nation, Timers, Initiatives
from nation.decorators import alliance_required, nation_required
from .forms import *

from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone

import random

@login_required
@nation_required
@alliance_required
def view(request):
    print request.POST
    if request.is_ajax():
        return post_handler(request)
    page = (request.GET['page'] if 'page' in request.GET else 'general')
    context = {'panel': 'activetab', 'page': page}
    nation = Nation.objects.select_related('alliance', 'permissions', 'alliance__bank', 'alliance__initiatives').get(user=request.user)
    permissions = nation.permissions
    alliance = nation.alliance
    if not permissions.panel_access():
        return redirect('alliance:main')
    
    if page == 'general':
        context.update(general(nation, alliance))
        context.update(notifications(alliance))
    elif page == 'banking':
        context.update(general(alliance))  

    
    context.update({
        'permissions': permissions,
        'alliance': alliance,
        'bankingform': bankingform(),
        'promoteform': promoteform(nation),
        'changeform': changeform(nation),
        'demoteform': demoteform(nation),
        'taxrateform': taxrateform(),
        'templatesform': templatesform(nation),
        })
    return render(request, 'alliance/control_panel.html', context)


def change(request):
    pass


def post_handler(request):
    alliance = request.user.nation.alliance
    nation = request.user.nation
    if 'toggle' in request.POST:
        field = request.POST['toggle']
        if field == "pk" or field == "id":
            return HttpResponse()
        if hasattr(Timers, field):
            initiatives = request.user.nation.alliance.initiatives
            if getattr(initiatives.timers, field) < timezone.now(): #not on a cooldown
                toggle(initiatives, field)
        elif hasattr(Allianceoptions, field):
            toggle(alliance, field)
        return HttpResponse()

    elif 'save' in request.POST:
        form = generals_form(request.POST)
        if form.is_valid():
            if nation.permissions.template.rank == 0:
                hform = heirform(nation, request.POST)
                if hform.is_valid():
                    heir = hform.cleaned_data['heir']
                    if alliance.permissions.filter(heir=True).exclude(member=heir).exists():
                        alliance.permissions.all().update(heir=False)
                    alliance.permissions.filter(member=heir).update(heir=False)
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

    return HttpResponse("Settings successfully saved")


def toggle(model, field):
    if getattr(model, field) == False:
        setattr(model, field, True)
    else:
        setattr(model, field, False)
    model.save(update_fields=[field])
    


def general(nation, alliance):
    membertitle = alliance.templates.values('title').get(rank=5)['title']
    return {
        'generals': generals_form(initial={'anthem': alliance.anthem, 'flag': alliance.flag, 'description': alliance.description}),
        'initiatives': initiative_display(alliance.initiatives),
        'membertitleform': membertitleform(initial={'title': membertitle}),
        'heirform': heirform(nation, initial={'heir': (alliance.permissions.get(heir=True).member if alliance.permissions.filter(heir=True).exists() else None)}),
    }



def bank(request):
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
    for init in v.initiativedisplay:
        app = {
            'status': initiatives.__dict__[init], 
            'txt': v.initiativedisplay[init]['display'],
            'tooltip': v.initiativedisplay[init]['tooltip'],
            'initiative': init,
            }
        if getattr(initiatives.timers, init) > timezone.now():
            app.update({'timer': getattr(initiatives.timers, init) - timezone.now()})
        else:
            app.update({'timer': False})
        inits.append(app)
    return inits