from django import template
from django.utils.safestring import mark_safe
import nation.variables as v
import nation.utilities as utils

register = template.Library()


def kick(permissions, member):
    return mark_safe(permissions.can_kick(member))


register.filter('kick', kick)

def iconsize(permissions):
	return mark_safe(20-permissions.template.rank)

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