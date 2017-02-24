from django.utils import timezone
from django.db.models import Sum

import nation.utilities as utils
from nation.models import *
import nation.variables as v
from math import sqrt


###################################
###
### Holds all the functions that relates to attribute changes
### that happens when turns fire
###
### This is to keep it all in one place so tooltips and turncode doesn't have their own copy
### just makes it easier to maintain
###
###################################


def nation_income(nation):
    if nation.has_alliance():
        pass


######################
## Alliance stuff lol
######################

def alliancetotal(alliance, display=False):
    membercount = alliance.members.filter(deleted=False, vacation=False).count()
    income = allianceincome(alliance, display)
    litcost = alliance_litcost(alliance, membercount)
    healthcost = alliance_healthcost(alliance, membercount)
    freedomcost = alliance_freedomcost(alliance)
    weaponcost = alliance_weapcost(alliance, membercount)
    return income - litcost - healthcost - freedomcost - weaponcost



def alliance_expenditures(alliance):
    pass    



def allianceincome(alliance, display=False):
    initiatives = alliance.initiatives
    stats = {}
    totalgdp = alliance.members.filter(deleted=False, vacation=False).aggregate(Sum('gdp'))['gdp__sum']
    try:
        alliance.averagegdp = totalgdp / alliance.members.filter(deleted=False, vacation=False).count()
    except:
        continue #empty alliance
    alliancegain = 0
    for member in alliance.members.filter(vacation=False, deleted=False).iterator():
        if utils.vaccheck(member):
            continue
        if member.budget > member.gdp*2:
            continue
        taxrate = alliance.taxrate(member)
        bracket = alliance.taxtype(member)
        memberincome = nation.gdp / 72
        if bracket in stats:
            stats

        




def alliance_litcost(alliance, membercount):
    cost = 0
    if alliance.initiatives.literacy:
        totalgdp = alliance.averagegdp * membercount
        cost = round(totalgdp/72/25.0)
    return cost

def alliance_healthcost(alliance, membercount):
    cost = 0
    if alliance.initiatives.healthcare:
        totalgdp = alliance.averagegdp * membercount
        cost = round(totalgdp/72/25.0)
    return cost

def alliance_freedomcost(alliance):
    cost = 0
    if alliance.initiatives.freedom:
        totlit = alliance.members.filter(deleted=False, vacation=False).aggregate(Sum('literacy'))['literacy__sum']
        cost = round(totlit/50.0)
    return cost

def alliance_weapcost(alliance):
    cost = 0
    if alliance.initiatives.weapontrade:
        totweps = alliance.members.filter(deleted=False, vacation=False).aggregate(Sum('military__weapons'))['military__weapons__sum']
        cost = round(totweps/100.0)
    return cost

#################
## West rep gain
#################


def westerngain(nation):
    rep = westerngain_econ(nation)
    rep += repgain(nation)
    rep += westerngain_alignment(nation) 
    return rep + repgain(nation)

def westerngain_econ(nation):
    if nation.economy < 33:
        return -2
    elif nation.economy > 66:
        return 2
    return 0

def westerngain_alignment(nation):
    if nation.alignment == 1:
        return -5
    elif nation.alignment == 3:
        return 3
    return 0

###################
## Soviet rep gain
################### 

def sovietgain(nation):
    rep = repgain(nation)
    rep += sovietgain_alignment(nation)
    rep += sovietgain_econ(nation)
    return rep
    
def sovietgain_alignment(nation):
    if nation.alignment == 1:
        return 3
    elif nation.alignment == 3:
        return -5
    return 0

def sovietgain_econ(nation):
    if nation.economy < 33:
        return 2
    elif nation.economy > 66:
        return -2
    return 0


####################################

def repgain(nation):
    rep = 0
    if nation.reputation <= 10:
        rep -= 3
    elif nation.reputation <= 20:
        rep -= 2
    elif nation.reputation <= 30:
        rep -= 1
    elif nation.reputation >= 90:
        rep += 3
    elif nation.reputation >= 80:
        rep += 2
    elif nation.reputation >= 70:
        rep += 1
    return rep

