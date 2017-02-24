from django import template
from django.utils.safestring import mark_safe
from django.db.models import Sum
import nation.variables as v
import nation.utilities as utils
from math import sqrt
import nation.turnchange as change

register = template.Library()


def infilchanges(spy):
    txt = ''
    if spy.location == spy.nation:
        txt += '<p style="color: green">+%s from home country.</p>' % change.spygain_home(spy)
    else:
        gain = change.spygain_alignment(spy)
        if gain > 0:
            txt += '<p style="color: green">+%s from opposite alignment.</p>' % gain
        gain = change.spygain_subregion(spy)
        if gain > 0:
            txt += '<p style="color: green">+%s from same subregion.</p>' % gain
        gain = change.spygain_region(spy)
        if gain > 0:
            txt += '<p style="color: green">+%s from same region.</p>' % gain

    if spy.experience > 24:
        txt += '<p style="color: green">+%s from experience.</p>' % change.spygain_experience(spy)

    if txt == '':
        txt = '<p>No change</p>'

    return mark_safe(txt)

register.filter('infilchanges', infilchanges)


def status(spy):
    txt = ''
    if spy.location == spy.nation:
        txt = "Awaiting instructions"
    elif spy.arrested:
        txt = "Under arrest"
    elif spy.specialty == "Intelligence":
        txt = "Gathering intel"
    elif spy.deploytime < 1:
        txt = "Finding safehouse"
    elif spy.deploytime < 5:
        txt = "Establishing network"
    elif spy.deploytime < 15:
        txt = "Expanding network"
    elif spy.deploytime < 25:
        txt = "Infiltrating the government"
    else:
        txt = "Coordinating with the %s" % v.agencies[spy.nation.alignment]
    return mark_safe(txt)


register.filter('status', status)


def foreignstatus(spy):
    txt = ''
    if spy.arrested:
        txt = "Imprisoned"
    elif spy.surveillance:
        txt = "Under surveillance"
    elif spy.specialty == "Intelligence":
        txt = "Gathering intel"
    elif spy.deploytime < 1:
        txt = "Finding safehouse"
    elif spy.deploytime < 5:
        txt = "Establishing network"
    elif spy.deploytime < 15:
        txt = "Expanding network"
    elif spy.deploytime < 25:
        txt = "Infiltrating the government"
    else:
        txt = "Coordinating with the %s" % v.agencies[spy.nation.alignment]
    return mark_safe(txt)


register.filter('foreignstatus', foreignstatus)


