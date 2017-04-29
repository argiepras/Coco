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
def main(request):
    context = {}
    nation = request.user.nation
    result = False
    if request.method == 'POST':
        if 'newid' in request.POST:
            form = newidform(request.POST)
            if form.is_valid():
                player = utils.get_player(form.cleaned_data['old'])
                if player:
                    assign_id(player, form.cleaned_data['new'])

                    result = "%s has been assigned ID %s" % (player.name, form.cleaned_data['new'])
                else:
                    result = "No nation found for '%s'" % form.cleaned_data['old']

        elif 'viewplayer' in request.POST:
            form = viewplayerform(request.POST)
            if form.is_valid():
                player = utils.get_active_player(form.cleaned_data['player'])
                if player:
                    return redirect('mod:nation', nation_id=player.index)

        elif 'comm' in request.POST:
            form = globalcommform(request.POST)
            if form.is_valid():
                for n in Nation.objects.filter(deleted=False).iterator():
                    n.comms.create(message=form.cleaned_data['content'], globalcomm=True)
                result = "Global communique has been issued!"
            else:
                result = "Bad input"

        elif 'quick' in request.POST:
            form = quickactionform(request.POST)
            if form.is_valid():
                player = utils.get_active_player(form.cleaned_data['player'])
                if player:
                    if form.cleaned_data['action'] == 'donor':
                        Settings.objects.filter(nation=player).update(donor=True)
                        action = "Gave %s donor" % player.name
                        result = "%s has recieved donor status!" % player.name

                    elif form.cleaned_data['action'] == 'revoke':
                        Settings.objects.filter(nation=player).update(donor=False)
                        action = "Revoked %ss donor" % player.name
                        result = "%s has lost donor status!" % player.name

                    elif form.cleaned_data['action'] == 'exit_vac':
                        Nation.objects.filter(pk=player.pk).update(vacation=False)
                        Settings.objects.filter(nation=player).update(vacation_timer=v.now())
                        action = "Removed %s from vacation mode" % player.name
                        result = "%s has been removed from vacation mode!" % player.name

                    elif form.cleaned_data['action'] == 'enter_vac':
                        Nation.objects.filter(pk=player.pk).update(vacation=True)
                        Settings.objects.filter(nation=player).update(vacation_timer=v.now() + timezone.timedelta(days=7))
                        action = "Placed %s in vacation mode" % player.name
                        result = "%s has been placed into vacation mode!" % player.name

                    elif form.cleaned_data['action'] == 'delete':
                        delete_nation(player)
                        action = "Deleted %s" % player.name
                        result = "%s has been deleted!" % player.name

                    elif form.cleaned_data['action'] == 'ban':
                        Ban.objects.create(IP=player.IPs.latest('pk').IP)
                        Nation.objects.filter(pk=player.pk).update(deleted=True)
                        action = "deleted and banned %s" % player.name
                        result = "%s has been deleted and %s put on the ban list" % (player.name, player.IPs.latest('pk').IP)

                    elif form.cleaned_data['action'] == 'banreport':
                        report_ban(player, False)
                        action = "banned %s from reporting" %  player.name

                        result = "%s has been banned from reporting" % player.name

                    elif form.cleaned_data['action'] == 'unbanreport':
                        player.settings.can_report = True
                        player.settings.save(update_fields=['can_report'])
                        action = "unbanned %s from reporting" %  player.name

                        result = "%s has been unbanned from reporting" % player.name

                    nation.mod_actions.create(
                    action=action,
                    reason=form.cleaned_data['reason'],
                    reversible=True,
                    reverse="not yet implemented",
                    )
                else:
                    result = "That nation doesn't exist!"

            else:
                result = "Invalid POST data (did you forget the enter a reason?)"

    context.update({
        'result': result,
        'reportcount': Report.objects.filter(investigated=False).count(),
        'suspectcount': Suspected.objects.filter(checked=False).count(),
        'globalcommform': globalcommform(),
        'quickactionform': quickactionform(),
        'viewplayerform': viewplayerform(),
        'newidform': newidform(),
        })
    return render(request, 'mod/main.html', context)

