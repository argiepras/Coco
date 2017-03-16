from django.shortcuts import render, redirect
from django.contrib.auth import update_session_auth_hash
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.db import transaction
from django.utils import timezone
#django stuff

#then other stuff
from .models import *
from .forms import *
from . import utilities as utils


def aidnews(sender, reciever, resource, amount):
    link = '<a href="%s"><b>%s</b></a>' % (sender.get_absolute_url(), sender.name)
    flavor = v.pretty(amount, resource).replace('our', 'their') #someone is not sending us n of our best food
    newsitem = "We have recieved %s from %s! How generous!" % (flavor, link)
    reciever.news.create(content=newsitem)



################################
#### War related news items ####
################################


def wardec(declarer, victim):
    link = '<a href="%s"><b>%s</b></a>' % (declarer.get_absolute_url(), declarer.name)
    txt = "%s has declared war on us! We must mobilize the troops \
        and to defend our country and people!" % link
    victim.news.create(content=txt)

def defeated(winner, loser, actions):
    link = '<a href="%s"><b>%s</b></a>' % (winner.get_absolute_url(), winner.name)
    txt = "%s has crushed the remainders of our armed forces and defeated us! " % link
    txt += ""


def peace(peacer, peacee):
    link = '<a href="%s"><b>%s</b></a>' % (peacer.get_absolute_url(), peacer.name)
    txt = "%s has sued for peace! Is it time to end this conflict?" % link
    peacee.news.create(content=txt)


def peaceaccept(peacer, peacee):
    link = '<a href="%s"><b>%s</b></a>' % (peacee.get_absolute_url(), peacee.name)
    txt = link + " has accepted our peace proposal! Peace in our time."
    peacer.news.create(content=txt)


#########
## ground attack
######
def groundengagement(aggro, victim, aggroloss, victimloss):
    link = '<a href="%s"><b>%s</b></a>' % (aggro.get_absolute_url(), aggro.name)
    txt = link + " has engaged our ground forces!"
    win = (True if aggroloss > victimloss else False)
    if aggroloss > 0:
        aggroloss = "%sk" % aggroloss
    if victimloss > 0:
        victimloss = "%sk" % victimloss
    if win:
        txt += " In the resulting battle, our troops held the ground and inflicted roughly %s \
        casualties on the enemy army whilst only suffering %s casualties" % (aggroloss, victimloss)
    else:
        txt += " In the resulting battle, our troops suffered a defeat! We lost %s soldiers \
        while only killing %s enemy combatants!" % (victimloss, aggroloss)
    victim.news.create(content=txt)

#######
## chems
######
def chemmed(aggro, victim, troops, gdploss):
    link = '<a href="%s"><b>%s</b></a>' % (aggro.get_absolute_url(), aggro.name)
    txt = link + " launched chemical attacks on populated areas and military positions alike, \
        thousands of civilian lives were lost, along with %sk military personnel \
        and $%sm worth of economic damages!" % (troops, gdploss)
    victim.news.create(content=txt)

#########
### navy
########

def navalbombardment(aggro, victim, loss):
    link = '<a href="%s"><b>%s</b></a>' % (aggro.get_absolute_url(), aggro.name)
    txt = link + " used their navy to bombard our military positions, \
    resulting in %sk casualties" % loss
    victim.news.create(content=txt)


def navalengage(aggro, victim, aggroloss, victimloss):
    link = '<a href="%s"><b>%s</b></a>' % (aggro.get_absolute_url(), aggro.name)
    txt = link + " engaged our navy in the open waters, sinking %s of our ships." % victimloss
    if aggroloss > 0:
        txt += " But we also managed to sink %s of the enemy ships." % aggroloss
    victim.news.create(content=txt)

#########
#### air
########


def airbattle(aggro, victim, won):
    link = '<a href="%s"><b>%s</b></a>' % (aggro.get_absolute_url(), aggro.name)
    if won:
        txt = link + " bombed our airfields, reducing the size of our airforce!"
    else:
        txt = link + " tried to bomb our airfields, but our airforce intercepted their planes\
        shooting them down!"
    victim.news.create(content=txt)


def groundbombing(aggro, victim, loss):
    link = '<a href="%s"><b>%s</b></a>' % (aggro.get_absolute_url(), aggro.name)
    if loss:
        txt = link + " has bombed our military positions and installations resulting in %sk \
        casualties!" % loss
    else:
        txt = link + " tried to bomb our military positions, but was intercepted by our airforce!"
    victim.news.create(content=txt)


def econbombing(aggro, victim, loss):
    link = '<a href="%s"><b>%s</b></a>' % (aggro.get_absolute_url(), aggro.name)
    if loss:
        txt = link + " has bombed our economic infrastructure! We lost $5m worth of growth and \
        $%s millions worth of damage to our GDP!" % loss
    else:
        txt = link + " tried to bomb our infrastructure, but was intercepted by our airforce!"
    victim.news.create(content=txt)


