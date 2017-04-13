from django import template
from django.utils.safestring import mark_safe
from django.db.models import Sum
import nation.variables as v
import nation.utilities as utils
from math import sqrt
import nation.turnchange as changes

register = template.Library()

def vaccheck(f):
    def wrap(nation, *args, **kwargs):
        if nation.vacation:
            return mark_safe('No change')
        return f(nation, *args, **kwargs)
    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap

def qol(qol):
    qol = (qol if qol > 0 else 1)
    qol = (qol/10 if qol % 10 != 0 else (qol/10)-1)
    if qol < 4:
        color = 'red'
    elif qol > 6:
        color = 'green'
    else:
        color= 'white'
    desc = v.qol[qol]
    return mark_safe('<span style="color:%s">%s</span>' % (color, desc))

register.filter('qol', qol)

def approval(appr):
    appr = (appr if appr > 0 else 1)
    appr = int(appr)
    bold = True
    appr = (appr/10 if appr % 10 != 0 else (appr/10)-1)
    if appr < 4:
        color = 'red'
    elif appr > 6:
        color = 'green'
    else:
        color= 'white'
    if bold:
        desc = "<b>%s</b>" % v.approval[appr]
    desc = v.approval[appr]
    return mark_safe('<span style="color:%s">%s</span>' % (color, desc))

register.filter('approval', approval)

def descriptor(gubmint):
    try:
        gubmint = int(gubmint)
    except:
        return mark_safe('<span>%s</span>' % gubmint)
    gubmint = (gubmint if gubmint > 0 else 1)
    gubmint = (gubmint/20 if gubmint % 20 != 0 else (gubmint/20)-1)
    desc = v.descriptor[gubmint]
    return mark_safe('<span>%s</span>' %  desc)

register.filter('descriptor', descriptor)

def title(gubmint):
    try:
        gubmint = int(gubmint)
    except:
        return mark_safe('<span>%s</span>' % gubmint)
    gubmint = (gubmint if gubmint > 0 else 1)
    gubmint = (gubmint/20 if gubmint % 20 != 0 else (gubmint/20)-1)
    desc = v.title[gubmint]
    return mark_safe('<span>%s</span>' % desc)

register.filter('title', title)


def government(gov):
    gov = (gov if gov > 0 else 1)
    gov = (gov/20 if gov % 20 != 0 else (gov/20)-1)
    return mark_safe(v.government[gov])

register.filter('government', government)

def stability(stab):
    bold = False
    stab = (stab if stab > 0 else 1)
    stab = (stab/10 if stab % 10 != 0 else (stab/10)-1)
    if stab < 4:
        color = 'red'
    elif stab > 6:
        color = 'green'
        bold = False
    else:
        color= 'white'
    if bold:
        desc = "<b>%s</b>" % v.stability[stab]
    else:
        desc = v.stability[stab]
    return mark_safe('<span style="color:%s">%s</span>' % (color, desc))

register.filter('stability', stability)

def rebels(rebels):
    rebels = (rebels/4+1 if rebels % 4 != 0 else rebels/4)
    rebels = (rebels if rebels < 4 else 4) #anything at or above 12 is civil war
    color = ('red' if rebels > 8 else 'white')
    return mark_safe('<span style="color:%s">%s</span>' % (color, v.rebels[rebels]))

register.filter('rebels', rebels)


def healthcare(healthcare):
    healthcare = (healthcare if healthcare > 0 else 1)
    healthcare = (healthcare/10 if healthcare % 10 != 0 else (healthcare/10)-1)
    if healthcare < 4:
        color = 'red'
    elif healthcare > 6:
        color = 'green'
    else:
        color= 'white'
    desc = v.healthcare[healthcare]
    return mark_safe('<span style="color:%s">%s</span>' % (color, desc))

register.filter('healthcare', healthcare)

def econsystem(econ):
    if econ < 33:
        econ = 0
    elif econ < 66:
        econ = 1
    else:
        econ = 2
    return mark_safe('<span>%s</span>' % v.economy[econ])

register.filter('econsystem', econsystem)

def growthdisplay(gro):
    color = ('red' if gro < 0 else False)
    if color:
        return mark_safe('<span style="color:red">%s</span>' % gro)
    else:
        return mark_safe('<span>%s</span>' % gro)

register.filter('growthdisplay', growthdisplay)

def relationpoints(points):
    if points >= 0:
        return mark_safe('<span>%s</span>' % points)
    else:
        return mark_safe('<span style="color:red">%s</span>' % points)

register.filter('relationpoints', relationpoints)