@headmod_required
def mods(request):
    context = {}
    result = False
    nation = request.user.nation
    if request.method == 'POST':
        if 'demote' in request.POST:
            try:
                demotee = Nation.objects.filter(settings__mod=True).get(pk=request.POST['demote'])
            except:
                result = "Selected is not a mod!"
            else:
                Settings.objects.filter(nation=demotee).update(mod=False)
                result = "%s has been successfully demoted!" % demotee.name

        elif 'promote' in request.POST:
            form = viewplayerform(request.POST)
            if form.is_valid():
                promotee = utils.get_active_player(form.cleaned_data['player'])
                Settings.objects.filter(nation__pk=promotee.pk).update(mod=True)
                result = "%s has been promoted to mod!" % promotee.name
            else:
                result = "Bad input"

    context.update({
        'result': result,
        'mods': Nation.objects.filter(settings__mod=True).exclude(pk=nation.pk),
        'promoteplayerform': viewplayerform(),
        })
    return render(request, 'mod/mods.html', context)

@mod_required
def reports(request, page):
    context = {}
    nation = request.user.nation
    result = False
    if request.method == "POST":
        if 'claim' in request.POST:
            claimed = Report.objects.get(pk=request.POST['claim'])
            if claimed.open():
                claimed.investigator = nation
                claimed.save(update_fields=['investigator'])
                result = "Report has been claimed."
            else:
                result = "This report has already been claimed by %s!" % claimed.investigator.name

        elif 'release' in request.POST:
            claimed = nation.investigated.get(pk=request.POST['release'])
            claimed.investigator = None
            claimed.save(update_fields=['investigator'])
            result = "Report has been released."


    reportquery = Report.objects.all().order_by('investigated')
    paginator, actionlist = utils.paginate_me(reportquery, 50, page)
    context.update({
            'result': result,
            'pages': utils.pagination(paginator, actionlist),
            'reports': actionlist,
        })


    
    return render(request, 'mod/reports.html', context)

@mod_required
def reportpage(request, report_id):
    context = {}
    result = False
    nation = request.user.nation
    try:
        report = Report.objects.get(pk=report_id)
    except:
        return render(request, 'mod/reportpage.html', {'notfound': True})
    if request.method == "POST":
        if 'claim' in request.POST:
            if report.open():
                report.investigator = nation
                report.save(update_fields=['investigator'])
                result = "Report has been claimed."
            else:
                result = "This report has already been claimed by %s!" % report.investigator.name

        elif 'release' in request.POST:
            report.investigator = None
            report.save(update_fields=['investigator'])
            result = "Report has been released."

        elif 'close' in request.POST:
            form = closereportform(request.POST)
            if form.is_valid():
                report.investigated = True
                report.conclusion = form.cleaned_data['conclusion']
                report.guilty = form.cleaned_data['guilty']
                report.save()
                result = "Report has been closed"
            else:
                result = "invalid POST data (forget a reason?)"
    context.update({
        'result': result,
        'report': report,
        'closereportform': closereportform(),
    })
    return render(request, 'mod/reportpage.html', context)



@mod_required
def wardetails(request, war_id):
    context = {}
    nation = request.user.nation
    try:
        war = Warlog.objects.select_related('attacker', 'defender').get(pk=war_id)
    except:
        return render(request, 'mod/not_found.html')
    if request.method == "POST":
        if 'delete' in request.POST:
            war.warlog.over = True
            war.warlog.save()
            war.delete()
            nation.mod_actions.create(
                action="Deleted war between %s and %s" % (war.attacker.name, war.defender.name),
                reason=form.cleaned_data['reason'],
                reversible=False,
                reverse="not yet implemented",
                    )
            return redirect('mod:overview')
            
    context.update({
        'reasonform': reasonform(),
        'war': war,
    })
    return render(request, 'mod/war.html', context)



@mod_required
def mod(request, modid):
    nation = request.user.nation
    if not nation.settings.head_mod:
        return redirect('mod:main')
    context = {}
    moderator = Nation.objects.get(index=modid)
    if request.method == "POST":
        if 'demote' in request.POST:
            if moderator.pk == nation.pk:
                result = "Why are you trying to demote yourself?"
            else:
                Settings.objects.filter(nation=moderator).update(mod=False, head_mod=False)
                result = "%s has been demoted" % moderator.name
            context.update({'result': result})
    context.update({
        'active_reports': moderator.investigated.filter(investigated=False),
        'reportcount': moderator.investigated.filter(investigated=False).count(),
        'completed_reports': moderator.investigated.filter(investigated=True).order_by('mod_timestamp')[0:10],
        'completed_reportcount': moderator.investigated.filter(investigated=True).count(),
        'mod': moderator,
        'views': moderator.mod_views.all()[0:10],
        'total_playerviews': moderator.mod_views.all().count(),
    })
    return render(request, 'mod/modpage.html', context)