def citybombing(aggro, victim, won):
    link = '<a href="%s"><b>%s</b></a>' % (aggro.get_absolute_url(), aggro.name)
    if won:
        txt = link + " bombed our city centers, reducing available manpower and the \
        quality of life of our citizens!"
    else:
        txt = link + " tried to bomb our city centers, but our airforce intercepted their planes\
        shooting them down!"
    victim.news.create(content=txt)


def navalbombing(aggro, victim, won):
    link = '<a href="%s"><b>%s</b></a>' % (aggro.get_absolute_url(), aggro.name)
    if won:
        txt = link + " has performed a bombing run on our navy, sinking one of our ships!"
    else:
        txt = link + " tried to bomb our navy, but fighters on a training exercise managed to \
        intercept them, reducing enemy airforce strength!"
    victim.news.create(content=txt)


def industrybombing(aggro, victim, won):
    link = '<a href="%s"><b>%s</b></a>' % (aggro.get_absolute_url(), aggro.name)
    if won:
        txt = link + " has bombed one of our factories, reducing it to rubble!"
    else:
        txt = link + " tried to bomb our factories, but was intercepted and shot down\
        reducing their airforce strength!"
    victim.news.create(content=txt)


def oilbombing(aggro, victim, won):
    link = '<a href="%s"><b>%s</b></a>' % (aggro.get_absolute_url(), aggro.name)
    if won:
        txt = link + " has bombed one of our oil wells, reducing it to giant pillar of black smoke!"
    else:
        txt = link + " tried to bomb our oil wells, but was intercepted and shot down\
        reducing their airforce strength!"
    victim.news.create(content=txt)


def chembombing(aggro, victim, won):
    link = '<a href="%s"><b>%s</b></a>' % (aggro.get_absolute_url(), aggro.name)
    if won:
        txt = link + " has bombed one of our chemical weapons storage facilities,\
         reducing our capabilities!"
    else:
        txt = link + " tried to bomb our chemical weapons storage facilities, but was intercepted and shot down\
        reducing their airforce strength!"
    victim.news.create(content=txt)


def agentorange(aggro, victim, won):
    link = '<a href="%s"><b>%s</b></a>' % (aggro.get_absolute_url(), aggro.name)
    if won:
        txt = link + " has bombed our farms, killing our crops and reducing our food production!"
    else:
        txt = link + " tried to bomb our farms, but early warning systems lead to a swift interception\
        and a reduction in enemy airforce strength!"
    victim.news.create(content=txt)

###############################
#### Alliance related news ####
###############################

def kicked(victim, alliance):
    link = '<a href="%s"><b>%s</b></a>' % (alliance.get_absolute_url(), alliance.name)
    txt = "We recieved a memo from %s saying that our membership have been terminated!" % link
    victim.news.create(content=txt)

def invited(invitee, alliance):
    link = '<a href="%s"><b>%s</b></a>' % (alliance.get_absolute_url(), alliance.name)
    txt = "We have a recieved an invitation to join %s! Go to their alliance page to accept/reject" % link
    invitee.news.create(content=txt)

def initiative_recalled(nation, initiative):
    txt = "The alliance bank has run out of funds and as a consequence the %s initiative has been recalled!" % initiative
    nation.news.create(content=txt)

def acceptedapplication(nation, alliance):
    link = '<a href="%s"><b>%s</b></a>' % (alliance.get_absolute_url(), alliance.name)
    txt = "%s has accepted your application for membership!" % link
    nation.news.create(content=txt)


def rejectedapplication(nation, alliance):
    link = '<a href="%s"><b>%s</b></a>' % (alliance.get_absolute_url(), alliance.name)
    txt = "%s has rejected your application for membership!" % link
    nation.news.create(content=txt)

def newapplicant(nation, alliance):
    link = '<a href="%s"><b>%s</b></a>' % (alliance.get_absolute_url(), alliance.name)
    txt = "A new nation has applied to be a member of %s!" % link
    nation.news.create(content=txt)

def random_tofounder(nation, alliance):
    link = '<a href="%s"><b>%s</b></a>' % (alliance.get_absolute_url(), alliance.name)
    txt = "The previous leader stepped down and you have been picked as the new founder of %s!" % link
    nation.news.create(content=txt)

def heir_tofounder(nation, alliance):
    link = '<a href="%s"><b>%s</b></a>' % (alliance.get_absolute_url(), alliance.name)
    txt = "The previous leader stepped down and you have assumed the role as founder of %s!" % link
    nation.news.create(content=txt)



#####################
### Spy stuff lol ###
#####################

def armrebels(nation):
    txt = "A foreign agent has been caught trying to arm rebels in our country!\
        The agent responsible has been arrested!"
    nation.news.create(content=txt)

def fundopposition(nation):
    txt = "A foreign agent has been caught trying to fund the opposition in our country!\
        The agent responsible has been arrested!"
    nation.news.create(content=txt)

def terroristattack(nation):
    txt = "A foreign agent has been caught planning a terrorist attack in our country!\
        The agent responsible has been arrested!"
    nation.news.create(content=txt)

