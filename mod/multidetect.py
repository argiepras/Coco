from nation.models import Nation, Aidlog, ID, Header, Logoutlog, Loginlog, Market, current_turn
from nation.turnchange import rmgain, mgdisplaywrapper, oilgain, foodgain_agriculture
import nation.utilities as utils

from django.utils import timezone
from django.db.models import Q, Sum
import math



#for convenience sake this function is all we import into tasks.py
#neatly tying it all together and letting tasks.py just feed nations into it
def cron_detect(nation):
    trade_balance_check(nation)
    trade_balance_changes(nation)
    compare_logins(nation)
    login_check(nation)
    meta_login_check(nation)
    ip_checks(nation)
    outgoing_aid_check_volume(nation)
    outgoing_aid_by_value(nation)
    incoming_aid_check(nation)
    nation.multimeter.save()



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
            nation.multimeter.trade_balance += 2
            nation.notes.get_or_create(
                auto_type="trade balance",
                note="Player has very unbalanced trades")
    else:
        nation.multimeter.trade_balance -= 2
    

def trade_balance_changes(nation):
    threshold = base_production(nation) + nation.gdp
    turnly_change = nation.multimeter.trade_balances.latest().change
    change = -2
    if threshold < turnly_change:
        change += 4
    if threshold * 2 < turnly_change:
        change += 2
    nation.multimeter.trade_balance += change


def factor(nation):
    # returns the factor of the threshold of the trade balance allowed
    # ie x * gdp+production <= -+ trade balance
    # where x is the factor
    delta = timezone.now() - nation.creationtime
    x = math.log((delta.total_seconds() / 60**2) / 12)
    x = (x if x > 1 else 1)
    return x

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
    login_nations, logout_hits = log_checks(nation, 'login_times', Logoutlog)
    logout_nations, login_hits = log_checks(nation, 'logout_times', Loginlog)
    if logout_hits:
        nation.multimeter.logouts += len(logout_hits) * 2 / len(login_nations)
    if login_hits:
        nation.multimeter.logins += len(login_hits) * 2 / len(logout_nations)

    if not login_hits and not logout_hits:
        nation.multimeter.logins -= 2
        nation.multimeter.logouts -= 2


def log_checks(nation, log, targetmodel):
    turn = ID.objects.get().turn
    turns = [x for x in range(turn-5, turn)]
    times = getattr(nation, log).filter(turn__in=turns).values_list('timestamp', flat=True)
    query = Aidlog.objects.filter(Q(sender=nation)|Q(reciever=nation))
    nations = list(set(
        list(query.values_list('sender__pk', flat=True).distinct()) + 
        list(query.values_list('reciever__pk', flat=True).distinct())))
    if nation.pk in nations:
        nations.remove(nation.pk)
    hits = []
    for timestamp in times:
        #here we gather a list of primary keys that coincide with log times
        query = targetmodel.objects.filter(
            Q(timestamp__lte=timestamp + timezone.timedelta(minutes=60))&
            Q(timestamp__gte=timestamp - timezone.timedelta(minutes=60)),
            nation__pk__in=nations).exclude(nation=nation)
        if query.exists():
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
def meta_login_check(nation):
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
            if hit in all_recipients:
                nation.notes.get_or_create(
                    auto_type="meta outgoing",
                    note="Same header as someone he's sending aid to")
            if hit in all_senders:
                nation.notes.get_or_create(
                    auto_type="meta incoming",
                    note="Same header as someone he's recieving aid from")



