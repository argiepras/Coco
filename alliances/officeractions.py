import nation.news as news
from django.db.models import Q
from nation.alliances.forms import declarationform
import nation.utilities as utils

def kick():
    pks = request.POST.getlist('ids')
    kickees = alliance.members.all().select_related('permissions').filter(pk__in=pks)
    if not nation.permissions.template.kick or not nation.permissions.template.kick_officer:
        result = "You can't kick anyone! Stop this!"
    elif len(kickees):
        result = "You didn't select any members to kick!"
    else:
        tmp = 'But you do not have permission to kick '
        errs = ''
        for kickee in kickees:
            if nation.permissions.can_kick(kickee):
                alliance.kick(kickee)
                news.kicked(kickee, alliance)
            else:
                errs += "%s, "
            result = "Selected members have been purged from our ranks!"
        if errs != '':
            result +=  tmp + errs[:-2]

def masscomm():
    form = masscommform(request.POST)
    if form.is_valid():
        if request.POST['masscomm'] == 'everyone' and nation.permissions.can_masscomm():
            members = alliance.members.all()
            for member in members:
                member.comms.create(sender=nation, masscomm=True, message=form.cleaned_data['message'])
            nation.sent_comms.create(masscomm=True, message=form.cleaned_data['message'])
            result = "Mass comm sent!"
        elif request.POST['masscomm'] == 'leadership' and nation.permissions.can_officercomm():
            members = alliance.members.all()
            for member in members:
                member.comms.create(sender=nation, leadership=True, message=form.cleaned_data['message'])
            nation.sent_comms.create(leadership=True, message=form.cleaned_data['message'])
            result = "Leadership comm sent!"
        nation.actionlogging('mass commed')



def resign(*args):
    if nation.permissions.panel_access():
        if alliance.members.all().count() == 1:
            alliance.kick(nation)
            alliance.delete()
            return redirect('nation:main')
        else:
            if alliance.permissions.filter(heir=True).count() > 0:
                heir = alliance.permissions.get(heir=True)
            elif alliance.permissions.filter(template__rank__gt=5).count() > 0:
                for n in range(1, 5):
                    if alliance.permissions.filter(template__rank__gt=n).count() > 0:
                        heir = alliance.permissions.filter(template__rank__gt=n).order_by('?')[0]
                        break
            else:
                heir = alliance.permissions.all().order_by('?')[0]
            heir.template = alliance.templates.get(rank=0)
            heir.save()
        membertemplate = alliance.templates.get(rank=5)
        nation.permissions.template = membertemplate
        nation.permissions.save(update_fields=['template'])
        result = "Resignation gets handed over and you assume the role of an ordinary member"


def invite_players(nation, POST):
    form = inviteform(POST)
    alliance = nation.alliance
    failed = []
    sent = []
    if form.is_valid():
        names = form.cleaned_data['name'].strip(' ').split(',')
        for name in names:
            invitee = get_active_player(name)
            if invitee:
                invitee.invites.create(inviter=nation, alliance=nation.alliance)
                news.invited(invitee, alliance)
                sent.append(invitee.name)
            else:
                failed.append("'%s'" % name)
        if len(sent) == 0:
            return "Nobody was found for '%s'" % utils.string_list(names)
    else:
        return "Slow down big boy! max 200 characters"
    if alliance.event_on_invite:
        squad = alliance.notification_squad('invite', exclusion=nation)
        news.players_invited(nation, squad, sent)
    nation.actionlogs.create(action="Invited players to %s" % alliance.name, policy=False, extra=form.cleaned_data['name'])

"""
def revoke_invites(nation, POST):
    if POST['revoke'] == 'all':
        pass
    ids = POST.getlist('ids')
    invites = nation.alliance.outstanding_invites.filter(nation__pk__in=ids)
    if len(invites) == 0:
        return "Nobodys invite has been revoked!"

            if request.POST['revoke'] == 'all':
                alliance.outstanding_invites.all().delete()
                result = "All outstanding invites have been revoked!"
            elif request.POST['revoke'] == 'some':
                alliance.outstanding_invites.all().filter(pk__in=request.POST.getlist('ids')).delete()
                result = "Selected invites have been revoked!"
            else:
                invite = alliance.outstanding_invites.all().filter(pk=request.POST['revoke']).get()
                result = "Invite to %s has been revoked!"
                invite.delete()

"""


def generate_inviteevents(nation, invitees, modifier):
    notifiers = nation.alliance.members.filter(
        (Q(permissions__template__rank__lt=5)&Q(permissions__template__invite=True))|Q(permissions__template__rank=0)
        #(rank  <5 and applicants == True) or rank == 0
        #founder rank overrides other requirements
        ).exclude(pk=nation.pk) #won't send notifications to the actioner
    news.revoked_invites(nation, notifiers, modifier,  invitees)



#permission checks are performed in the view
def applicants(nation, POST):
    pks = POST.getlist('ids')
    applications = nation.alliance.applications.all().filter(pk__in=pks)
    if len(applications) == 0:
        return "You didn't select any!"
    if 'accept' in POST:
        return accept_applicants(nation, applications)
    return reject_applicants(nation, applications)


def accept_applicants(nation, applications):
    alliance = nation.alliance
    applicants = []
    for application in applications:
        alliance.add_member(application.nation)
        news.acceptedapplication(application.nation, alliance)
        application.delete()
        applicants.append(application.nation)

    if alliance.event_on_applicants:
        generate_applicantevents(nation, applicants, 'accepted')

    return  "The selected applicants are now members!"

def reject_applicants(nation, applications):
    alliance = nation.alliance
    applicants = []
    for application in applications:
        news.rejectedapplication(application.nation, alliance)
        application.delete()
        applicants.append(application.nation)

    if alliance.event_on_applicants:
        generate_applicantevents(nation, applicants, 'rejected')

    return "The selected applicants have been rejected!"


def generate_applicantevents(nation, applicants, modifier):
    notifiers = nation.alliance.members.filter(
        (Q(permissions__template__rank__lt=5)&Q(permissions__template__applicants=True))|Q(permissions__template__rank=0)
        #(rank  <5 and applicants == True) or rank == 0
        #founder rank overrides other requirements
        ).exclude(pk=nation.pk) #won't send notifications to the actioner
    news.applicant_events(nation, notifiers, modifier,  applicants)



#alliance declaration stuff
#officers only
def declare(nation, POST):
    if nation.permissions.is_officer():
        form = declarationform(POST)
        if form.is_valid():
            nation.alliance.declarations.create(nation=nation, content=form.cleaned_data['message'])
            return "Declaration made!"
        else:
            return "A declaration must be between 5 and 400 characters"
    return "Only available to officers"