from nation.models import *
import nation.utilities as utils
import nation.variables as v
import random

from django.db import IntegrityError, OperationalError


class EventHandler(object):
    events = {}

    def register_event(self, event_name, event):
        self.events.update({event_name: event})

    def get_event(self, newsitem):
        nation = newsitem.nation
        return self.events[newsitem.content](nation)

    def assign_event(self, nation, event):
        if not event in self.events:
            return False
        nation.news.create(content=event, event=True, deletable=self.events[event].instant_apply)


    def process_event(self, nation, eventname, choice):
        #called when someone presses a button and makes a decision with an event
        #fetches the corresponding event and applies the changes the players choice has
        if not eventname in self.events:
            return "You do not have this event!"
        event = self.events[eventname](nation)
        result = event.apply_choice(choice)
        if result:
            nation.event_history.create(event=eventname, choice=choice)
            return result
        return "You do not have this event!"


    def trigger_events(self, nation):
        #called at turn change to trigger events
        #iterates over the list of registered events and have them check if eligible
        #if true, create event
        event_count = 0
        for event in self.events:
            eventtype = self.events[event](nation)
            if eventtype.conditions(nation):
                if nation.news.filter(content=event).exists() and not eventtype.apply_instantly:
                    continue
                elif event_count > 0 and not eventtype.apply_instantly:
                    if random.randint(1, 10) > 5: #50% chance of getting a second event
                        continue
                nation.news.create(event=True, content=event, deletable=eventtype.apply_instantly)
                if eventtype.apply_instantly:
                    while True:
                        try:
                            eventtype.instant_apply()
                        except IntegrityError, OperationalError:
                            #row is likely locked, meaning something has changed
                            #reinitialize the event and try again
                            eventtype = self.events[event](nation)
                            continue
                        break
                else:
                    event_count += 1


eventhandler = EventHandler()


class Event_base(object):
    def __init__(self, nation):
        self.nation = nation

    apply_instantly = False

    def apply_choice(self, choice):
        if choice not in self.choices:
            return False
        data = self.choices[choice]
        if data['model'] == Nation:
            pk = self.nation.pk
        else:
            pk = data['model'].objects.filter(nation=self.nation)[0].pk
        utils.atomic_transaction(data['model'], pk, data['actions'])
        return self.result[choice]

    def instant_apply(self):
        for action in self.choices:
            data = self.choices[action]
            if data['model'] == Nation:
                pk = self.nation.pk
            else:
                pk = data['model'].objects.filter(nation=self.nation)[0].pk
            utils.atomic_transaction(data['model'], pk, data['actions'])