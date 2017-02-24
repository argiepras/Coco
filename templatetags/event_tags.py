from django import template
from nation.events import *

register = template.Library()


@register.inclusion_tag('nation/event.html', takes_context=True)
def event_display(context, newsitem):
    nation = context['nation']
    event = eventhandler.get_event(newsitem)
    buttons = []
    for button in event.fields():
        buttons.append({
            'name': button,
            'description': event.buttons[button],
            'tooltip': event.tooltips[button],
            })
    return {
        'buttons': buttons,
        'description': event.description,
        'img': event.img,
        'id': newsitem.pk,
    }


