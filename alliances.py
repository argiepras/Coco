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