def terroristattacked(nation):
    txt = "We been struck by a terrorist attack! Countless innocent civilians have\
        perished and our stability has decreased!"
    nation.news.create(content=txt)

def sabotagewell(nation):
    txt = "A foreign agent has been caught trying to sabotage our oil production!\
        The agent responsible has been arrested!"
    nation.news.create(content=txt)

def sabotagedwell(nation):
    txt = "One of our oil wells suffered a catastrophic failure and has been closed permanently. \
        Inspectors thinks it was sabotage."

def sabotagemine(nation):
    txt = "A foreign agent has been caught trying to sabotage our raw materials production!\
        The agent responsible has been arrested!"
    nation.news.create(content=txt)

def sabotagedmine(nation):
    txt = "One of our mines has collapsed! About two dozen miners died and it appears to be sabotage!"
    nation.news.create(content=txt)

def poisoncrops(nation):
    txt = "A foreign agent was caught preparing to poison a field of crops! He has been placed under arrest."
    nation.news.create(content=txt)

def poisonedcrops(nation):
    txt = "Many farmers have experienced sudden crop death! Further investigation reveals intentional poisoning!"
    nation.news.create(content=txt)

def caughtspyarrested(nation):
    txt = "A foreign agent was caught trying to cross the border! He was immediately arrested."
    nation.news.create(content=txt)

def caughtspyreturn(nation):
    txt = "A foreign agent was caught trying to cross the border! The squad leader that \
        discovered him decided to send him back where he came from."
    nation.news.create(content=txt)

def caughtspyreturning(nation, target):
    txt = "A foreign agent from %s was caught trying to leave our country! He has been \
    placed under arrest." % ('<a href="%s">%s</a>' % (target.get_absolute_url(), target.name))
    nation.news.create(content=txt)

def avoidedarrest(nation, target, spy):
    txt = "Security forces in %s tried to apprehend agent %s but he managed to evade \
     and go underground." % ('<a href="%s">%s</a>' % (target.get_absolute_url(), target.name), spy.name)
    nation.news.create(content=txt)

def arrested(nation, target, spy):
    txt = "Security forces in %s has placed agent %s under arrest!" % \
    ('<a href="%s">%s</a>' % (target.get_absolute_url(), target.name), spy.name)
    nation.news.create(content=txt)

def deported(nation, target, spy):
    txt = "%s has deported agent %s." % \
    ('<a href="%s">%s</a>' % (target.get_absolute_url(), target.name), spy.name)
    nation.news.create(content=txt)

def executed(nation, target, spy):
    txt = "%s has executed agent %s!" % \
    ('<a href="%s">%s</a>' % (target.get_absolute_url(), target.name), spy.name)
    nation.news.create(content=txt)

def extradition_request(nation, target, spy):
    link = '<a href="%s">%s</a>' % (target.get_absolute_url(), target.name)
    linkspyowner = '<a href="%s">%s</a>' % (spy.nation.get_absolute_url(), spy.nation.name)
    txt = "%s has requested that we recieve an agent %s from %s!" % \
        (link, spy.name, linkspyowner)
    nation.news.create(content=txt)

def extradited(nation, target, spy):
    txt = "Sources are telling us that %s has been moved to %s!" % \
       (spy.name, '<a href="%s">%s</a>' % (target.get_absolute_url(), target.name)) 
    nation.news.create(content=txt)

def extraditioned(nation, target, v, spy):
    link = '<a href="%s">%s</a>' % (target.get_absolute_url(), target.name)
    txt = "%s has %s our extradition request!" % (link, v)
    nation.news.create(content=txt)
    if v == 'accepted':
        txt = "Sources are telling us that %s has been moved to %s!" % \
           (spy.name, link) 
        spy.nation.news.create(content=txt)

def avoidedaccident(spy):
    txt = "Agent %s narrowly avoided an execution disguised as an accident!" % spy.name
    spy.nation.news.create(content=txt)

def accidentally(spy):
    link = '<a href="%s">%s</a>' % (spy.location.get_absolute_url(), spy.location.name)
    txt = "Agent %s has been killed in what appears to be an accident in %s!" % (spy.name, link)
    spy.nation.news.create(content.txt)




#########################
## Base nuked news items
#########################

def nuked(nation, nuker):
    link = '<a href="%s">%s</a>' % (nuker.get_absolute_url(), nuker.name)
    txt = "%s has dropped a nuke into our capital, killing hundreds of \
    thousands innocent civilians! Our industrial and military capability has been \
    obliterated, and our economy is taken aback from the sheer destruction caused.\
    Hopefully, the world community will take action against this cruel act..." % link
    nation.news.create(content=txt)


def global_nuked(nation, region):
    txt = "A nuclear weapon has been detonated in %s! Economic development in %s is \
    hampered from the shock of such a weapon being unleashed, and the radioactive \
    fallout spreads across the planet, impacting the quality of life of billions!" % \
    (region, region)
    nation.news.create(content=txt)
