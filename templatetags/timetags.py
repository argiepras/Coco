from django import template
from django.utils.safestring import mark_safe
register = template.Library()


def timer(delta):
    seconds = delta.seconds
    hours = seconds / 3600
    hours += delta.days*24
    if hours == 0:
        hours = seconds / 60
        return mark_safe("%s minutes" % hours)
    return mark_safe("%s hours" % hours)

register.filter('timer', timer)