#sending resources to and from "people" you share IP with is a nono
def ip_checks(nation):
    turn = current_turn()
    to_check = nation.outgoing_aid.filter(
        Q(turn=turn-2)|Q(turn=turn-1)|Q(turn=turn)).distinct().values_list('reciever__pk', flat=True)
    to_check = list(set(to_check))
    ips = nation.IPs.all().values_list('IP', flat=True)
    ips = list(set(ips))
    
    offenders = IP.objects.all().exclude(nation=nation).filter(
        IP__in=ips, 
        nation__pk__in=to_check).values_list('nation__pk', flat=True)
    offenders = list(set(offenders))
    #the list(set()) removes duplicate entries
    if len(offenders) > 0:
        nation.notes.get_or_create(
                auto_type="outgoing aid IP",
                note="Player is sending aid to someone with the same IP")

    #reset and recycle for incoming aid
    to_check = nation.incoming_aid.filter(
        Q(turn=turn-2)|Q(turn=turn-1)|Q(turn=turn)).distinct().values_list('sender__pk', flat=True)
    to_check = list(set(to_check))
    ips = nation.IPs.all().values_list('IP', flat=True)
    ips = list(set(ips))
    
    offenders = IP.objects.all().exclude(nation=nation).filter(
        IP__in=ips, 
        nation__pk__in=to_check).values_list('nation__pk', flat=True)
    offenders = list(set(offenders))
    if len(offenders) > 0:
        nation.notes.get_or_create(
                auto_type="incoming aid IP",
                note="Player is recieving aid from someone with the same IP")



###
#below here is aid checks
###


#to reiterate
#higher = more likely to be a multi


#aid by volume is the amount of times the person in question sent stuff to others
#multis will have outgoing aid mostly going to one person
#we will check both volume and value
def outgoing_aid_check_volume(nation):
    all_recipients = nation.outgoing_aid.all().values_list('reciever__pk', flat=True)
    unique_recipients = list(set(all_recipients))
    nations = {}
    for recipient in unique_recipients:
        nations[recipient] = 0

    for recipient in all_recipients:
        nations[recipient] += 1 

    highest = get_highest(nations, unique_recipients)

    try: #nations.values() can result in division by 0
        percentage = highest * 100 / sum(nations.values())
    except:
        percentage = 0
    if percentage > 35:
        nation.multimeter.aid += 1
    else:
        nation.multimeter.aid -= 1
    if percentage >= 50:
        nation.multimeter.aid += 2
        if nation.notes.filter(
                auto_type="outgoing aid by volume").exists():
            nation.notes.filter(
                auto_type="outgoing aid by volume").update(
                    note="Player has %s%% of outgoing aid going to a single player by volume" % percentage)
        else:
            nation.notes.create(
                auto_type="outgoing aid by volume",
                note="Player has %s%% of outgoing aid going to a single player by volume" % percentage)


def outgoing_aid_by_value(nation):
    all_recipients = nation.outgoing_aid.all().values_list('reciever__pk', flat=True)
    unique_recipients = list(set(all_recipients))
    nations = {}
    for recipient in unique_recipients:
        nations[recipient] = nation.outgoing_aid.filter(pk=recipient).aggregate(Sum('value'))['value__sum']
    highest = get_highest(nations, unique_recipients)
    try: #nations.values() can result in division by 0
        percentage = highest * 100 / sum(nations.values())
    except:
        percentage = 0
    if percentage > 35:
        nation.multimeter.aid += 1
    else:
        nation.multimeter.aid -= 1
    if percentage >= 50:
        nation.multimeter.aid += 2
        if nation.notes.filter(
                auto_type="outgoing aid by value").exists():
            nation.notes.filter(
                auto_type="outgoing aid by value").update(
                    note="Player has %s%% of outgoing aid going to a single player by value" % percentage)
        else:
            nation.notes.create(
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
    turns = [x for x in range(turn-3, turn)]
    all_senders = nation.incoming_aid.all().values_list('sender__pk', flat=True)
    unique_senders = list(set(all_senders))
    change = -2
    hits = 0.0
    for sender in unique_senders:
        turn_hits = {}
        for turn in turns:
            turn_hits[turn] = 0
        for x in turns: #check the current turns aid against the previous 3 turns aid logs
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
            keys = turn_hits.keys()
            if turn_hits[keys[0]] == turn_hits[keys[1]] == turn_hits[keys[2]]:
                naugty_boy = utils.link_me(Nation.objects.get(pk=sender))
                nation.notes.get_or_create(
                    note="Player has recieved similar aid from %s 3 turns in a row" % naugty_boy,
                    auto_type="incoming hat-trick"
                    )
    if hits > 0:
        change += hits

    nation.multimeter.aid += change