def alignment(align):
    return mark_safe(v.alignment[align])

register.filter('alignment', alignment)

def reputation(rep):
    rep = (rep if rep > 0 else 1)
    rep = (rep/10 if rep % 10 != 0 else (rep/10)-1)
    if rep < 3:
        color = 'red'
    elif rep > 7:
        color = 'green'
    else:
        color= 'white'
    desc = v.reputation[rep]
    return mark_safe('<span style="color:%s">%s</span>' % (color, desc))

register.filter('reputation', reputation)

def manpower(mp):
    mp = (mp/20+1 if mp % 20 != 0 else mp/20)
    if mp < 2:
        color = 'red'
    elif mp > 3:
        color = 'green'
    else:
        color = 'white'
    return mark_safe('<span style="color:%s">%s</span>' % (color, v.manpower[mp]))

register.filter('manpower', manpower)

def training(tlevel):
    tlevel = (tlevel if tlevel > 0 else 1)
    tlevel = (tlevel/20 if tlevel % 20 != 0 else tlevel/20-1)
    return mark_safe(v.training[tlevel])

register.filter('training', training)

def chemicalweapons(chem):
    if chem == 10:
        result = "Armed"
    else:
        result = '<div class="progress-bar progress-bar-danger" style="width: %s"></div>' % (chem*10)
    return mark_safe(result)

register.filter('chemicalweapons', chemicalweapons)

def tech(weps):
    if weps >= 2000:
        weps = 2000
    elif weps >= 1000:
        weps = 1000
    elif weps >= 500:
        weps = 500
    elif weps >= 300:
        weps = 300
    elif weps >= 150:
        weps = 150
    elif weps >= 50:
        weps = 50
    elif weps >= 10:
        weps = 10
    else:
        weps = 0

    return mark_safe(v.techlimits[weps])

register.filter('tech', tech)


def airforce(planes):
    return mark_safe(v.airforce[planes])

register.filter('airforce', airforce)


def navy(ships):
    if ships > 70:
        ships = 100
    elif ships > 50:
        ships = 70
    elif ships > 30:
        ships = 50
    elif ships > 10:
        ships = 30
    elif ships > 0:
        ships = 10
    else:
        ships = 0

    return mark_safe(v.navy[ships])

register.filter('navy', navy)

def lastonline(seen):
    delta = v.now() - seen
    toreturn = longtimeformat(delta)

    return mark_safe(toreturn)

register.filter('lastonline', lastonline)

def famine(food):
    if food > 0:
        return mark_safe("%s Tons" % food)
    else:
        return mark_safe('<span style="color: red">FAMINE</span>')

register.filter('famine', famine)

def longtimeformat(delta):
    days = delta.days
    timedeltaseconds = delta.seconds
    hours, remainder = divmod(timedeltaseconds, 3600)
    hours += 24 * days
    minutes, seconds = divmod(remainder, 60)
    if hours == 0:
        if minutes <= 5:
            return '<p style="color: green"><b>Online Now</b></p>'
        return '<p>Last seen: %s minutes ago</p>' % minutes

    else:
        return '<p>Last seen: %s hours ago</p>' % hours

@vaccheck
def oilchange(nation):
    loss = gain = ''
    if nation.factories > 0 and changes.mgdisplaywrapper(nation) > 0:
        loss = '<p><span class="red">-%s<span> mbbls from factories</p>' % changes.mgdisplaywrapper(nation)
    oilgain = changes.oilbase(nation)
    if oilgain > 0:
        gain = '<p><span class="green">+%s<span> mbbls from oil wells</p>' % oilgain
    else:
        gain = ''
    bonus = changes.oilbonus(nation, oilgain)
    if bonus > 0:
        bonus = '<p><span class="green">+%s<span> mbbls from improved technology</p>' % bonus
    else:
        bonus = ''
    if not gain and not loss and not bonus:
        gain = "No change"
    return mark_safe(gain + ' ' + bonus + ' ' + loss)

register.filter('oilchange', oilchange)

@vaccheck
def rmchange(nation):
    loss = gain = bonus = ''
    if changes.mgdisplaywrapper(nation) > 0:
        loss = '<p><span class="red">-%s<span> tons from factories</p>' % changes.mgdisplaywrapper(nation)
    if changes.rmbase(nation) > 0:
        gain = '<p><span class="green">+%s<span> tons from mines</p>' % changes.rmbase(nation)
    bonusgain = changes.rmgain_tech(nation)
    if bonusgain > 0:
        bonus = '<p><span class="green">+%s<span> tons from improved technology</p>' % bonusgain
    if not gain and not loss:
        gain = "No change"
    return mark_safe(gain + ' ' + bonus + ' ' + loss)