@mod_required
def nation_overview(request, page):
    context = {}
    if request.method == "POST":
        if 'search' in request.POST:
            form = viewplayerform(request.POST)
            if form.is_valid():
                name = form.cleaned_data['player']
                ncount = Nation.objects.filter(name__icontains=name).count()
                ucount = Nation.objects.filter(user__username__icontains=name).count()
                context.update({
                        'nation_name_matches': Nation.objects.filter(name__icontains=name),
                        'username_matches': Nation.objects.filter(user__username__icontains=name),
                        'search_query': name,
                    })
            else:
                context.update({'result': 'Invalid input'})
    query = Nation.objects.filter(deleted=False)
    paginator, actionlist = utils.paginate_me(query, 50, page)
    context.update({
            'pages': utils.pagination(paginator, actionlist),
            'nations': actionlist,
            'searchform': viewplayerform(),
        })
    return render(request, 'mod/nations.html', context)

@mod_required
def nation_page(request, nation_id):
    nation = request.user.nation
    context = {}
    pagename = "overview"
    result = False
    target = utils.get_player(nation_id)
    if target == False:
        return render(request, 'mod/not_found.html')
    pagecheck(nation, target, pagename)
    if request.method == "POST":
        form = reasonform(request.POST)
        if form.is_valid():
            if 'delete' in request.POST:
                delete_nation(target)
                nation.mod_actions.create(
                    action="Deleted %s" % target.name,
                    reason=form.cleaned_data['reason'],
                    reversible=True,
                    reverse="not yet implemented",
                    )
                result = "%s has been deleted" % target.name

            elif 'reportban' in request.POST:
                delall = (True if 'killreports' in request.POST else False)
                report_ban(target, delall)
                nation.mod_actions.create(
                    action="Report banned %s" % target.name,
                    reason=form.cleaned_data['reason'],
                    reversible=True,
                    reverse="not yet implemented",
                    )
                result = "%s has banned from reporting" % target.name

            elif 'ban' in request.POST:
                act = "Deleted and banned %s" % target.name
                delete_nation(target)
                ips = []
                if 'banall' in request.POST:
                    act += " and banned all associated IPs"
                    for ip in target.IPs.all():
                        if not Ban.objects.filter(IP=ip.IP).exists():
                            Ban.objects.create(IP=ip.IP)
                            ips.append(ip.IP)
                else:
                    latest = target.IPs.all().latest('pk')
                    if not Ban.objects.filter(IP=latest.IP).exists():
                        Ban.objects.create(IP=latest.IP)
                        ips.append(latest.IP)

                nation.mod_actions.create(
                    action=act,
                    reason=form.cleaned_data['reason'],
                    reversible=True,
                    reverse="not yet implemented",
                    )
                result = act

            elif 'deletewar' in request.POST:
                result, otherguy = delete_war(request, target)
                nation.mod_actions.create(
                    action="Deleted war between %s and %s" % (target.name, otherguy),
                    reason=form.cleaned_data['reason'],
                    reversible=True,
                    reverse="not yet implemented",
                    )
                result = "War between %s and %s has been deleted" % (target.name, otherguy)

            elif 'force' in request.POST:
                target.vacation = True
                target.save(update_fields=["vacation"])
                nation.mod_actions.create(
                    action="Placed %s into vacation mode" % target.name,
                    reason=form.cleaned_data['reason'],
                    reversible=True,
                    reverse="not yet implemented",
                    )
                result = "%s has been placed into vacation mode" % target.name

            elif 'remove' in request.POST:
                target.vacation = False
                target.save(update_fields=["vacation"])
                nation.mod_actions.create(
                    action="Removed %s from vacation mode" % target.name,
                    reason=form.cleaned_data['reason'],
                    reversible=True,
                    reverse="not yet implemented",
                    )
                result = "%s has been removed from vacation mode" % target.name

        else:
            result = 'invalid reason (did you forget it?)'

    #set a variable that determines whether mod can see sensitive data
    #like logs of pretty much everything
    can_see = True
    #nation.investigated.all().filter(reported=target).exists()

    if can_see:
        context.update({
                'warlogs': Warlog.objects.filter(Q(attacker=target)|Q(defender=target))[0:10],
                'incoming_aid': target.incoming_aid.all()[0:20],
                'outgoing_aid': target.outgoing_aid.all()[0:20],
                'actionlogs': target.actionlogs.all()[0:10],
                'login_times': target.login_times.all()[0:10],
                'associated_IPs': target.IPs.all(),
            }) 
    context.update({
            'result': result,
            'can_see': can_see,
            'reasonform': reasonform(),
            'target': target,
            'reports_made': Report.objects.filter(reporter=target),
            'reports_made_count': Report.objects.filter(reporter=target).count(),
            'reports_dismissed_count': Report.objects.filter(reporter=target, guilty=False).count(),
        })

    return render(request, 'mod/nation.html', context)


