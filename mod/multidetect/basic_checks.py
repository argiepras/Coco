from nation.models import *
from nation.turnchange import rmgain, mgdisplaywrapper, oilgain, foodgain
from django.utils import timezone
import math







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
    gains = {
        'rm': rmgain(nation),
        'mg': mgdisplaywrapper(nation),
        'oil': oilgain(nation),
        'food': foodgain(nation)
    }
    for gain in gains:
        baseproduction += gains[gain] * prices[gain]
    return baseproduction