register.filter('rmchange', rmchange)

@vaccheck
def mgchange(nation):
    gain = ''
    mg = changes.mgdisplaywrapper(nation)
    if nation.factories > 0:
        if mg > 0:
            gain += '<p><span class="green">+%s tons from factories<span></p>' % mg
        techbonus = changes.mgbonus(nation, mg)
        if techbonus > 0:
            gain += '<p><span class="green">+%s tons from technological improvements<span></p>' % techbonus

    if nation.universities > 0:
        uniloss = changes.mgunidecay(nation)
        if uniloss < 0:
            txt = '%s tons' % uniloss
            uni = '<p><span class="red">%s from universities<span></p>' % txt
            gain += uni

    if not gain:
        gain = "<p>No change</p>"
    return mark_safe(gain)

register.filter('mgchange', mgchange)


def agency(alignment):
    return mark_safe(v.agencies[alignment])

register.filter('agency', agency)

@vaccheck
def researchgain(nation):
    gain = changes.researchgain_literacy(nation)
    if gain > 0:
        lit = "+%s research from literacy" % gain
        lit = '<p><span class="green">%s</span></p>' % lit
    else:
        lit = ""
    rgain = changes.researchgain_unis(nation)
    if rgain > 0:
        uni = "+%s research from universities" % rgain
        uni = '<p><span class="green">%s</span></p>' % uni
    else:
        uni = ""

    again = changes.researchgain_alliance(nation)
    if again > 0:
        foi = "+%s from freedom of information initiative" % int(again)
        foi = '<p><span class="green">%s</span></p>' % foi
    else:
        foi = ""


    return mark_safe(lit+uni+foi)

register.filter('researchgain', researchgain)

def qolchange(nation, gaintype):
    if nation.vacation:
        return mark_safe('No change')
    gain = changes.qolgain_template(nation, gaintype)
    gain = inttostr(gain)
    if not gain:
        return mark_safe('<p>No change from %s</p>' % gaintype)
    color = ('green' if gain[0] == '+' else 'red')
    adj = ('high' if gain[0] == '+' else 'low')
    txt = "%s%% from %s %s" % (gain, adj, gaintype)
    lit = '<p><span class="%s">%s</span></p>' % (color, txt)
    return mark_safe(lit)


register.filter('qolchange', qolchange)


def inttostr(var):
    if var > 0:
        var = '+%s' % var
    elif var < 0:
        var = str(var)
    else:
        var = False
    return var

#growth change text
#factories -> unis -> stability -> open boarders
#clusterfuck of a function
@vaccheck
def growthchange(nation):
    if changes.faminecheck(nation):
        ret = '<p><span class="red">$%s million from famine!</span></p>' % v.faminecost
    else:
        fac = uni = stab = ob = mil = redis = rec = unsust = ''
        faccount = changes.growthchanges_industry(nation)
        if faccount > 0:
            fac = '+%s million from industry' % faccount
            fac = '<p><span class="green">%s</span></p>' % fac

        unic = changes.growthchanges_unis(nation)
        if unic > 0:
            txt = '+%s million from universities' % unic
            uni = '<p><span class="green">%s</span></p>' % txt


        gain = inttostr(changes.growthchanges_stab(nation))
        if gain:
            color = ('green' if gain[0] == '+' else 'red')
            txt = '%s million from stability' % gain
            stab = '<p><span class="%s">%s</span></p>' % (color, txt)


        obgain = changes.growthchanges_openborders(nation)
        if obgain > 0:
            ob = '<p><span class="green">+2 million due to open borders within your alliance</span></p>'



        if changes.growthchanges_military(nation):
            txt = "-%s million from military upkeep" % changes.growthchanges_military(nation)
            mil = '<p><span class="red">%s</span></p>' % txt

        redisgain = changes.growthchanges_redistribution(nation)
        if redisgain:
            redisgain = inttostr(redisgain)
            txt = "%s million due to redistribution of wealth policy in your alliance" % redisgain
            color = ('green' if redisgain[0] == '+' else 'red')
            redis = '<p><span class="%s">%s</span></p>' % (color, txt)


        if changes.growthchanges_unsustainable(nation) < 0:
            txt = "%s million from unsustainable growth" % changes.growthchanges_unsustainable(nation)
            unsust = '<p><span class="red">%s</span></p>' % txt

        ret = fac + uni + stab + ob + mil + redis + rec + unsust
        if ret == '':
            return mark_safe('<p>No change</p>')
    return mark_safe(ret)

