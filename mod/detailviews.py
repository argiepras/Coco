from django.shortcuts import render, redirect
from django.db.models import Count, Q
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.core.paginator import *
from django.http import HttpResponseRedirect

from nation.models import *
from nation.allianceforms import *
from nation.decorators import mod_required, headmod_required
from .forms import *
import nation.utilities as utils
import nation.variables as v




@mod_required
def nation_actions(request, nation_id, page):
    nation = request.user.nation
    target = utils.get_player(nation_id)
    if target == False:
        return render(request, 'mod/not_found.html')
    context = {'target': target}
    utils.pagecheck(nation, target, "all actions")

    query = target.actionlogs.all().order_by('-pk')
    paginator, actionlist = utils.paginate_me(query, 50, page)
    context.update({
            'pages': utils.pagination(paginator, actionlist),
            'actions': actionlist,
        })
    return render(request, 'mod/actions.html', context)




@mod_required
def nation_incoming(request, nation_id, page):
    nation = request.user.nation
    target = utils.get_player(nation_id)
    if target == False:
        return render(request, 'mod/not_found.html')
    context = {'target': target, 'title': 'All incoming aid', 'direction': 'in'}
    utils.pagecheck(nation, target, "incoming aid")
    query = target.incoming_aid.all().order_by('-pk')
    paginator, actionlist = utils.paginate_me(query, 50, page)
    context.update({
            'pages': utils.pagination(paginator, actionlist),
            'aidlist': actionlist,
        })
    return render(request, 'mod/aid.html', context)

@mod_required
def nation_outgoing(request, nation_id, page):
    nation = request.user.nation
    target = utils.get_player(nation_id)
    if target == False:
        return render(request, 'mod/not_found.html')
    context = {'target': target, 'title': 'All outgoing aid', 'direction': 'out'}
    utils.pagecheck(nation, target, "outgoing aid")
    query = target.outgoing_aid.all().order_by('-pk')
    paginator, actionlist = utils.paginate_me(query, 50, page)
    context.update({
            'pages': utils.pagination(paginator, actionlist),
            'aidlist': actionlist,
        })
    return render(request, 'mod/aid.html', context)

@mod_required
def nation_allaid(request, nation_id, page):
    nation = request.user.nation
    target = utils.get_player(nation_id)
    if target == False:
        return render(request, 'mod/not_found.html')
    context = {'target': target}
    utils.pagecheck(nation, target, "all aid")
    query = Aidlog.objects.filter(Q(sender=target)|Q(reciever=target)).order_by('-pk')
    paginator, actionlist = utils.paginate_me(query, 50, page)
    context.update({
            'pages': utils.pagination(paginator, actionlist),
            'aidlist': actionlist,
        })
    return render(request, 'mod/allaid.html', context)

@mod_required
def nation_wars(request, nation_id, page):
    nation = request.user.nation
    target = utils.get_player(nation_id)
    if target == False:
        return render(request, 'mod/not_found.html')
    context = {'target': target}
    utils.pagecheck(nation, target, "all wars")
    query = Warlog.objects.filter(Q(attacker=target)|Q(defender=target)).order_by('-pk')
    paginator, actionlist = utils.paginate_me(query, 50, page)
    context.update({
            'pages': utils.pagination(paginator, actionlist),
            'reports': actionlist,
        })
    return render(request, 'mod/wars.html', context)


@mod_required
def nation_reports(request, nation_id, page):
    nation = request.user.nation
    target = utils.get_player(nation_id)
    if target == False:
        return render(request, 'mod/not_found.html')
    context = {'target': target}
    utils.pagecheck(nation, target, "all wars")
    query = target.reports.all().order_by('-pk')
    paginator, actionlist = utils.paginate_me(query, 50, page)
    context.update({
            'pages': utils.pagination(paginator, actionlist),
            'reports': actionlist,
        })
    return render(request, 'mod/nation_reports.html', context)


@mod_required
def nation_logins(request, nation_id, page):
    nation = request.user.nation
    target = utils.get_player(nation_id)
    if target == False:
        return render(request, 'mod/not_found.html')
    context = {'target': target}
    utils.pagecheck(nation, target, "all wars")
    query = target.login_times.all().order_by('-pk')
    paginator, actionlist = utils.paginate_me(query, 50, page)
    context.update({
            'pages': utils.pagination(paginator, actionlist),
            'logins': actionlist,
        })
    return details(request, nation_id, page, 'logins')


def details(request, nation_id, page, template):

    if template == 'logins':
        context = basedetails(request, nation_id, 'login_times', 'all logins')

    return render(request, 'mod/%s.html' % template, context)


def basedetails(request, nation_id, manager, pcheck, var):
    nation = request.user.nation
    target = utils.get_player(nation_id)
    if target == False:
        return render(request, 'mod/not_found.html')
    context = {'target': target}
    utils.pagecheck(nation, target, pcheck)
    query = getattr(target, manager).all().order_by('-pk')
    paginator, actionlist = utils.paginate_me(query, 50, page)
    context.update({
            'pages': utils.pagination(paginator, actionlist),
            var: actionlist,
        })
    return context

@mod_required
def iplogs(request, nation_id):
    nation = request.user.nation
    target = utils.get_player(nation_id)
    if target == False:
        return render(request, 'mod/not_found.html')
    context = {'target': target}
    #POST data handling
    #what little of it there are
    if request.method == "POST":
        if 'correlate' in request.POST:
            context.update({'result': 'not yet implemented'})

        elif 'checkip' in request.POST:
            try:
                ip = target.IPs.get(pk=request.POST['checkip'])
            except:
                context.update({'result': 'Invalid entry'})
            else:
                context.update({
                    'associates': IP.objects.select_related('nation').filter(IP=ip.IP),
                    'checked': True,
                    'selected_ip': ip.IP,
                })

    query = target.IPs.all().order_by('-pk')
    iplist = []
    for ip in query:
        ip.nationcount = IP.objects.filter(IP=ip.IP).count()
        iplist.append(ip)
    context.update({
            'IPs': query,
        })
    return render(request, 'mod/ips.html', context)