from .forms import declarationform, depositform, withdrawform
import nation.variables as v
from nation.models import Bank
import nation.news as news
from nation.models import Memberstats

from django.db.models import F

def leave(nation):
    alliance = nation.alliance
    if alliance.members.all().count() == 1:
        alliance.delete()
        nation.actionlogs.create(action="Left alliance and disbanded", policy=False, extra=alliance.name)
        return "Alliance has been disbanded"

    if alliance.event_on_leaving:
        news.player_left(nation)
    nation.actionlogs.create(action="Left alliance", policy=False, extra=alliance.name)
    if nation.permissions.template.rank == 0 and alliance.members.filter(permissions__template__rank=0).count() == 1: 
        #special founder exception
        #if the leaver is founder level and the only person with a rank 0 template
        from .officeractions import set_new_heir
        alliance.kick(nation)
        set_new_heir(alliance, nation)
    else:
        alliance.kick(nation)
    return "You say your goodbyes before being tossed by security."


def withdraw(nation, POST):
    if not nation.permissions.has_permission('withdraw'):
        return "You need permission to do this"
    bank = Bank.objects.select_for_update().get(alliance=nation.alliance)
    form = withdrawform(nation, POST)
    if form.is_valid():
        nation.budget += form.cleaned_data['amount']
        bank.budget -= form.cleaned_data['amount']
        if nation.alliance.bank.limit:
            if nation.alliance.bank.per_nation:
                qfilter = {'nation': nation}
            else:
                qfilter = {'alliance': nation.alliance}
            Memberstats.objects.select_for_update().filter(**qfilter).update(budget=F('budget') + form.cleaned_data['amount'])
        kwargs = {'update_fields': ['budget']}
        nation.save(**kwargs)
        bank.save(**kwargs)
        nation.alliance.bank_logs.create(nation=nation, amount=form.cleaned_data['amount'])
        nation.actionlogging('Withdrew from alliance bank', str(form.cleaned_data['amount']))
        result = "Withdrawal has been made!"
    else:
        result = "You can't withdraw %s!" % POST['amount']
    return result

def deposit(nation, POST):
    bank = Bank.objects.select_for_update().get(alliance=nation.alliance)
    form = depositform(nation, POST)
    if form.is_valid():
        nation.budget -= form.cleaned_data['amount']
        bank.budget += form.cleaned_data['amount']
        kwargs = {'update_fields': ['budget']}
        bank.save(**kwargs)
        nation.save(**kwargs)
        nation.actionlogs.create(action="deposited", policy=False, extra=str(form.cleaned_data['amount']))
        nation.alliance.bank_logs.create(nation=nation, deposit=False, amount=form.cleaned_data['amount'])
        result = "$%sk has been deposited!" % form.cleaned_data['amount']
    else:
        result = "Must be between $1k and $%sk" % nation.budget
    return result


def invite(nation, alliance, action):
    nation = kwargs['nation']
    alliance = kwargs['alliance']
    action = kwargs['action']
    try:
        invite = alliance.invites.filter(nation=nation)
    except:
        return "You do not have an invitation from this alliance!"
    if action == "accept":
        return accept_invite(nation, alliance, invite)
    return reject_invite(nation, alliance, invite)


def accept_invite(nation, alliance, invite):
    alliance.add_member(nation)
    #automatically deletes the invite
    if alliance.event_on_invite:
        news.invitee_events(nation, alliance.notification_squad('invite'), 'accepted')
    nation.actionlogs.create(action="Accepted invite to %s" % alliance.name, policy=False)
    return "The invitation was graciously accepted"


def reject_invite(nation, alliance, invite):
    invite.delete()
    if alliance.event_on_invite:
        news.invitee_events(nation, alliance.notification_squad('invite'), 'rejected')
    nation.actionlogs.create(action="Rejected invite to %s" % alliance.name, policy=False)
    return "Invitation declined"



def post_chat(nation, POST):
    #don't need to check for alliance because that's taken care of in the view
    form = declarationform(POST)
    if form.is_valid():
        message = form.cleaned_data['message']
        if nation.alliance.chat.filter(nation=nation, content__iexact=message, timestamp__gte=v.onlineleaders()).exists():
            #onlineleaders is a 10 minute time delta
            #this is to avoid spamming
            result = "Please don't spam"
        else:
            nation.alliance.chat.create(nation=nation, content=form.cleaned_data['message'])
            nation.actionlogs.create(action="Posted alliance chat", policy=False, extra=nation.alliance.name)
            result = "Message posted!"
    else:
        result = "Must be between 5 and 400 characters"
    return result



def apply(nation, alliance):
    if nation.has_alliance():
        return "You are already a member of an alliance!"
    #using same function for both applying and retracting the application   
    if alliance.applications.filter(nation=nation).exists():
        alliance.applications.filter(nation=nation).delete()
        if alliance.event_on_applicants:
            news.retracted_application(nation, alliance)
        nation.actionlogs.create(action='unapplied to %s' % alliance.name, policy=False)
        return "Application retracted"
    alliance.applications.create(nation=nation)
    if alliance.event_on_applicants:
        news.player_applied(nation, alliance)
    nation.actionlogs.create(action='applied to %s' % alliance.name, policy=False)
    return "Your application has been sent! Now we wait and see if they will accept it."