@mod_required
def nation_actions(request, nation_id, page):
    nation = request.user.nation
    target = utils.get_player(nation_id)
    if target == False:
        return render(request, 'mod/not_found.html')
    context = {'target': target}
    pagecheck(nation, target, "all actions")

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
    pagecheck(nation, target, "incoming aid")
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
    pagecheck(nation, target, "outgoing aid")
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
    pagecheck(nation, target, "all aid")
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
    pagecheck(nation, target, "all wars")
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
    pagecheck(nation, target, "all wars")
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
    #POST data handling
    #what little of it there are
    if request.method == "POST":
        if 'correlate' in request.POST:
            context.update({'result': 'not yet implemented'})


    pagecheck(nation, target, "all wars")
    query = target.login_times.all().order_by('-pk')
    paginator, actionlist = utils.paginate_me(query, 50, page)
    context.update({
            'pages': utils.pagination(paginator, actionlist),
            'logins': actionlist,
        })
    return render(request, 'mod/logins.html', context)

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

def pagecheck(nation, target, pagename):
    #check if entry exists and if so, update timestamp
    #to avoid multiple entries in the database with repeated viewings
    #don't need the same person to be placed in 10 times
    if nation.mod_views.filter(timestamp__gte=v.now() - timezone.timedelta(hours=1), nation=target, page=pagename).exists():
        nation.mod_views.filter(timestamp__gte=v.now() - timezone.timedelta(hours=1), nation=target, page=pagename).update(timestamp=v.now())
    else:
        nation.mod_views.create(nation=target, page=pagename)





def delete_war(request, target):
    if request.POST['deletewar'] == 'offensive':
        war = target.offensives.all()[0] #there's only 1 because 1 war limit
        otherguy = war.defender.name
        adj = 'offensive'
    else:
        war = target.defensives.all()[0]
        otherguy = war.attacker.name
        adj = 'defensive'
    log = war.warlog
    log.over = True
    log.timeend = v.now()
    log.save()
    war.delete()
    return "%s war against %s has been deleted" % (adj, otherguy), otherguy


#here we "delete" a nation, ie set as deleted and remove outstanding things like wars
def delete_nation(target):
    target.deleted = True
    target.save(update_fields=['deleted'])
    if target.offensives.all().exists():
        war = target.offensives.all()[0]
        Warlog.objects.filter(war=war).update(over=False, timeend=v.now())
        war.delete()
    if target.defensives.all().exists():
        war = target.defensives.all()[0]
        Warlog.objects.filter(war=war).update(over=False, timeend=v.now())
        war.delete()



def report_ban(target, deleteall):
    target.settings.can_report = False
    target.settings.save(update_fields=['can_report'])
    if deleteall: #delete all reports made
        target.reports.all().delete()


def assign_id(target, new_id):
    try:
        alredy = Nation.objects.get(index=new_id)
    except:
        pass
    else:
        idindex = ID.objects.get()
        while True:
            if Nation.objects.filter(index=idindex.index).exists():
                idindex.index += 1
            else:
                break
        alredy.index = idindex.index
        alredy.save(update_fields=['index'])
    target.index = new_id
    target.save(update_fields=['index'])


