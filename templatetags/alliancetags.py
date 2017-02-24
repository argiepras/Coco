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