#############
## approval
#############

def approvalchange(nation):
    if faminecheck(nation):
        return v.faminecost
    approval = 0
    if nation.qol > 70:
        approval = 1
    elif nation.qol <= 40:
        approval = -2
    if nation.approval >= 45:
        approval -= 1
    if nation.has_alliance():
        if nation.alliance.initiatives.freedom:
            if nation.government < 60:
                approval -= 1
    return approval


#############
## stability
#############

def stabilitygain(nation):
    if faminecheck(nation):
        return v.faminecost
    stability = stabilitygain_modifiers(nation, 'qol')
    stability += stabilitygain_modifiers(nation, 'approval')
    stability += stabilitygain_rebels(nation)
    stability += stabilitygain_democracy(nation)
    return stability


def stabilitygain_rebels(nation):
    stability = 0
    if nation.rebels > 8:
        stability -= 4
    elif nation.rebels > 4:
        stability -= 3
    elif nation.rebels > 0:
        stability -= 2
    return stability

def stabilitygain_democracy(nation):
    if nation.government > 60:
        if nation.approval >= 50:
            return 1
        return -1
    return 0

def stabilitygain_modifiers(nation, var):
    stability = 0
    if nation.__dict__[var]/2 > nation.stability:
        stability += 4
    elif nation.__dict__[var]/1.5 > nation.stability:
        stability += 2
    elif nation.__dict__[var] > nation.stability:
        stability += 1
    elif nation.__dict__[var]/2 < nation.stability:
        stability -= 4
    elif nation.__dict__[var]/1.5 < nation.stability:
        stability -= 2
    elif nation.__dict__[var] < nation.stability:
        stability -= 1
    return stability

def stabilitygain_growthloss(nation):
    stability = 0
    if nation.growth < -33:
        stability = -10
    return stability

def stabilitygain_openborders(nation):
    if nation.has_alliance():
        if nation.alliance.initiatives.open_borders:
            return -1
    return 0


#############
## QOL stuff 
#############

def qolgain(nation):
    qol = 0
    qol += qolgain_template(nation, 'literacy')
    qol += qolgain_template(nation, 'healthcare')
    return qol

def qolgain_template(nation, gaintype):
    qol = 0
    if nation.__dict__[gaintype]/2 > nation.qol:
        qol += 4
    elif nation.__dict__[gaintype] > nation.qol:
        qol += 2
    elif nation.__dict__[gaintype]*2 < nation.qol:
        qol -= 4
    elif nation.__dict__[gaintype] < nation.qol:
        qol -= 2
    return qol


############
## oil gain
############

def oilgain(nation):
    oil = oilbase(nation)
    oil += oilbonus(nation, oil)
    return oil

#also doubles as reserve loss
def oilbase(nation):
    if nation.oilreserves > nation.wells:
        return nation.wells
    else:
        return nation.oilreserves

def oilbonus(nation, oil):
    oil *= utils.research('oil', nation.researchdata.oiltech)
    return int(round(oil))


###########
## rm gain
###########


def rmgain(nation):
    rm = rmbase(nation)
    rm += rmgain_tech(nation)
    return rm

# I know it's basic but simple editing of the game changes later on
def rmbase(nation):
    return nation.mines

def rmgain_tech(nation):
    return int(round(nation.mines * utils.research('rm', nation.researchdata.miningtech)))


###########
## MG gain
###########


def mggain(nation, rm, oil):
    mg = mgbase(nation, rm, oil)
    mg += mgbonus(nation, mg)
    return mg

def mgdisplaywrapper(nation):
    return mgbase(nation, rmgain(nation) + nation.rm, oilgain(nation) + nation.oil)

def mgbase(nation, rm, oil):
    mg = 0
    if rm >= nation.factories and oil >= nation.factories:
        mg = nation.factories
    else: #if not enough raw materials, pick whatever is the lowest
        if rm <= oil:
            mg = rm
        else:
            mg = oil
    return mg

