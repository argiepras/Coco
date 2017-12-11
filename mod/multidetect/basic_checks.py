from nation.models import *
from nation.turnchange import rmgain, mgdisplaywrapper, oilgain, foodgain_agriculture
from django.utils import timezone
import math


def trade_balance_check(nation):
    #trade balance accounts for the in and outs
    #sending out sends it into the negatives
    #receiving goes positive
    base = base_production(nation) + nation.gdp
    #base constitutes the total production
    threshold = base * factor(nation)
    tb = nation.trade_balance
    tb = (tb if tb > 0 else -tb)
    if tb > threshold:
        nation.multimeter.trade_balance += 2
        if tb > threshold*2:
            nation.notes.get_or_create(
                auto_type="trade balance",
                note="Player has very unbalanced trades")

    

def trade_balance_changes(nation):
    threshold = base_production(nation) + nation.gdp
    turnly_change = nation.multimeter.trade_balances.latest().change
    change = 2
    if threshold < turnly_change:
        change -= 4
    if threshold * 2 < turnly_change:
        change -= 2
    nation.multimeter.trade_balance += change


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
    baseproduction += foodgain_agriculture(nation) * prices['food']
    
    return baseproduction


def actionchecks(nation):
    #check if the actions are bare basics
    #lazy multis just maintain, so daily actions look similar
    begin = nation.creationtime


#Cross referencing logout to login times with people that has sent/recieved aid
#from the target player
#since the whole point of multis is to enrich yourself in a many  to one fashion
#this might work


def compare_logins(nation):
    login_nations, logout_hits = log_checks(nation, 'login_logs', Logoutlog)
    logout_nations, login_hits = log_checks(nation, 'logout_logs', Loginlog)

    if logout_hits:
        nation.multimeter.logouts += len(logout_hits) * 10 / len(login_nations)

    if login_hits:
        nation.multimeter.logins += len(login_hits) * 10 / len(logout_nations)

    if not login_hits and not logout_hits:
        nation.multimeter.logins -= 2
        nation.multimeter.logouts -= 2


def log_checks(nation, log, targetmodel):
    turn = ID.objects.get().turn
    times = getattr(nation, log).filter(turn=turn).values_list('timestamp', flat=True)
    query = Aid.objects.filter(Q(sender=nation)|Q(reciever=nation))
    nations = list(set(
        query.values_list('sender__pk', flat=True).distinct() + 
        query.values_list('reciever__pk', flat=True).distinct()))
    if nation.pk in nations:
        nations.remove(nation.pk)

    hits = []
    for time in times:
        #here we gather a list of primary keys that coincide with log times

        query = targetmodel.objects.filter(
            Q(timestamp__lte=timestamp + timedelta(minutes=5))&
            Q(timestamp__gte=timestamp - timedelta(minutes=5)),
            nation__pk__in=nations, turn=turn).exclude(nation=nation)
        if query.exist():
            hits.append(list(set(query.values_list('nation__pk', flat=True))))
    return nations, hits


#the logic here is that because cookies are persistent
#there isn't a big need to log in often
#with multis and bots being the exception
def login_check(nation):
    delta = timezone.now() - nation.timestamp
    if delta.days > nation.login_logs.all().count():
        nation.notes.get_or_create(
                    auto_type="login count",
                    note="Logs in frequently")
        nation.multimeter.logins += 1

#checking metas is done to catch multis who don't switch browsers but may switch proxies
def meta_check(nation):
    login_nations, logout_hits = log_checks(nation, 'login_logs', Logoutlog)
    logout_nations, login_hits = log_checks(nation, 'logout_logs', Loginlog)
    all_recipients = nation.outgoing_aid.all().values_list('recipient__pk', flat=True)
    all_senders = nation.incoming_aid.filter(turn=turn).values_list('sender__pk', flat=True)
    
    #we check metadata against login/logout hits and incoming + outgoing aid senders/recipients
    #do note that this is a list of primary keys
    to_check = list(set(login_nations + logout_nations + all_recipients + all_senders))
    metas = nation.seen_headers.all().values_list('user_agent', flat=True)
    hits = Header.objects.filter(user_agent__in=metas).exclude(nation=nation).values_list('nation__pk', flat=True)
    if len(hits) == 0:
        nation.multimeter.meta -= 2
    else:
        nation.multimeter.meta += 2
        hits = list(set(hits))
        for hit in hits:
            if hit in login_nations:
                nation.notes.get_or_create(
                    auto_type="meta login",
                    note="Same header as someone with a close login time")
            if hit in logout_nations:
                nation.notes.get_or_create(
                    auto_type="meta logout",
                    note="Same header as someone with a close logout time")


