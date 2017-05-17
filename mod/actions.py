from django.shortcuts import render, redirect
from django.db.models import Count, Q, F
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.core.paginator import *
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User

from nation.models import *
from nation.allianceforms import *
from nation.decorators import mod_required, headmod_required
from .forms import *
import nation.utilities as utils
import nation.variables as v



#####################
##BEGIN quickactions
#####################

def give_donor(mod, player, reason):
    Settings.objects.filter(nation=player).update(donor=True)
    result = "%s has recieved donor status!" % player.name
    set_modaction(mod, "Gave %s donor" % player.name, reason)
    return result

def revoke_donor(mod, player, reason):
    Settings.objects.filter(nation=player).update(donor=False)
    result = "%s has lost donor status!" % player.name
    set_modaction(mod, "Revoked %ss donor" % player.name, reason)
    return result

def enter_vacation(mod, player, reason):
    Nation.objects.filter(pk=player.pk).update(vacation=True)     
    Settings.objects.filter(nation=player).update(vacation_timer=v.vacationtimer())
    result = "%s has been placed into vacation mode!" % player.name
    set_modaction(mod, "Placed %s in vacation mode" % player.name, reason)
    return result

def exit_vacation(mod, player, reason):
    Nation.objects.filter(pk=player.pk).update(vacation=False)
    Settings.objects.filter(nation=player).update(vacation_timer=v.now())
    result = "%s has been removed from vacation mode!" % player.name
    set_modaction(mod, "Removed %s from vacation mode" % player.name, reason)
    return result

def delete(mod, player, reason):
    delete_nation(player)
    result = "%s has been deleted!" % player.name
    set_modaction(mod, "Deleted %s" % player.name, reason)

def ban(mod, player, reason, all=False):
    ban_player(player)
    result = "Banned %s" % player.name
    set_modaction(mod, "Banned %s" % player.name, reason)


###################
##END quickactions
###################


#Shadow banning from reporting
def report_ban(target, deleteall=False):
    target.settings.can_report = False
    target.settings.save(update_fields=['can_report'])
    if deleteall: #delete all reports made
        target.reports.all().delete()

def report_unban(target):
    Settings.objects.filter(nation=target).update(can_report=True)
    action = "unbanned %s from reporting" %  target.name



def set_modaction(mod, action, reason, reversible=True):
    mod.mod_actions.create(
        action=action,
        reason=reason,
        reversible=reversible, 
        reverse="not yet implemented",
    )


def delete_war(request, target):
    if request.POST['deletewar'] == 'offensive':
        war = target.offensives.filter(over=False)[0] #there's only 1 because 1 war limit
        otherguy = war.defender.name
        adj = 'offensive'
    else:
        war = target.defensives.filter(over=False)[0]
        otherguy = war.attacker.name
        adj = 'defensive'
    log = war.warlog
    log.timeend = v.now()
    log.save()
    war.delete()
    return "%s war against %s has been deleted" % (adj, otherguy), otherguy

#simple single IP ban
def ban_nation(target, allips=False):
    delete_nation(target)
    bans = []
    if allips:
        for ip in target.IPs.all().values_list('IP', flat=True):
            bans.append(Ban(IP=ip))
    else:
        bans.append(Ban(IP=target.IPs.latest('pk').IP))
    Bans.objects.bulk_create(bans)


#here we "delete" a nation, ie set as deleted and remove outstanding things like wars
#applications, market offers etc
def delete_nation(target):
    Nation.objects.filter(pk=target.pk).update(deleted=True)
    target.deleted = True
    target.user.is_active = False
    target.save()
    target.user.save()
    User.objects.filter(nation=target).update(is_active=False)
    #deleting the wars automatically delete the war logs
    target.offensives.all().delete()
    target.defensives.all().delete()
    #all infiltrating spies are sent home, same with outstanding spies
    for spy in Spy.objects.filter(Q(location=target)|Q(nation=target)):
        spy.send_home()
    Extradition_request.objects.filter(Q(target=target)|Q(nation=target)).delete()
    target.invites.all().delete()
    target.offers.all().delete()
    if target.has_alliance():
        target.alliance.kick(target)


#Shadow banning from reporting
def report_ban(target, deleteall=False):
    target.settings.can_report = False
    target.settings.save(update_fields=['can_report'])
    if deleteall: #delete all reports made
        target.reports.all().delete()


#Reassigns an ID to the target nation
#if the chosen ID has already been picked
#iterates over the database to find an available ID to the unlucky guy
#slow and inefficient, might get rewritten
def assign_id(target, new_id):
    try:
        alredy = Nation.objects.get(index=new_id)
    except:
        alredy = False
    else:
        idindex = ID.objects.get()
        while True:
            if Nation.objects.filter(index=idindex.index).exists():
                idindex.index += 1
            else:
                break
        if alredy:
            alredy.index = idindex.index
            alredy.save(update_fields=['index'])
    target.index = new_id
    target.save(update_fields=['index'])


def ban_player(target, allips=False):
    #Puts a player on the ban list
    #all or just the latest IP
    bans = [target.IPs.latest('pk').IP]
    if allips:
        bans = [ip for ip in target.IPs.all().values_list('IP', flat=True)]

    for ip in bans:
        #unique constraints and negligent performance penalties
        #means looping over a get or create is ideal
        Ban.objects.get_or_create(IP=ip)

