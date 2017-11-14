from django import template
from django.utils.safestring import mark_safe
import nation.variables as v
import nation.utilities as utils

register = template.Library()


def warlink(war, nation):
    return mark_safe((war.attacker.get_absolute_url() if war.defender.pk == nation.pk else war.defender.get_absolute_url()))

register.filter('warlink', warlink)

def wartype(war, nation):
    if war.defender.pk == nation.pk:
        war_type = 'Defensive'
    else:
        war_type = 'Offensive'
    return mark_safe(war_type)

register.filter('wartype', wartype)


def lastip(nation):
    return mark_safe(nation.IPs.all().latest('pk'))

register.filter('lastip', lastip)

def lastipurl(nation):
    return mark_safe(nation.IPs.all().latest('pk').get_absolute_modurl())

register.filter('lastipurl', lastipurl)


def outcome(war, nation):
    if war.winner == '':
        war_outcome = "ongoing"
    else:
        try:
            int(war.winner)
        except:
            war_outcome = war.winner
        else:
            if int(war.winner) == nation.pk:
                war_outcome = '<span style="color: green">Won</span>'
            else:
                 war_outcome = '<span style="color: red">Lost</span>'
    return mark_safe(war_outcome)

register.filter('outcome', outcome)


def war_otherguy(war, nation):
    if war.defender.pk == nation.pk:
        target = war.attacker.name
    else:
         target = war.defender.name
    return mark_safe(target)

register.filter('war_otherguy', war_otherguy)


def losses(war, nation):
    return mark_safe(50)

register.filter('losses', losses)


def aiddirection(direction):
    return mark_safe(('From' if direction == 'in' else 'To'))

register.filter('aiddirection', aiddirection)


#this is a bit redundant but whatever lol
def warstatus(war, nation):
    if war.winner == '':
        war_outcome = "ongoing"
    else:
        try:
            int(war.winner)
        except:
            war_outcome = war.winner
        else:
            if war.winner == '':
                war_outcome = "ongoing"
            elif int(war.winner) == nation.pk:
                war_outcome = 'won'
            else:
                 war_outcome = 'lost'
    return mark_safe(war_outcome)

register.filter('warstatus', warstatus)


def aidname(resource):
    return mark_safe(v.aidnames[resource])


register.filter('aidname', aidname)


def aidamount(aidobject):
    txt = ''
    if aidobject.resource == 'budget':
        txt = "$%sk" % aidobject.amount
    else:
        txt = "%s" % aidobject.amount

    return mark_safe(txt)



register.filter('aidamount', aidamount)



@register.inclusion_tag('mod/ip_list.html', takes_context=True)
def ip_listing(context):
    return context



    