register.filter('growthchange', growthchange)


def landuse(nation):
    km = " km<sup>2</sup>"
    land = nation.land
    txt = ''
    for field in v.landorder:
        landcost = nation.landcost(field)
        landcost = nation.__dict__[field] * landcost
        if landcost > 0:
            txt += '<p>%s %s %s (%s %s per %s)</p>' % (landcost, km, v.landflavor[field], nation.landcost(field), km, v.landsimple[field])
            land -= landcost
    txt += '<p>%s %s %s (500 %s per farmplot)</p>' % (land, km, v.landflavor['farmland'], km)
    return mark_safe(txt)


register.filter('landuse', landuse)

@vaccheck
def stabilitychange(nation):
    if changes.faminecheck(nation):
        tot = '<p><span class="red">%s%% from famine!</span></p>' % v.faminecost
    else:
        appr = demappr = qol = borders = rebs = coll = ''
        gain = False
        gain = inttostr(changes.stabilitygain_democracy(nation)) 
        if gain:
            color = ('green' if gain[0] == '+' else 'red')
            adj = ('high' if gain[0] == '+' else 'low')
            txt = "%s%% stability from %s approval in a democracy" % (gain, adj)
            demappr = '<p><span class="%s">%s</span></p>' % (color, txt)
            gain = False

        if changes.stabilitygain_growthloss(nation):
            txt = "%s stability due to economic collapse" % inttostr(changes.stabilitygain_growthloss(nation))
            coll = '<p><span class="red">%s</span></p>' % txt

        appr = stability_alt(nation, 'approval', 'approval')
        qol = stability_alt(nation, 'qol', 'quality of life')
        
        opbo = changes.stabilitygain_openborders(nation)
        if opbo:
            txt = '%s stability due to open borders within your alliance' % opbo
            borders = '<p><span class="red">%s</span></p>' % txt


        rebeloss = changes.stabilitygain_rebels(nation)
        if rebeloss:
            txt = "%s stability due to rebels" % rebeloss
            rebs = '<p><span class="red">%s</span></p>' % txt
            gain = False

        tot = appr + demappr + qol + borders + rebs + coll
        if tot == '':
            return mark_safe('<p>No change</p>')
    return mark_safe(tot)

register.filter('stabilitychange', stabilitychange)

def stability_alt(nation, attr, flavor):
    txt = ''
    gain = inttostr(changes.stabilitygain_modifiers(nation, attr))
    if gain:
        color = ('green' if gain[0] == '+' else 'red')
        adj = ('high' if gain[0] == '+' else 'low')
        txt = "%s%% stability due to %s %s" % (gain, adj, flavor)
        txt = '<p><span class="%s">%s</span></p>' % (color, txt)
    return txt

@vaccheck
def rep_relation(nation):
    txt = ''
    gain = inttostr(changes.repgain(nation))
    if gain:
        color = ('green' if gain[0] == '+' else 'red')
        adj = ('high' if gain[0] == '+' else 'low')
        txt = "%s  due to %s reputation" % (gain, adj)
        txt = '<p><span class="%s">%s</span></p>' % (color, txt)
    return txt

@vaccheck
def soviet_relations(nation):
    align = alliance_align = econ = rep = ''

    aligngain = inttostr(changes.sovietgain_alignment(nation))
    if aligngain:
        txt = "%s due to official alignment" % aligngain
        if aligngain[0] == '+':
            align = '<p><span class="green">%s</span></p>' % txt
        else:
            align = '<p><span class="red">%s</span></p>' % txt

    try:
        if nation.alliance.initiatives.alignment == 'Soviet Union':
            txt = "+1 due to your alliances alignment with the Soviet Union"
            alliance_align = '<p><span class="green">%s</span></p>' % txt
        elif nation.alliance.initiatives.alignment == 'United States':
            txt = "-1 due to your alliances alignment with the United States"
            alliance_align = '<p><span class="red">%s</span></p>' % txt
    except:
        pass

    econgain = changes.sovietgain_econ(nation)
    if econgain:
        if econgain < 0:
            txt = "%s due to capitalist economy" % (inttostr(econgain))
            econ = '<p><span class="red">%s</span></p>' % txt
        else: 
            txt = "%s due to communist economy" % (inttostr(econgain))
            econ = '<p><span class="green">%s</span></p>' % txt


    rep = rep_relation(nation)

    tot = align + econ + alliance_align + rep
    if tot == '':
        return mark_safe('<p>No change</p>')
    return mark_safe(tot)

