from django import template
from django.utils.safestring import mark_safe
import nation.variables as v
import nation.utilities as utils

register = template.Library()


def kick(permissions, member):
    return permissions.can_kick(member)

register.filter('kick', kick)

def iconsize(permissions):
    size = 30-permissions.template.rank*2
    txt = "max-width: %(size)spx; max-height: %(size)spx;" % {'size': size}
    return mark_safe(txt)

register.filter('iconsize', iconsize)


def banktotal(total):
    if total > 0:
        txt = '+$%sk' % total
        txt = '<span class="green">%s</span>' % txt
    elif total < 0:
        total *= -1
        txt = '-$%sk' % total
        txt = '<span class="red">%s</span>' % txt
    else:
        txt = '<span>$0k</span>'
    return mark_safe(txt)


register.filter('banktotal', banktotal)


def remaining_limit(nation, resource):
    stockpile = nation.__dict__[resource]
    bankstock = nation.alliance.bank.__dict__[resource]
    if nation.alliance.bank.limit and not nation.permissions.template.founder:
        limit = nation.alliance.bank.__dict__['%s_limit' % resource] - nation.memberstats.__dict__[resource]
        maxwithdraw = (limit if limit < bankstock else bankstock)
    else:
        maxwithdraw = bankstock
    return mark_safe(maxwithdraw)
    
register.filter('remaining_limit', remaining_limit)


def check_permission(permissions, permission):
    #simple wrapper for the permissions method
    #since templates don't allow passing arguments
    return permissions.has_permission(permission)

register.filter('check_permission', check_permission)