def mgbonus(nation, mg):
    return int(round(mg * utils.research('mg', nation.researchdata.industrialtech)))


def mgunidecay(nation):
    pass



#############
## Food gain
#############

def faminecheck(nation):
    if nation.food - foodgain(nation) == 0:
        return True
    return False

def foodgain(nation):
    food = foodgain_agricultureideal(nation)
    food -= foodgain_milcost(nation)
    food -= foodgain_civcost(nation)
    if food + nation.food < 0: #famine!
        return nation.food
    return food



def foodgain_agricultureideal(nation):
    for field in v.foodproduction:
        land = field
        gain = v.foodproduction[field]
    return int((nation.farmland() / land) * gain) * nation.researchdata.foodtech

def foodgain_agriculture(nation):
    return int(foodgain_agricultureideal(nation) * (nation.econdata.foodproduction/100.0))

def foodgain_milcost(nation):
    return nation.milfoodconsumption()

def foodgain_civcost(nation):
    return nation.civfoodconsumption()

#############
## Research
#############

def researchgain(nation):
    rs = researchgain_literacy(nation)
    rs += researchgain_unis(nation)
    rs += researchgain_alliance(nation)
    return rs

def researchgain_literacy(nation):
    gain = 0
    if nation.literacy > 9:
        gain = (nation.literacy/10)+1
        gain = (10 if gain == 11 else gain)
    return gain

def researchgain_unis(nation):
    rm = nation.rm + rmgain(nation)
    oil = oilgain(nation) + nation.oil
    mg = nation.mg + mggain(nation, rm, oil)
    if nation.universities > 0:
        cost = nation.universities * v.unicost
        if mg > cost:
            return cost
        return mg * v.researchperuni/2
    return 0

def researchgain_alliance(nation):
    if nation.has_alliance():
        if nation.alliance.initiatives.freedom:
            tot = nation.alliance.members.filter(deleted=False, vacation=False).aggregate(Sum('universities'))['universities__sum']
            return round(tot*(nation.literacy/100.0))
    return 0


############
## Manpower
############

def manpowergain(nation):
    if faminecheck(nation):
        return v.faminecost
    mp = manpowergain_default(nation)
    mp += manpowergain_bonus(nation)
    mp += manpowergain_borders(nation)
    mp += manpowergain_healthcare(nation)
    return mp

def manpowergain_default(nation):
    if nation.manpower <= 10:
        return 1
    elif nation.manpower > 60:
        return 6
    return 4

def manpowergain_bonus(nation):
    if nation.region() == 'Asia':
        return 2
    return 0

def manpowergain_borders(nation):
    if nation.has_alliance():
        if nation.alliance.initiatives.open_borders:
            return 1
    return 0

def manpowergain_healthcare(nation):
    if nation.healthcare < 25:
        return -1
    elif nation.healthcare > 75:
        return 1
    return 0




#decays



def literacydecay(nation):
    lit = 0
    if nation.literacy <= 50:
        lit -= 1
    elif nation.literacy <= 75:
        lit -= 2
    else:
        lit -= 3
    return lit

def healthcaredecay(nation):
    hc = 0
    if nation.healthcare <= 50:
        hc -= 1
    elif nation.healthcare <= 75:
        hc -= 2
    else:
        hc -= 3
    return hc


###########
## FI
###########

def FIchanges(nation):
    FI = 0
    if nation.economy > 33:
        FI = nation.growth
        if nation.economy > 66 and nation.growth > 0:
            FI *= 2
    else:
        if nation.FI > 0:
            g = nation.growth
            if nation.growth < 0:
                g = -g
            FI = int(sqrt(g*1.5))
            FI = (FI if nation.growth >= 0 else int(-FI*1.5))
            if nation.FI < FI:
                FI = -nation.FI
            else:
                FI = -FI
        else:
            FI = nation.growth*2
            if nation.FI < FI:
                FI = -nation.FI
            else:
                FI = -FI
    return FI


############
### Growth
############

