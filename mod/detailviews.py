from django.shortcuts import render, redirect
from django.db.models import Count, Q, Sum
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.core.paginator import *
from django.http import HttpResponseRedirect

from nation.models import *
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
def aidpage(request, nation_id):
    nation = utils.get_player(nation_id)
    order = request.COOKIES.get('order_by', '-timestamp')
    try:
        if '-' in order:
            Aid._meta.get_field(order[1:])
        else:
            Aid._meta.get_field(order)
    except:
        order = "-timestamp"
    aid = Aid.objects.filter(Q(sender=nation)|Q(reciever=nation)).order_by(order)
    pager, logs = utils.paginate_me(aid, 25, request.GET.get('page', 1))
    
    direction = "up"
    if '-' in order:
        direction = "down"
        order = order[1:]
      

    context = {
        'target': nation, 
        'pages': utils.pagination(pager, logs), 
        'aids': logs,
        'ordering': order,
        'direction': 'arrow-' + direction,
    }

    """incoming = calculaid(nation.incoming_aid, 'sender')
    if incoming:
        context.update({'incoming': {'player': incoming[0], 'count': incoming[1]}})
    outgoing = calculaid(nation.outgoing_aid, 'reciever')
    if outgoing:
        context.update({'outgoing': {'player': outgoing[0], 'count': outgoing[1]}})
        """
    ordering = ['budget', 'rm', 'mg', 'oil', 'food', 'troops', 'weapons', 'research', 'uranium', 'nuke']
    totals = []
    for resource in ordering:
        total_in = nation.incoming_aid.filter(resource=resource).aggregate(total=Sum('amount'))['total']
        total_in = (total_in if total_in != None else 0)
        total_out = nation.outgoing_aid.filter(resource=resource).aggregate(total=Sum('amount'))['total']
        total_out = (total_out if total_out != None else 0)
        totals.append({'resource': v.aidnames[resource], 'incoming': total_in, 'outgoing': total_out})
    context.update({'totals': totals})
    return render(request, 'mod/aidpage.html', context)


def calculaid(aid, var):
    distincts = []
    data = []
    #this first part is to get a list of unique senders/recipients
    for aids in aid.all().distinct(var):
        if getattr(aid, var): #avoid NULLed entries
            distincts.append(getattr(aid, var))
    if not distincts:
        return None

    current = 0
    highest = 0
    hp = None
    #then find out who has the most entries
    for player in distincts:
        current = aids.filter(**{var: player}).count()
        if current > highest:
            highest = current
            hp = player
    return hp, highest


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