register.filter('soviet_relations', soviet_relations)


@vaccheck
def us_relations(nation):
    align = alliance_align = econ = rep = ''
    
    aligngain = inttostr(changes.westerngain_alignment(nation))
    if aligngain:
        txt = "%s due to official alignment" % aligngain
        if aligngain[0] == '+':
            align = '<p><span class="green">%s</span></p>' % txt
        else:
            align = '<p><span class="red">%s</span></p>' % txt

    try:
        if nation.alliance.initiatives.alignment == 'Soviet Union':
            txt = "-1 due to your alliance's alignment with the Soviet Union"
            alliance_align = '<p><span class="red">%s</span></p>' % txt
        elif nation.alliance.initiatives.alignment == 'United States':
            txt = "+1 due to your alliance's alignment with the United States"
            alliance_align = '<p><span class="green">%s</span></p>' % txt
    except:
        pass

    #economy

    econgain = changes.westerngain_econ(nation)
    if econgain:
        if econgain > 0:
            txt = "%s due to capitalist economy" % (inttostr(econgain))
            econ = '<p><span class="green">%s</span></p>' % txt
        else: 
            txt = "%s due to communist economy" % (inttostr(econgain))
            econ = '<p><span class="red">%s</span></p>' % txt

    #reputation

    rep = rep_relation(nation)

    tot = align + econ + alliance_align + rep
    if tot == '':
        return mark_safe('<p>No change</p>')
    return mark_safe(tot)

register.filter('us_relations', us_relations)

@vaccheck
def manpowerchanges(nation):
    txt = ''
    if changes.faminecheck(nation):
        txt = '<p style="color: red">%sk men from the famine!</p>' % v.faminecost
    else:
        basemp = changes.manpowergain_default(nation)
        txt = '<p style="color: green">+%sk men from population growth</p>' % basemp
        asiamp = changes.manpowergain_bonus(nation)
        if asiamp:
            txt += '<p style="color: green">+%sk men from Asian population</p>' % asiamp
        borders = changes.manpowergain_borders(nation)
        if borders:
            txt += '<p style="color: green">+%sk men from open borders</p>' % borders
        hc = changes.manpowergain_healthcare(nation)
        if hc:
            if hc > 0:
                txt += '<p style="color: green">+%sk men from great healthcare</p>' % hc
            else:
                txt += '<p style="color: red">%sk men from bad healthcare</p>' % hc
        if txt == '':
            return mark_safe('<p>No change</p>')

    return mark_safe(txt)

register.filter('manpowerchanges', manpowerchanges)


def warstatus(target, nation):
    from nation.utilities import can_attack
    result, reason = can_attack(nation, target)
    if result:
        result = '<span style="color: green">Yes</span>'
    else:
        result = '<span style="color: red">No</span>'
    txt = '<a title="%s" href="#"><b>%s</b></a>' % (reason, result)

    return mark_safe(txt)

register.filter('warstatus', warstatus)


def commlabels(comm):
    txt = ''
    prefix = []
    for field in list(comm._meta.fields)[4:]:
        if v.commprefix.has_key(field.name):
            if comm.__dict__[field.name]:
                txt += '<span class="badge" id="newbadge">%s</span>' % v.commprefix[field.name]
    return mark_safe(txt)


register.filter('commlabels', commlabels)

@vaccheck
def foodchanges(nation):
    foodgain = changes.foodgain_agriculture(nation)
    txt = '<p><span style="color: green;">+%s Tons from agriculture (%s%% output)</span></p>' % (foodgain, nation.econdata.foodproduction)
    if changes.foodgain_milcost(nation) > 0:
        txt += '<p><span style="color: red;">-%s Tons from military consumption</span></p>' % changes.foodgain_milcost(nation)
    if changes.foodgain_civcost(nation) > 0:
        txt += '<p><span style="color: red;">-%s Tons from civilian consumption</span></p>' % changes.foodgain_civcost(nation)
    population_feed = nation
    return mark_safe(txt)

register.filter('foodchanges', foodchanges)

@vaccheck
def FIchanges(nation):
    txt = "No change"
    gain = changes.FIchanges(nation)
    if gain > 0:
        txt = '<span style="color: green;">+$%sk from growth!</span>' % gain
    elif gain < 0:
        txt = '<span style="color: red;">-$%sk from growth!</span>' % inttostr(gain)
    return mark_safe('<p>%s</p>' % txt)

register.filter('FIchanges', FIchanges)