def growthchanges(nation):
    if faminecheck(nation):
        return v.faminecost
    growth = 0
    growth += growthrecovery(nation)
    growth += growthchanges_industry(nation)
    growth += growthchanges_stab(nation)
    growth += growthchanges_unsustainable(nation)
    growth += growthchanges_openborders(nation)
    growth += growthchanges_redistribution(nation)
    growth += growthchanges_unis(nation)
    growth += growthchanges_military(nation)
    return growth

def growthrecovery(nation):
    gain = 0
    if nation.gdp < int(nation.maxgdp*0.9):
        gain = int(sqrt(nation.maxgdp - nation.gdp))
    return gain

def growthchanges_stab(nation):
    if nation.stability > 80:
        return 2
    elif nation.stability >= 50 and nation.stability <= 80:
        return 1
    elif nation.stability >= 20 and nation.stability < 50:
        return -1
    else:
        return -2

def growthchanges_unsustainable(nation):
    unsus = 0
    if nation.growth > 20 and nation.gdp > int(nation.maxgdp*0.9):
        unsus =(nation.growth/20-1)**2
        if unsus > nation.growth:
            unsus = int(nation.growth + sqrt(nation.growth))
    return -unsus

#nice and simple
def growthchanges_industry(nation):
    return mgdisplaywrapper(nation)

def growthchanges_unis(nation):
    if nation.mg + mggain(nation, nation.rm, nation.oil) > nation.universities:
        return nation.universities * 2
    return (nation.mg + mggain(nation, nation.rm, nation.oil))*2

def growthchanges_military(nation):
    return nation.military.army/20

def growthchanges_openborders(nation):
    if nation.has_alliance():
        if nation.alliance.initiatives.open_borders:
            return 2
    return 0

def growthchanges_redistribution(nation):
    gain = 0
    if nation.has_alliance():
        avg = nation.alliance.members.filter(deleted=False, vacation=False).aggregate(Sum('gdp'))['gdp__sum']
        if nation.gdp < avg/2:
            gain = 5
        elif nation.gdp < avg:
            gain = 3
        elif nation.gdp/2 > avg:
            gain = -5
        elif nation.gdp > avg:
            gain = -3
    return gain


##############
### rebels ###
##############


def rebelgain(nation):
    rebels = 0
    rebels += rebelgain_stab(nation)
    rebels += rebelgain_appr(nation)
    rebels += rebelgain_qol(nation)
    return rebels

def rebelgain_stab(nation):
    rebels = 0
    if nation.stability > 80:
        rebels -= 2
    elif nation.stability >= 50 and nation.stability <= 80:
        rebels -= 1
    return rebels

def rebelgain_appr(nation):
    return (-1 if nation.approval > 70 else 0)

def rebelgain_qol(nation):
    if nation.qol < 30 and nation.government <= 60:
        return 2
    return 0



###################
#### Spy stuff ####
###################

def spygain(spy):
    gain = 0
    gain += spygain_alignment(spy)
    gain += spygain_subregion(spy)
    gain += spygain_region(spy)
    gain += spygain_home(spy)
    gain += spygain_experience(spy)
    return gain

def spygain_home(spy):
    if spy.location == spy.nation:
        return 5
    return 0

def spygain_alignment(spy):
    if spy.location != spy.nation:
        if spy.location.alignment == 3 and spy.nation.alignment == 1 or \
            spy.location.alignment == 1 and spy.nation.alignment == 3:
            return 1
    return 0

def spygain_subregion(spy):
    if spy.location != spy.nation:
        if spy.location.subregion == spy.location.subregion:
            return 1
    return 0

def spygain_region(spy):
    if spy.location != spy.nation:
        if spy.location.region() == spy.location.region():
            return 1
    return 0

def spygain_experience(spy):
    return spy.experience/25






#############################
## Alliance initiative costs
#############################


def literacycost(alliance):
    if alliance.initiatives.literacy:
        count = alliance.members.filter(vacation=False, deleted=False).count()
        gdp = alliance.members.filter(vacation=False, deleted=False).aggregate(Sum('gdp'))['gdp__sum']
