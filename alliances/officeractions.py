import nation.news as news
from django.db.models import Q
from nation.alliances.forms import declarationform
import nation.utilities as utils
from .forms import inviteform, masscommform
from nation.models import Permissiontemplate

def kick(nation, POST):
    if not nation.permissions.has_permission('kick') and not nation.permissions.has_permission('kick_officer'):
        return "You can't kick anyone! Stop this!"

    pks = POST.getlist('member_choice')
    kickees = nation.alliance.members.all().select_related('permissions').filter(pk__in=pks)

    if len(kickees) ==  0:
        return "You didn't select anyone!"
    else:
        tmp = 'But you do not have permission to kick '
        success = []
        errs = []
        result = ''
        for kickee in kickees:
            if nation.permissions.can_kick(kickee):
                nation.alliance.kick(kickee)
                news.kicked(kickee, nation.alliance)
                success.append(kickee)
            else:
                errs.append(kickee)
        if success:
            result = "%s have been purged from our ranks!" % utils.string_list(success, 'name')
        if errs:
            result +=  tmp + utils.string_list(errs)
        nation.actionlogs.create(action="kicked players", policy=False, extra=utils.string_list(kickees, 'name'))
    return result


def masscomm(nation, POST):
    if POST['masscomm'] == 'everyone':
        if not nation.permissions.has_permission('mass_comm'):
            return "You do not have permission to do this!"
    else:
        if not nation.permissions.has_permission('officer_comm'):
            return "You do not have permission to do this!"
    form = masscommform(POST)
    if form.is_valid():
        payload = {
            'sender': nation,
            'message' : form.cleaned_data['message'],
        }
        if POST['masscomm'] == 'everyone':
            recipients = nation.alliance.members.all()
            payload.update({'masscomm': True})
            result = "Mass comm sent!"
        else:
            recipients = nation.alliance.officers.all()
            payload.update({'leadership': True})
            result = "Leadership comm sent!"
 
        for recipient in recipients:
            recipient.comms.create(**payload)
 
        payload.pop('sender')
        nation.sent_comms.create(**payload)
        nation.actionlogging('mass commed')
    
    else:
        result = 'Message must be between 5 and 500 characters'
    return result



def resign(nation):
    if not nation.permissions.panel_access():
        return "You cannot resign from being a member"
    action = "resigned"
    alliance = nation.alliance
    if alliance.members.all().count() == 1:
        alliance.kick(nation)
        alliance.delete()
        action += " and disbanded alliance"
    else:
        if nation.permissions.template.rank == 0:
            set_new_heir(nation.alliance, nation)
        membertemplate = alliance.templates.get(rank=5)
        nation.permissions.template = membertemplate
        nation.permissions.save(update_fields=['template'])
        result = "Resignation gets handed over and you assume the role of an ordinary member"
    nation.actionlogs.create(action=action, policy=False)


def set_new_heir(alliance, exclude):
    if alliance.permissions.filter(template__rank=0).exclude(member=exclude).exists():
        #don't set a new heir if a founder level person already exists
        return
    foundertemplate = alliance.templates.filter(rank=0)[0]
    if alliance.permissions.filter(heir=True).exists():
        alliance.permissions.filter(heir=True).update(heir=False, template=foundertemplate)
    else: #without an heir we randomly pick in descending order of rank, ie 0 -> 1 -> 2
        for rank, _ in Permissiontemplate.rank_choices[1:]:
            if alliance.permissions.filter(template__rank=rank).exclude(member=exclude).count() > 0:
                heir = alliance.permissions.filter(template__rank=rank).exclude(member=exclude).order_by('?')[0]
                heir.template = foundertemplate
                heir.save(update_fields=['template'])
                news.heir_tofounder(heir.member)
                break


def invite_players(nation, POST):
    if not nation.permissions.has_permission('invite'):
        return "You do not have permission to do this"
    form = inviteform(POST)
    alliance = nation.alliance
    created = False
    failed = []
    sent = []
    if form.is_valid():
        names = form.cleaned_data['name'].strip(' ').split(',')
        for name in names:
            invitee = utils.get_active_player(name)
            if invitee:
                inv, created = invitee.invites.get_or_create(inviter=nation, alliance=nation.alliance)
                if created:
                    news.invited(invitee, alliance)
                    sent.append(invitee.name)
            else:
                failed.append("'%s'" % name)
        if len(sent) == 0 and not created:
            return "%s already has an invite" % utils.string_list(names)
        elif len(sent) == 0:
            return "No matches found for %s" % utils.string_list(names)
    else:
        return "Slow down big boy! max 200 characters"
    if alliance.event_on_invite:
        squad = alliance.notification_squad('invite', exclusion=nation.pk)
        news.players_invited(nation, squad, sent)
    nation.actionlogs.create(action="Invited players to %s" % alliance.name, policy=False, extra=form.cleaned_data['name'])

    if len(sent) == 0:
        txt = "%s wasn't found" % utils.string_list(failed)
    else:
        txt = "Invite%s has been sent to %s" % (('s' if len(sent) > 1 else ''), utils.string_list(sent))
        if len(failed) > 0:
            txt += ". %s wasn't found" % utils.string_list(failed)
    return txt



def revoke_invites(nation, POST):
    result = "Invites have been revoked"
    if POST['revoke'] == 'all':
        invites = nation.alliance.outstanding_invites.all()
    
    elif POST['revoke'] == 'some':
        ids = POST.getlist('ids')
        invites = nation.alliance.outstanding_invites.filter(nation__pk__in=ids)

    else:
        invites = nation.alliance.outstanding_invites.all().filter(pk=POST['revoke'])
        result = "Invite to %s has been revoked!"

    if len(invites) == 0:
        return "Nobodys invite has been revoked!"

    revokees = []
    for invite in invites:
        news.invite_revoked(invite)
        revokees.append(invite.nation)
        invite.delete()
    if nation.alliance.event_on_invite:
        news.revoked_invites(nation, revokees)

    nation.actionlogs.create(action="Revoked invites", policy=False, extra=utils.string_list(revokees, 'name'))


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
    nation.actionlogging('accepted applicants', utils.string_list(applicants))
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
    nation.actionlogging('rejected applicants', utils.string_list(applicants))
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
    if nation.permissions.panel_access():
        form = declarationform(POST)
        if form.is_valid():
            dec = nation.alliance.declarations.create(nation=nation, content=form.cleaned_data['message'])
            nation.actionlogging('made alliance declaration', str(dec.pk))
            return "Declaration made!"
        else:
            return "A declaration must be between 5 and 400 characters"
    return "Only available to officers"