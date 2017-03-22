from django import template
from django.utils.safestring import mark_safe
import nation.variables as v

register = template.Library()

def align(text, nation):
    if nation.alignment == 1:
        toreturn = 'ussr.png'
    elif nation.alignment == 2:
        toreturn = 'neutral.png'
    else:
        toreturn = 'us.png'
    return mark_safe(text + toreturn)

register.filter('align', align)


def offerdisplay(offer):
    if nation.alignment == 1:
        toreturn = 'ussr.png'
    elif nation.alignment == 2:
        toreturn = 'neutral.png'
    else:
        toreturn = 'us.png'
    return mark_safe(text + toreturn)

register.filter('offerdisplay', offerdisplay)


def tariff(offer, player):
    return offer.tariff * offer.request_amount

register.filter('tariff', tariff)


def offerformat(amount, offertype):
    return mark_safe(v.pretty(amount, offertype, True))

register.filter('offerformat', offerformat)