from nation.models import Modnote, current_turn
from nation.turnchange import rmgain, mgdisplaywrapper, oilgain, foodgain

from django.utils import timezone
from django.db.models import Sum

import math



#aid by volume is the amount of times the person in question sent stuff to others
#multis will have outgoing aid mostly going to one person
#we will check both volume and value
def outgoing_aid_check_volume(nation):
    all_recipients = nation.outgoing_aid.all().values_list('recipient__pk', flat=True)
    unique_recipients = list(set(all_recipients))
    nations = {}
    for recipient in unique_recipients:
        nations[recipient] = 0

    for recipient in all_recipients:
        nations[recipient] += 1 

    highest = get_highest(nations, unique_recipients)

    percentage = highest * 100 / sum(nations.values())
    if percentage > 35:
        nation.multimeter.aid -= 1
    else:
        nation.multimeter.aid += 1
    if percentage >= 50:
        nation.multimeter.aid -= 2
        if Modnote.objects.filter(
                nation=nation,
                auto_type="outgoing aid by volume").exists():
            Modnote.objects.filter(
                nation=nation,
                auto_type="outgoing aid by volume").update(
                    note="Player has %s%% of outgoing aid going to a single player by volume" % percentage)
        else:
            Modnote.objects.create(
                nation=nation,
                auto_type="outgoing aid by volume",
                note="Player has %s%% of outgoing aid going to a single player by volume" % percentage)


def outgoing_aid_by_value(nation):
    all_recipients = nation.outgoing_aid.all().values_list('recipient__pk', flat=True)
    unique_recipients = list(set(all_recipients))
    nations = {}
    for recipient in unique_recipients:
        nations[recipient] = nation.outgoing_aid.filter(pk=recipient).aggregate(Sum('value'))['value__sum']

    highest = get_highest(nations, unique_recipients)
    percentage = highest * 100 / sum(nations.values())
    if percentage > 35:
        nation.multimeter.aid -= 1
    else:
        nation.multimeter.aid += 1
    if percentage >= 50:
        nation.multimeter.aid -= 2
        if Modnote.objects.filter(
                nation=nation,
                auto_type="outgoing aid by value").exists():
            Modnote.objects.filter(
                nation=nation,
                auto_type="outgoing aid by value").update(
                    note="Player has %s%% of outgoing aid going to a single player by value" % percentage)
        else:
            Modnote.objects.create(
                nation=nation,
                auto_type="outgoing aid by value",
                note="Player has %s%% of outgoing aid going to a single player by value" % percentage)


def get_highest(nations, unique_recipients):
    highest = 0
    for recipient in unique_recipients:
        if nations[recipient] > highest:
            highest = nations[recipient]
    return highest


#incoming is a bit different since multis will be sending out instead of in
#so checking for regular shipments among the senders is the way to go
#it's also very heavy on the IO
def incoming_aid_check(nation):
    turn = current_turn() #current_turn() is housed in models.py
    all_senders = nation.incoming_aid.filter(turn=turn).values_list('sender__pk', flat=True)
    unique_senders = list(set(all_senders))
    change = -2
    hits = 0.0
    for sender in unique_senders:
        turn_hits = {turn - 1: 0, turn - 2: 0, turn - 3: 0}
        for x in [turn - 1, turn - 2, turn - 3]: #check the current turns aid against the previous 3 turns aid logs
            if nation.incoming_aid.filter(turn=x, sender__pk=sender).exists():
                logs = nation.incoming_aid.filter(turn=turn, sender__pk=sender)
                for log in logs:
                    #if the person has sent the same thing +- 25% in the last 3 turns
                    if nation.incoming_aid.filter(
                            Q(amount__gte=int(log.amount*0.75))|Q(amount__lte=int(log.amount*1.25)),
                            turn=x, 
                            resource=log.resource).exists():
                        hits += 1
                        turn_hits[x] += 1
                        #there may be legitimate reasoning behind regular shipments
                        #likely discussed in comms
                        if nation.comms.filter(sender__pk=sender).exists():
                            hits -= 0.5
        if sum(turn_hits) > 0:
            if turn_hits[turn - 1] == turn_hits[turn - 2] == turn_hits[turn - 3]:
                naugty_boy = utils.link_me(Nation.objects.get(pk=sender))
                nation.notes.get_or_create(
                    note="Player has recieved similar aid from %s 3 turns in a row" % naugty_boy,
                    auto_type="incoming hat-trick"
                    )

    if hits > 0:
        change += hits / 2

    nation.multimeter.aid += change