from nation.models import Allianceoptions, Nation, Timers, Initiatives
from nation.decorators import alliance_required, nation_required
from .forms import *

from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

import random

@login_required
@nation_required
@alliance_required
def view(request):
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
    if 'toggle' in request.POST:
        field = request.POST['toggle']
        if hasattr(Timer, field):
            initiatives = request.user.nation.alliance.initiatives


    


def general(nation, alliance):
    membertitle = alliance.templates.values('title').get(rank=5)['title']
    return {
        'anthemform': anthemform(initial={'anthem': alliance.anthem}),
        'flagform': flagform(initial={'flag': alliance.flag}),
        'initiatives': initiative_display(alliance.initiatives),
        'membertitleform': membertitleform(initial={'title': membertitle}),
        'heirform': heirform(nation, initial={'heir': (alliance.permissions.get(heir=True).member if alliance.permissions.filter(heir=True).exists() else None)}),
        'descriptionform': descriptionform(initial={'content': alliance.description}),
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
                'locked': ('locked' if random.randint(1, 2) == 1 else ''),
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
        if initiatives.__dict__['%s_timer' % init] > timezone.now():
            app.update({'timer': initiatives.__dict__['%s_timer' % init] - timezone.now()})
        else:
            app.update({'timer': False})
        inits.append(app)
    return inits