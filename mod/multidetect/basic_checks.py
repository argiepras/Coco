from nation.models import *
from nation.turnchange import rmgain, mgdisplaywrapper, oilgain, foodgain
from django.utils import timezone
import math





def basic_aid_check(nation):
    aid = nation.outgoing_aid.all()
    nations = {}
    total = len(aid)
    # if more than 50% of all aid is going to one person, probably a multi
    for x in aid:
        if x.reciever.name in x:
            nations[x.reciever.name] += 1
        else:
            nations.update({x.reciever.name: 1})

    for entry in nations:
        if total * (nations[entry] / 100.0) >= 50:
            return True
    return False



def trade_balance_check(nation):
    #trade balance accounts for the in and outs
    #sending out sends it into the negatives
    #receiving goes positive
    base = base_production(nation) + nation.gdp
    threshold = base * factor(nation)
    if nation.trade_balance > 0: #multis are usually used to send out stuff
        #where as regular players might have a surplus because alliance flooding
        pass
        #to be implemented later

    return threshold < nation.trade_balance or threshold < nation.trade_balance*-1



def factor(nation):
    # returns the factor of the threshold of the trade balance allowed
    # ie x * gdp+production <= -+ trade balance
    # where x is the factor
    delta = timezone.now() - nation.creationtime
    return math.log((delta.total_seconds() / 60**2) / 12)


def base_production(nation):
    baseproduction = 0 
    #base production is total worth of production
    prices = Market.objects.latest('pk').prices()
    baseproduction += rmgain(nation) * prices['rm']
    baseproduction += mgdisplaywrapper(nation) * prices['mg']
    baseproduction += oilgain(nation) * prices['oil']
    baseproduction += foodgain(nation) * prices['food']
    
    return baseproduction


def actionchecks(nation):
    #check if the actions are bare basics
    #lazy multis just maintain, so daily actions look similar
    begin = nation.creationtime
