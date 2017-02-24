from .models import *
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
import utilities as utils
from decorators import nation_required, novacation
import variables as v
import random


@nation_required
@login_required
@novacation
def militarypolicies(request):
    context = {}
    img = ''
    result = False
    nation = Nation.objects.select_related('military').get(user=request.user) #1 instead of 2
    mildata = nation.military
    trainingcost = (mildata.army**2/100)*(mildata.training**2/50)
    trainingcost = (trainingcost if mildata.army < trainingcost else mildata.army)
    if request.method == 'POST':
        actions = {}
        img = "/static/img/"

        if 'train' in request.POST:
            if nation.budget < trainingcost:
                result = "You do not have enough money!"
            elif mildata.training >= 100:
                result = "Your men are the elite of the elite, there is no need to train them further!"
            else:
                actions.update({'budget': {'action': 'subtract', 'amount': trainingcost}})
                mildata.training += utils.attrchange(mildata.training, 5)
                mildata.save(update_fields=['training'])
                img += "train.jpg"
                result = "Your men are drilled in the latest bayoneting techniques. 10,000 straw dummies sacrifice their lives for the cause."

        elif 'conscript' in request.POST:
            if nation.growth <= -2:
                result = "Your economy cannot support further conscription!"
            elif nation.manpower == 0:
                result = "All of the available manpower has already been thrown into the meatgrinder!"
            else:
                actions.update({
                    'growth': {'action': 'subtract', 'amount': 1},
                    'manpower': {'action': 'add', 'amount': utils.attrchange(nation.manpower, -4)}
                    })
                milactions = {
                    'training': {'action': 'add', 'amount': utils.attrchange(mildata.training, -(200/mildata.army))},
                    'army': {'action': 'add', 'amount': 2},
                    }
                utils.atomic_transaction(Military, mildata.pk, milactions)
                img = ""
                result = "You conscript thousands of young men into your army."

        elif 'demobilize' in request.POST:
            if mildata.army < 5:
                result = "Your forces are fully demobilized!"
            else:
                if random.randint(1, 10) > 5:
                    actions.update({'growth': {'action': 'add', 'amount': 1}})
                    result = "Your soldiers lay down their rifles and pick up the hammer, boosting the economy."
                else:
                    result = "Your soldiers lay down their rifles and pick up the bottle, with no affect on your economy."
                img = ""
                actions.update({'manpower': {'action': 'add', 'amount': utils.attrchange(nation.manpower, 3)}})
                milactions = {'army': {'action': 'subtract', 'amount': 2}}
                utils.atomic_transaction(Military, mildata.pk, milactions)

        elif 'attackrebels' in request.POST:
            if nation.budget < 10:
                result = "You do not have enough money!"
            elif nation.rebels == 0:
                result = "There are no rebels to attack!"
            elif mildata.army == 0:
                result = "You do not have an army to attack with!"
            else:
                actions.update({'budget': {'action': 'subtract', 'amount': 10}})
                chance = random.randint(1, 10)
                if chance > 5:
                    actions.update({'rebels': {'action': 'subtract', 'amount': 1}})
                    mildata.army -= 1
                    result = "Your forces suffer casualties but they manage to weaken the rebels."
                elif chance < 2:
                    mildata.army -= 1
                    actions.update({'rebels': {'action': 'add', 'amount': 1}})
                    result = "Your army is defeated and takes casualties! The rebels make significant gains from their victory and grow in size."
                else:
                    actions.update({'rebels': {'action': 'subtract', 'amount': 1}})
                    result = "Your forces are victorious against the rebels."
                img = ""
                mildata.save(update_fields=['army'])

        elif 'gasrebels' in request.POST:
            if mildata.chems <= 9:
                result = "You do not have chemical weapons!"
            elif nation.rebels == 0:
                result = "There are no rebels to gas!"
            else:
                kills = (nation.rebels*0.25 if nation.rebels*0.25 > 2 else 2)
                actions.update({
                    'rebels': {'action': 'add', 'amount': utils.attrchange(nation.rebels, -kills)},
                    'reputation': {'action': 'add', 'amount': utils.attrchange(nation.reputation, -25)},
                    })
                img = ""
                result = "Your attacks decimate the rebels, forcing what few remain into hiding. However photographs of \
                civilian casualties soon circulate through international media, and foreigners declare you to be a 'monster'."

        elif 'migs' in request.POST:
            cost = 11 + ((mildata.planes**2)-10)
            oilcost = mildata.planes + 5
            if nation.oil < oilcost:
                result = "You do not have enough oil!"
            elif nation.soviet_points < cost:
                result = "You do not have a good enough relationship with the Soviets!"
            elif mildata.planes == 10:
                result = "Your airforce is already at full strength!"
            else:
                mildata.planes += 1
                mildata.save(update_fields=['planes'])
                actions.update({
                    'soviet_points': {'action': 'subtract', 'amount': cost},
                    'oil': {'action': 'subtract', 'amount': oilcost},
                    })
                img = ""
                result = "Several MiGs are flown in from Moscow!"

        elif 'manufactureaircraft' in request.POST:
            cost = 11 + ((mildata.planes**2)/2)
            oilcost = mildata.planes + 5
            if nation.oil < oilcost:
                result = "You do not have enough oil!"
            elif nation.mg < cost:
                result = "You do not have enough manufactured goods!"
            elif mildata.planes == 10:
                result = "Your airforce is already at full strength!"
            elif nation.factories < 2:
                result = "You do not have the capacity to manufacture these! Build more weapons factories!"
            else:
                mildata.planes += 1
                mildata.save(update_fields=['planes'])
                actions.update({
                    'mg': {'action': 'subtract', 'amount': cost},
                    'oil': {'action': 'subtract', 'amount': oilcost},
                    })
                img = ""
                result = "Several cropdusters are rigged with machine guns!"

        elif 'f8' in request.POST:
            cost = 11 + ((mildata.planes**2)-10)
            oilcost = mildata.planes + 5
            if nation.oil < oilcost:
                result = "You do not have enough oil!"
            elif nation.us_points < cost:
                result = "You do not have a good enough relationship with the USA!"
            elif mildata.planes == 10:
                result = "Your airforce is already at full strength!"
            else:
                mildata.planes += 1
                mildata.save(update_fields=['planes'])
                actions.update({
                    'us_points': {'action': 'subtract', 'amount': cost},
                    'oil': {'action': 'subtract', 'amount': oilcost},
                    })
                img = ""
                result = "The finest of American death machines are flown in from Nevada!"

        elif 'chem' in request.POST:
            if nation.budget < 500:
                result = "You do not have enough money!"
            elif mildata.chems >= 10:
                result = "You already have chemical weapons!"
            elif nation.reputation < 10:
                result = "Your reputation is too low, the necessary chemicals have been barred from importation!"
            elif nation.research < 5:
                result = "You do not have enough research!"
            else:
                chance = random.randint(1,10)
                actions.update({
                    'budget': {'action': 'subtract', 'amount': 500},
                    'reputation': {'action': 'add', 'amount': utils.attrchange(nation.reputation, -10)},
                    'research': {'action': 'subtract', 'amount': 5},
                    })
                if chance > 4:
                    mildata.chems += 2
                    if mildata.chems > 10:
                        mildata.chems = 10
                    result = "Progress continues toward usable chemical weapons!"
                elif chance < 2:
                    mildata.chems -= 1
                    result = "A stealth bomber has struck your chemical plant in the middle of production! Someone doesn't want you getting chemical weapons... Progress is set back."
                else:
                    result = "Your chemists unfortunately fail to make progress..."
                img = ""
                mildata.save(update_fields=['chems'])

        elif 'reactor' in request.POST:
            if nation.budget < 5000:
                result = "You do not have enough money!"
            elif mildata.reactor >= 20:
                result = "You already have a reactor!"
            elif nation.uranium == 0:
                result = "You do not have the necessary uranium!"
            else:
                chance = random.randint(1, 10)
                actions.update(
                    {
                    'budget': {'action': 'subtract', 'amount': 5000},
                    'uranium': {'action': 'subtract', 'amount': 1},
                    })
                img = ""
                if chance > 4:
                    mildata.reactor += 1
                    result = "Progress continues toward a working reactor!"
                elif chance < 2:
                    mildata.reactor -= 1
                    result = "A stealth bomber has struck your reactor in the middle of construction! Someone doesn't want you getting nuclear weapons... Progress is set back."
                else:
                    result = "Your nuclear scientists unfortunately fail to make progress..."

        elif 'nuke' in request.POST:
            if nation.budget < 100000:
                result = "You do not have enough money!"
            elif nation.uranium < 20:
                result = "You do not have enough uranium!"
            elif mildata.reactor < 20:
                result = "You do not have a nuclear reactor!"
            else:
                actions.update(
                    {
                    'budget': {'action': 'subtract', 'amount': 100000},
                    'uranium': {'action': 'subtract', 'amount': 20},
                    })
                img = "http://i.imgur.com/wLtwYXi.jpg"
                result = 'You have a nuke.'

        elif 'aks' in request.POST:
            if nation.soviet_points < 5:
                result = "You do not have close enough relations with the Soviets!"
            elif mildata.weapons > 500:
                result = "You have better equipment! These are worthless!"
            else:
                actions.update({'soviet_points': {'action': 'subtract', 'amount': 5}})
                mildata.weapons += 2
                mildata.save(update_fields=['weapons'])
                img = ""
                result = "Thousands of AKMs are airlifted straight to you from Moscow."

        elif 'm14' in request.POST:
            if nation.us_points < 5:
                result = "You do not have close enough relations with the US!"
            elif mildata.weapons > 500:
                result = "You have better equipment! These are worthless!"
            else:
                actions.update({'us_points': {'action': 'subtract', 'amount': 5}})
                mildata.weapons += 2
                mildata.save(update_fields=['weapons'])
                img = ""
                result = "Thousands of FALs are airlifted straight to you from a Nevada warehouse."

        elif 'presidente' in request.POST:
            chance = random.randint(1,3)
            if nation.mg < 5:
                result = "You do not have enough manufactured goods!"
            elif mildata.weapons > 500:
                result = "You have better equipment! These are worthless!"
            elif nation.factories < 2:
                result = "You do not have the capacity to manufacture these! Build more weapons factories!"
            else:
                actions.update({'mg': {'action': 'subtract', 'amount': 5}})
                mildata.weapons += chance
                mildata.save(update_fields=['weapons'])
                img = ""
                result = "Your workers proudly stamp your face on each and every rifle."

        elif 't62' in request.POST:
            cost = 13
            oilcost = 3
            if nation.soviet_points < cost:
                result = "You do not have enough soviet relations!"
            elif nation.oil < oilcost:
                result = "You do not have enough oil!"
            elif mildata.weapons <= 500 and mildata.weapons > 2000:
                result = "You have better equipment! These are worthless"
            else:
                actions.update({
                    'soviet_points': {'action': 'subtract', 'amount': cost},
                    'oil': {'action': 'subtract', 'amount': oilcost},
                    })
                mildata.weapons += 6
                mildata.save(update_fields=['weapons'])
                img = ""
                result = "A couple T-62s arrive on the latest freighter from Odessa"

        elif 'm60' in request.POST:
            cost = 13
            oilcost = 3
            if nation.us_points < cost:
                result = "You do not have enough You do not have enough relationship points with the United States!"
            elif nation.oil < oilcost:
                result = "You do not have enough oil!"
            elif mildata.weapons <= 500 and mildata.weapons > 2000:
                result = "You have better equipment! These are worthless"
            else:
                actions.update({
                    'us_points': {'action': 'subtract', 'amount': cost},
                    'oil': {'action': 'subtract', 'amount': oilcost},
                    })
                mildata.weapons += 6
                mildata.save(update_fields=['weapons'])
                img = ""
                result = "A couple of Pattons arrive on the latest freighter from LA."


        elif 'istan' in request.POST:
            chance = random.randint(5, 8)
            oilcost = 5
            if nation.mg < 13:
                result = "You do not have enough manufactured goods!"
            elif mildata.weapons <= 500 and mildata.weapons > 2000:
                result = "You have better equipment! These are worthless!"
            elif nation.factories < 4:
                result = "You do not have the capacity to manufacture these! Build more weapons factories!"
            elif nation.oil < oilcost:
                result = "You do not have enough oil!"
            else:
                actions.update({
                    'mg': {'action': 'subtract', 'amount': 13},
                    'oil': {'action': 'subtract', 'amount': oilcost}})
                mildata.weapons += chance
                mildata.save(update_fields=['weapons'])
                img = ""
                result = "Your workers proudly stamp your face on each and every tank."

        elif 't90' in request.POST:
            cost = 20
            oilcost = 10
            if nation.soviet_points < cost:
                result = "You do not have enough relationship points with the Soviet Union!"
            elif nation.oil < oilcost:
                result = "You do not have enough oil!"
            elif mildata.weapons < 2000:
                result = "You have better equipment! These are worthless"
            else:
                actions.update({
                    'soviet_points': {'action': 'subtract', 'amount': cost},
                    'oil': {'action': 'subtract', 'amount': oilcost},
                    })
                mildata.weapons += 11
                mildata.save(update_fields=['weapons'])
                img = ""
                result = "A couple T-90s arrive on the latest freighter from Odessa"

        elif 'm1' in request.POST:
            cost = 20
            oilcost = 10
            if nation.us_points < cost:
                result = "You do not have enough relationship points with the United States!"
            elif nation.oil < oilcost:
                result = "You do not have enough oil!"
            elif mildata.weapons < 2000:
                result = "You have better equipment! These are worthless"
            else:
                actions.update({
                    'us_points': {'action': 'subtract', 'amount': cost},
                    'oil': {'action': 'subtract', 'amount': oilcost},
                    })
                mildata.weapons += 11
                mildata.save(update_fields=['weapons'])
                img = ""
                result = "A couple of Pattons arrive on the latest freighter from LA."

        elif 'despot' in request.POST:
            chance = random.randint(7, 14)
            oilcost = 13
            if nation.mg < 18:
                result = "You do not have enough manufactured goods!"
            elif mildata.weapons <= 500 and mildata.weapons > 2000:
                result = "You have better equipment! These are worthless!"
            elif nation.factories < 8:
                result = "You do not have the capacity to manufacture these! Build more factories!"
            elif nation.oil < oilcost:
                result = "You do not have enough oil!"
            else:
                actions.update({
                    'mg': {'action': 'subtract', 'amount': 18},
                    'oil': {'action': 'subtract', 'amount': oilcost}
                    })
                mildata.weapons += chance
                mildata.save(update_fields=['weapons'])
                img = ""
                result = "Your workers proudly stamp your face on each and every tank."

        elif 'manufacturenavy' in request.POST:
            cost = 10+mildata.navy
            oilcost = 10+mildata.navy/2
            if nation.oil < oilcost:
                result = "You do not have enough oil!"
            elif nation.mg < cost:
                result = "You do not have enough manufactured goods!"
            elif nation.factories < 2:
                result = "You do not have the capacity to manufacture these! Build more factories!"
            elif mildata.navy == 100:
                result = "Your navy is at full strength!"
            else:
                actions.update({
                    'mg': {'action': 'subtract', 'amount': cost},
                    'oil': {'action': 'subtract', 'amount': oilcost}
                    })
                mildata.navy += 1
                mildata.save(update_fields=['navy'])
                img += "newship.jpg"
                result = 'A brand new ship is launched from the shipyards!'
        if actions:
            utils.atomic_transaction(Nation, nation.pk, actions)
            nation.policylogging(request.POST, actions)
            nation.refresh_from_db()
            context.update({'img': img})
    if result:
        context.update({'result': result})
    context.update({
            'trainingcost': (mildata.army**2/100)*(mildata.training**2/50),
            'migcost': {'oil': mildata.planes + 5, 'points': 11 + ((mildata.planes**2)-10)},
            'planecost': {'mg': 11 + ((mildata.planes**2)/2), 'oil': mildata.planes + 5},
            'shipcost': {'mg': 10+mildata.navy, 'oil': 10+mildata.navy/2},  
        })

    return render(request, 'nation/military.html', context)


@nation_required
@login_required
@novacation
def foreignpolicies(request):
    nation = Nation.objects.select_related('military').get(user=request.user) #1 instead of 2
    mildata = nation.military
    context = {}
    img = ''
    result = False
    if request.method == "POST":
        actions = {}
        img = "/static/img/"
        if 'praise_ussr' in request.POST:
            cost = 50
            if nation.budget < cost:
                result = "You do not have enough money!"
            elif nation.alignment == 1:
                result = "You are already aligned with the Soviet Union!"
            else:
                stabchange = utils.attrchange(nation.stability, -5)
                actions.update({
                    'budget': {'action': 'subtract', 'amount': cost},
                    'alignment': {'action': 'set', 'amount': 1},
                    'stability': {'action': 'add', 'amount': stabchange}
                    })
                img += "soviets.jpg"
                result = "You praise the glorious advances of the Soviet Union. They like that."


        elif 'praise_us' in request.POST:
            cost = 50
            if nation.budget < cost:
                result = "You do not have enough money!"
            elif nation.alignment == 3:
                result = "You are already aligned with the United States!"
            else:
                stabchange = utils.attrchange(nation.stability, -5)
                actions.update({
                    'budget': {'action': 'subtract', 'amount': cost},
                    'alignment': {'action': 'set', 'amount': 3},
                    'stability': {'action': 'add', 'amount': stabchange}
                    })
                img += "usa.jpg"
                result = "You praise the glorious success of American freedom. They like that."

        elif 'declareneutrality' in request.POST:
            cost = 50
            if nation.budget < cost:
                result = "You do not have enough money!"
            elif nation.alignment == 2:
                result = "You are already a neutral actor on the world stage!"
            else:
                stabchange = utils.attrchange(nation.stability, -5)
                actions.update({
                    'budget': {'action': 'subtract', 'amount': cost},
                    'alignment': {'action': 'set', 'amount': 2},
                    'stability': {'action': 'add', 'amount': stabchange}
                    })
                img += "neutrality.jpg"
                result = "You praise the beautiful freedom and independence of your people. They like that."

        elif 'sovietintervention' in request.POST:
            cost = 35
            if nation.soviet_points < cost:
                result = "You do not have high enough relations with the Soviets!"
            else:
                actions.update({'soviet_points': {'action': 'subtract', 'amount': cost}})
                mildata.army += 10
                mildata.save(update_fields=['army'])
                img += "sovietintervention.jpg"
                result = "10k Soviet troops arrive to liberate us from the capitalist oppressors"

        elif 'sovietaid' in request.POST:
            cost = 10
            if nation.soviet_points < cost:
                result = "You do not have high enough relations with the Soviets!"
            else:
                actions.update({
                    'soviet_points': {'action': 'subtract', 'amount': cost},
                    'growth': {'action': 'add', 'amount': 2},
                    })
                img += "sovietaid.jpg"
                result = "Growth increases as the our Soviet comrades shower us with the glorious benefits of socialism."

        elif 'usintervention' in request.POST:
            cost = (25 if nation.region() == 'Latin America' else 35)
            if nation.us_points < cost:
                result = "You do not have high enough relations with the USA!"
            else:
                actions.update({'us_points': {'action': 'subtract', 'amount': cost}})
                mildata.army += 10
                mildata.save(update_fields=['army'])
                img += "usintervention.jpg"
                result = "10k Americans troops arrive to spread freedom and blow stuff up."

        elif 'usaid' in request.POST:
            cost = 10
            if nation.us_points < cost:
                result = "You do not have high enough relations with the USA!"
            else:
                actions.update({
                    'us_points': {'action': 'subtract', 'amount': cost},
                    'growth': {'action': 'add', 'amount': 2},
                    })
                img += "usaid.jpg"
                result = "Growth increases as Americans give us free stuff in the name of freedom because freedom isn't free or something."

        if actions:
            utils.atomic_transaction(Nation, nation.pk, actions)
            nation.policylogging(request.POST, actions)
            nation.refresh_from_db()
            context.update({'img': img})

    if result:
        context.update({'result': result})
    context.update({'intervention': (25 if nation.region() == 'Latin America' else 35)})
    return render(request, 'nation/foreign.html', context)



def domesticpolicycosts(nation, initiatives):
    data =  {
        'housing': nation.gdp/2,
        'wage': int((nation.gdp*1.05)/400),
        'school': {'rm':  nation.literacy/8 + (nation.gdp/150) / (nation.universities+1), 'money': int((nation.gdp/1.5)/(nation.universities+1))},
        'hospital': {'rm': nation.qol/6 + nation.gdp/150, 'money': nation.gdp/2},
        'medical': {'research': nation.healthcare/10, 'money': nation.gdp/2},
        'food': ((nation.qol/10)*(nation.approval/10)*(nation.gdp/200)/4),
    }
    total = nation.factories + nation.universities
    if nation.region() != "Asia":
        data.update({'university': {
            'rm': total*100+50,
            'oil': total*50+25,
            'mg': total*2,
            }})
    else:
        data.update({'university': {
            'rm': total*75+38,
            'oil': total*38+19,
            'mg': int(total*2*0.75),
            }})
    if initiatives:
        if initiatives.literacy:
            for field in data['school']:
                data['school'][field] /= 2
        if initiatives.healthcare:
            for field in data['hospital']:
                data['hospital'][field] /= 2
            for field in data['medical']:
                data['medical'][field] /= 2
    return data



@nation_required
@login_required
@novacation
def domesticpolicies(request):
    context = {}
    img = ''
    result = False
    nation = Nation.objects.select_related('military', 'researchdata', 'alliance__initiatives').get(user=request.user) #1 instead of 2
    mildata = nation.military
    research = nation.researchdata
    try:
        initiatives = nation.alliance.initiatives
    except:
        initiatives = False
    if request.method == 'POST':
        actions = {}
        costs = domesticpolicycosts(nation, initiatives)
        img = "/static/img/"
        if 'arrest' in request.POST:
            cost = 50
            if nation.budget < 50:
                result = "You do not have enough money!"
            elif nation.government == 0:
                result = "All dissidents are already in prison!"
            else:
                chance = random.randint(1, 10)
                gov = utils.attrchange(nation.government, -6)
                stab = utils.attrchange(nation.stability, 3)
                if nation.government <= 6:
                    result = "All dissidents are in jail already!"
                elif chance > 5 and nation.rebels > 0:
                    actions.update({
                        'budget': {'action': 'subtract', 'amount': cost},
                        'government': {'action': 'add', 'amount': gov},
                        'stability': {'action': 'add', 'amount': stab},
                        'rebels': {'action': 'subtract', 'amount': 1},
                        })
                    img += "arrest.jpg"
                    result = "You arrest the opposition. Turns out some of them were working with the rebels! Rebel strength decreases."
                else:
                    actions.update({
                        'budget': {'action': 'subtract', 'amount': cost},
                        'government': {'action': 'add', 'amount': gov},
                        'stability': {'action': 'add', 'amount': stab},
                        })
                    img += "arrest.jpg"
                    result = "You arrest the opposition. Unfortunately none of them seemed to be working with the rebels..."

        elif 'release' in request.POST:
            cost = 50
            if nation.budget < cost:
                result = "You do not have enough money!"
            elif nation.government == 100:
                result = "There are no political prisoners to release!"
            else:
                chance = random.randint(1, 10)
                gov = utils.attrchange(nation.government, 6)
                stab = utils.attrchange(nation.stability, -4)
                actions.update({
                    'budget': {'action': 'subtract', 'amount': cost},
                    'government': {'action': 'add', 'amount': gov},
                    'stability': {'action': 'add', 'amount': stab},
                        })
                img = ''
                if chance > 6:
                    actions.update({'rebels': {'action': 'add', 'amount': 1}})
                    result = "You release the prisoners, but some of them go on to join the rebels!"
                else:
                    result = "You release the prisoners and everything seems a bit freer."

        elif 'martial' in request.POST:
            cost = 100
            if nation.budget < cost:
                result = "You do not have enough money!"
            elif nation.government <= 20:
                result = "You are already in a state of martial law!"
            elif nation.manpower < 10:
                result = "All available bodies are already at the frontlines!"
            else:
                gov = utils.attrchange(nation.government, -50)
                rep = utils.attrchange(nation.reputation, -2)
                mp = utils.attrchange(nation.manpower, -10)
                stab = utils.attrchange(nation.stability, -5)
                actions.update({
                    'budget': {'action': 'subtract', 'amount': cost},
                    'government': {'action': 'add', 'amount': gov},
                    'reputation': {'action': 'add', 'amount': rep},
                    'manpower': {'action': 'add', 'amount': mp},
                    'stability': {'action': 'add', 'amount': stab},
                    })
                mildata.army += 5
                mildata.training = mildata.training-(200/mildata.army)
                mildata.save(update_fields=['army', 'training'])
                img += "martial.jpg"
                result = 'Your soldiers march down the street, conscripting men on the spot and arresting all dissenters.'

        elif 'elections' in request.POST:
            cost = 200
            if nation.budget < cost:
                result = "You do not have enough money!"
            else:
                chance = random.randint(1, 10)
                gov = utils.attrchange(nation.government, 30)
                appr = utils.attrchange(nation.approval, random.randint(0, 10))
                stab = utils.attrchange(nation.stability, -random.randint(0, 25))
                actions.update({
                    'budget': {'action': 'subtract', 'amount': cost},
                    'government': {'action': 'add', 'amount': gov},
                    'stability': {'action': 'add', 'amount': stab},
                    'approval': {'action': 'add', 'amount': appr},
                    })
                img += "elections.jpg"
                if chance > 6 and nation.approval > 50:
                    result = 'Elections are held, but the rebels continue their struggle, dropping stability. Despite this your victory in the elections increases your popularity.'
                elif nation.rebels >= 3 and nation.approval > 50:
                    actions.update({'rebels': {'action': 'subtract', 'amount': 3}})
                    result = "As you win the elections some rebels recognize the legitimacy of your government and lay down their arms, while popularity increases."
                elif nation.approval > 50:
                    actions.update({'growth': {'action': 'add', 'amount': 1}})
                    result = 'After successful free elections investors invest, hoping to benefit from your stability. Growth and popularity grow.'
                else:
                    stab = utils.attrchange(nation.stability, -random.randint(0, 10))
                    actions = {
                    'budget': {'action': 'subtract', 'amount': cost},
                    'stability': {'action': 'add', 'amount': stab},
                    }
                    img = ""
                    result = "You would have lost the election. Your electoral board has of course rigged it so you stay in power... but be careful next time! Stability drops."

        elif 'housing' in request.POST:
            cost = nation.gdp/2
            if nation.budget < cost:
                result = "You do not have enough money!"
            elif nation.economy >= 66:
                result = "In a free market people pay for their home or they sleep on the street!"
            else:
                chance = random.randint(1, 10)
                appr = utils.attrchange(nation.approval, 10)
                econ = utils.attrchange(nation.economy, -2)
                actions.update({
                    'budget': {'action': 'subtract', 'amount': cost},
                    'economy': {'action': 'add', 'amount': econ},
                    'approval': {'action': 'add', 'amount': appr},
                    })
                img += "housing.jpg"
                if chance > 8:
                    actions.update({'qol': {'action': 'add', 'amount': 1}})
                    result = 'The people are overjoyed at their new cement box! Government popularity increases, as does quality of life.'
                else:
                    result = 'The people are overjoyed at their new cement box! Government popularity increases.'

        elif 'wage' in request.POST:
            if nation.economy <= 33:
                result = "As a socialist state you have already abolished wage slavery!"
            elif nation.growth < -5:
                result = "Your growth is too low to support raising the minimum wage!"
            else:
                chance = random.randint(1, 10)
                cost = int((nation.gdp*1.05)/400)
                econ = utils.attrchange(nation.economy, -2)
                appr = utils.attrchange(nation.approval, 21)
                actions.update({
                    'growth': {'action': 'subtract', 'amount': cost},
                    'economy': {'action': 'add', 'amount': econ},
                    'approval': {'action': 'add', 'amount': appr},
                    })
                img += "minimum.jpg"
                if chance > 8:
                    qol = utils.attrchange(nation.qol, 1)
                    actions.update({'qol': {'action': 'add', 'amount': qol}})
                    result = 'Workers can now afford two and a half meals a day! Government popularity increases, as does quality of life slightly.'
                else:
                    result = 'Wage increases but unfortunately have few effects on the quality of life.'

        elif 'cult' in request.POST:
            cost = 500
            if nation.budget < cost:
                result = "You do not have enough money!"
            elif nation.government <= 40:
                result = "The Great Dear Leader is already adored and loved by his people!"
            else:
                appr = utils.attrchange(nation.approval, 15)
                actions.update({
                    'budget': {'action': 'subtract', 'amount': cost},
                    'government': {'action': 'set', 'amount': 0},
                    'approval': {'action': 'add', 'amount': appr},
                    })
                img += "cult.jpg"
                result = 'Oh How The People Love Me. I Am Their Guardian And Protector From Want And Fear. What A Great Leader I Am.'

        elif 'school' in request.POST:
            cost = costs['school']['money']
            rmcost = costs['school']['rm']
            if nation.budget < cost:
                result = "You do not have enough money!"
            elif nation.rm < rmcost:
                result = "You do not have enough raw materials!"
            elif nation.literacy == 100:
                result = "Literacy rates are already 100%!"
            else:
                lit = utils.attrchange(nation.literacy, 5)
                actions.update({
                    'budget': {'action': 'subtract', 'amount': cost},
                    'literacy': {'action': 'add', 'amount': lit},
                    'rm': {'action': 'subtract', 'amount': rmcost},
                    })
                img += "school.jpg"
                result = 'Literacy increases! Yay!'

        elif 'university' in request.POST:
            total = nation.factories + nation.universities
            rmcost = costs['university']['rm']
            oilcost = costs['university']['oil']
            mgcost = costs['university']['mg']
            if nation.oil < oilcost:
                result = "You do not have enough oil!"
            elif nation.rm < rmcost:
                result = "You do not have enough raw materials!"
            elif nation.mg < mgcost:
                 result = "You do not have enough manufactured goods!"
            elif nation.farmland() < nation.landcost('universities'):
                result = "You do not have enough unused land!"
            else:
                actions.update({
                    'rm': {'action': 'subtract', 'amount': rmcost},
                    'oil': {'action': 'subtract', 'amount': oilcost},
                    'mg': {'action': 'subtract', 'amount': mgcost},
                    'universities': {'action': 'add', 'amount': 1},
                    })
                img += "university.jpg"
                result = "Your students take to the classrooms!"

        elif 'hospital' in request.POST:
            cost = costs['hospital']['money']
            rmcost = costs['hospital']['rm']
            if nation.economy >= 66:
                result = "In a free market economy healthcare is a privilege, not a right!"
            elif nation.rm < rmcost:
                result = "You do not have enough raw materials!"
            elif nation.budget < cost:
                result = "You do not have enough money!"
            elif nation.healthcare == 100:
                result = "National healthcare is already the best it can be!"
            else:
                health = utils.attrchange(nation.healthcare, 10)
                actions.update({
                    'rm': {'action': 'subtract', 'amount': rmcost},
                    'budget': {'action': 'subtract', 'amount': cost},
                    'healthcare': {'action': 'add', 'amount': health},
                    })
                img += "hospital.jpg"
                result = "Deaths from preventative diseases drop significantly, and healthcare skyrockets."

        elif 'medicalresearch' in request.POST:
            cost = costs['medical']['money']
            rmcost = costs['medical']['research']
            if nation.research < rmcost:
                result = "You do not have enough research!"
            elif nation.budget < cost:
                result = "You do not have enough money!"
            elif nation.healthcare == 100:
                result = "National healthcare is already the best it can be!"
            else:
                health = utils.attrchange(nation.healthcare, 10)
                actions.update({
                    'research': {'action': 'subtract', 'amount': rmcost},
                    'budget': {'action': 'subtract', 'amount': cost},
                    'healthcare': {'action': 'add', 'amount': health},
                    })
                img += "hospital.jpg"
                result = "A new vaccine saves countless lives, and healthcare skyrockets."

        elif 'housing' in request.POST:
            cost = nation.gdp/2
            if nation.economy >= 66:
                result = "In a free market people pay for their home or they sleep on the street!"
            elif nation.budget < cost:
                result = "You do not have enough money!"
            elif nation.approval == 100:
                result = "There is already more housing than people!"
            else:
                chance = random.randint(1, 10)
                appr = utils.attrchange(nation.approval, 10)
                econ = utils.attrchange(nation.economy, -2)
                qol = utils.attrchange(nation.qol, 1)
                actions.update({
                    'budget': {'actions': 'subtract', 'amount': cost},
                    'approval': {'actions': 'add', 'amount': appr},
                    'economy': {'actions': 'add', 'amount': econ},
                    })
                img += "housing.jpg"
                if chance > 8:
                    actions.update({'qol': {'actions': 'add', 'amount': qol}})
                    result = "The people are overjoyed at their new cement box! Government popularity increases, as does quality of life."
                else:
                    result = "The people are overjoyed at their new cement box! Government popularity increases."

        elif 'freefood' in request.POST:
            cost = (nation.qol/10*nation.approval/10*nation.gdp/200/4)
            if nation.food < cost:
                result = "You do not have enough food!"
            elif nation.approval == 100:
                result = "People are fat enough as it is!"
            else:
                econ = utils.attrchange(nation.economy, -5)
                appr = utils.attrchange(nation.approval, 10)
                actions.update({
                    'food': {'action': 'subtract', 'amount': cost},
                    'economy': {'action': 'add', 'amount': econ},
                    'approval': {'action': 'add', 'amount': appr},
                    })
                img += "freefood.jpg"
                result = "The poor rejoice at not having to worry about their next meal! Obesity increases by 1%."
        if actions:
            utils.atomic_transaction(Nation, nation.pk, actions)
            nation.policylogging(request.POST, actions)
            nation.refresh_from_db()
            context.update({'img': img})
        if result:
            context.update({'result': result})
    context.update({
        'costs': domesticpolicycosts(nation, initiatives),
        })
    return render(request, 'nation/domestic.html', context)


@nation_required
@login_required
@novacation
def economicpolicies(request):
    nation = Nation.objects.select_related('military', 'researchdata', 'econdata').get(user=request.user)
    mildata = nation.military
    research = nation.researchdata
    policyactions = nation.econdata
    context = {}
    img = ''
    result = False
    if request.method == 'POST':
        actions = {}
        costs = econpolicycosts(nation)
        img = "/static/img/"
        if 'greatleap' in request.POST:
            cost = 100
            rmcost = (nation.growth/3 if nation.growth > 2 else 1)
            if nation.budget < cost:
                result = "You do not have enough money!"
            elif nation.rm < rmcost:
                result = "You do noth ave enough raw materials!"
            elif nation.economy > 66:
                result = "Free markets cannot engage in heinous socialism!"
            else:
                chance = random.randint(1, 10)
                actions.update({
                    'budget': {'action': 'subtract', 'amount': cost},
                    'rm': {'action': 'subtract', 'amount': rmcost},
                    })
                img = ''
                if chance > 4:
                    econ = utils.attrchange(nation.economy, -6)
                    actions.update({
                        'growth': {'action': 'add', 'amount': 1},
                        'economy': {'action': 'add', 'amount': econ}
                        })
                    img += "glf.jpg"
                    result = 'You have improved your economic growth! Let a thousand pig irons bloom!'
                elif chance < 2:
                    actions.update({'growth': {'action': 'subtract', 'amount': 1}})
                    result = 'Poor pig iron! Economic growth decreases!'
                else:
                    result = 'Mediocre pig iron! You have failed to improve economic growth!'

        elif 'blood' in request.POST:
            if nation.region() != 'Africa':
                result = "Only African nations can sell blood diaminds to De Beers!"
            elif policyactions.diamonds < 1:
                result = "You have sold your entire supply already!"
            else:
                gain = nation.gdp/4
                gain = (gain if gain > 100 else 100)
                qol = utils.attrchange(nation.qol, -2)
                rep = utils.attrchange(nation.reputation, -6)
                actions.update({
                    'budget': {'action': 'add', 'amount': gain},
                    'qol': {'action': 'add', 'amount': qol},
                    'reputation': {'action': 'add', 'amount': rep},
                    })
                econactions = {'diamonds': {'action': 'subtract', 'amount': 1}}
                utils.atomic_transaction(Econdata, policyactions.pk, econactions)
                img += "blood.jpg"
                result = 'Your agent makes the handoff to the de Beers agent in Antwerp and returns with a nice suitcase of $%sk cash.' % gain

        elif 'drugs' in request.POST:
            chance = random.randint(1, 10)
            gain = (nation.gdp if nation.gdp > 500 else 500)
            if nation.region() != 'Latin America':
                result = "Only Latin American countries can smuggle drugs directly into the US!"
            elif policyactions.drugs < 1:
                result = "You have sold your entire supply already!"
            else:
                econactions= {'drugs': {'action': 'subtract', 'amount': 1}}

                if chance > 6:
                    actions.update({'budget': {'action': 'add', 'amount': gain}})
                    img += "drugs.jpg"
                    result = 'Your agent makes the handoff to some Cubans in Miami with no problems and returns with a nice suitcase of $$%sk cash.' % gain
                else:
                    rep = utils.attrchange(nation.reputation, -25)
                    actions.update({'reputation': {'action': 'add', 'amount': rep}})
                    img = ""
                    result = "The coastguard captures your shipment off the Florida coast and you are directly implicated! You are condemned by the American President who goes on to mention something about 'regime change'..."
                utils.atomic_transaction(Econdata, policyactions.pk, econactions)

        elif 'collectivization' in request.POST:
            if nation.approval < 30:
                result = "You do not have the approval to push this through!"
            elif nation.qol < 30:
                result = "You do not have the quality of life to do this!"
            elif nation.economy > 33:
                result = "You nations economy is not centrally planned!"
            else:
                chance = random.randint(1, 100)
                qol = utils.attrchange(nation.qol, -20)
                appr = utils.attrchange(nation.approval, -20)
                actions.update({
                'approval': {'action': 'add', 'amount': appr},
                'qol': {'action': 'add', 'amount': qol},
                })
                img = ""
                if chance > 79:
                    research.foodtech += 1
                    img += "collectivization.jpg"
                    result = 'The grains have never been grainer!'
                elif chance < 11:
                    research.foodtech -= (1 if research.foodtech > 0 else 0)
                    result = 'Your forced collectivization is an utter disaster, reducing your agricultural output, reducing approval and quality of life.'
                else:
                    result = "Your forced collectivization is a failure, reducing approval and quality of life."
                research.save(update_fields=['foodtech'])

        elif 'labordiscipline' in request.POST:
            cost = nation.factories * 2 * policyactions.labor
            if nation.oil < cost:
                result = "You do not have enough oil!"
            elif nation.rm < cost:
                result = "You do not have enough raw material!"
            elif nation.approval < 20:
                result = "Your approval is too low! The workers go on strike."
            else:
                appr = utils.attrchange(nation.approval, -10)
                actions.update({
                    'mg': {'action': 'add', 'amount': nation.factories},
                    'rm': {'action': 'subtract', 'amount': cost},
                    'oil': {'action': 'subtract', 'amount': cost},
                    'approval': {'action': 'add', 'amount': appr},
                    })
                img = "http://i.imgur.com/ZAxmwGG.jpg"
                result = 'Your people take to the assembly lines!'

        elif 'industrialize' in request.POST:
            rmcost = costs['industry']['rm']
            oilcost = costs['industry']['oil']
            mgcost = costs['industry']['mg']
            if nation.farmland() < nation.landcost('factories'):
                result = "You do not have enough unused land!"
            elif nation.oil < oilcost:
                result = "You do not have enough oil!"
            elif nation.rm < rmcost:
                result = "You do not have enough raw material!"
            elif nation.mg < mgcost:
                result = "You do not have enough manufactured goods!"
            else:
                actions.update({
                    'mg': {'action': 'subtract', 'amount': mgcost},
                    'rm': {'action': 'subtract', 'amount': rmcost},
                    'oil': {'action': 'subtract', 'amount': oilcost},
                    'factories': {'action': 'add', 'amount': 1},
                    })
                img += "industry.jpg"
                result = 'Your people take to the assembly lines!'

        elif 'deindustrialize' in request.POST:
            if nation.approval < 10:
                result = "Approval is too low!"
            elif nation.factories == 0:
                result = "There are no factories to close!"
            else:
                actions.update({
                    'factories': {'action': 'subtract', 'amount': 1},
                    'closed_factories': {'action': 'add', 'amount': 1},
                    })
                img += "http://i.imgur.com/QerllfI.jpg"
                result = "Thousands lose their jobs!"

        elif 'nationalize' in request.POST:
            if policyactions.nationalize:
                result = "You cannot nationalize or privatize more than once a turn"
            elif nation.FI < 20:
                result = "You cannot nationalize nothing!"
            else:
                econ = utils.attrchange(nation.economy, -50)
                rep =  utils.attrchange(nation.reputation, 2)
                qol = utils.attrchange(nation.qol, -3)
                stab = utils.attrchange(nation.stability, -10)
                actions.update({
                    'budget': {'action': 'add', 'amount': nation.FI},
                    'FI': {'action': 'set', 'amount': 0},
                    'economy': {'action': 'add', 'amount': econ},
                    'reputation': {'action': 'add', 'amount': rep},
                    'qol': {'action': 'add', 'amount': qol},
                    'stability': {'action': 'add', 'amount': stab},
                    })
                Econdata.objects.filter(pk=policyactions.pk).update(nationalize=True)
                img += "nationalize.jpg"
                result = "You seize what is yours! Foreign investment added to the budget. Spend it before the next turn or you'll lose it all!"

        elif 'privatize' in request.POST:
            gain = 300
            if nation.gdp < 110:
                result = "You are too poor, there is nothing to sell!"
            elif policyactions.nationalize:
                result = "You cannot nationalize or privatize more than once per turn!"
            elif nation.economy > 75:
                result = "You have privatized all major state enterprises already!"
            else:
                econ = utils.attrchange(nation.economy, 40)
                actions.update({
                    'budget': {'action': 'add', 'amount': gain},
                    'gdp': {'action': 'subtract', 'amount': 15},
                    'economy': {'action': 'add', 'amount': econ},
                    })
                Econdata.objects.filter(pk=policyactions.pk).update(nationalize=True)
                img += "privatization.jpg"
                result = "Fire sale! Every social program must go! You get 300k in the bank."

        elif 'prospect' in request.POST:
            cost = ((policyactions.prospects**2)*1000)+500
            if nation.region() == "Middle East":
                cost /= 2
            discovery = (random.randint(1000, 5000) if nation.region() == "Middle East" else random.randint(50, 500))
            discovery *= utils.research('prospect', research.prospecttech)
            if nation.budget < cost:
                result = "You do not have enough money!"
            else:
                actions.update({
                    'oilreserves': {'action': 'add', 'amount': int(discovery)},
                    'budget': {'action': 'subtract', 'amount': cost},
                    })
                policyactions.prospects += 1
                policyactions.save(update_fields=['prospects'])
                img += "oil.jpg"
                result = 'Your exploration reveals %s mmbl of black gold below our otherwise worthless sand dunes.' % discovery

        elif 'imf' in request.POST:
            if nation.growth <= 0:
                result = "You cannot borrow if your economy is not growing!"
            elif nation.alignment == 0:
                result = "Eastern Bloc nations are not members of the IMF!"
            else:
                econ = utils.attrchange(nation.economy, 6)
                qol = utils.attrchange(nation.qol, -1)
                actions.update({
                    'budget': {'action': 'add', 'amount': 100},
                    'growth': {'action': 'subtract', 'amount': 2},
                    'economy': {'action': 'add', 'amount': econ},
                    'qol': {'action': 'add', 'amount': qol},
                    })
                img += "imf.jpg"
                result = "You take out an IMF loan. Growth decreases as you must now pay off your debt. Spend the loan before the next turn or you'll lose it all!!"

        elif 'humanitarian' in request.POST:
            cost = 75
            if nation.gdp > 299:
                result = "Your nation is too wealthy to recieve humanitarian aid!"
            elif nation.budget < cost:
                result = "You do not have enough money!"
            else:
                actions.update({
                    'budget': {'action': 'subtract', 'amount': cost},
                    'growth': {'action': 'add', 'amount': 1},
                    })
                img += "humanitarian.jpg"
                result = "Your nation's economy has improved slighty!"

        elif 'foreigninvestment' in request.POST:
            cost = 75
            fi = (5 if nation.growth <= 5 else nation.growth)
            rmcost = (nation.growth/6 if nation.growth > 2 else 1)
            if nation.budget < cost:
                result = "You do not have enough money!"
            elif nation.rm < rmcost:
                result = "You do not have enough raw material!"
            elif nation.economy < 33:
                result = "Foreign capitalists will not invest in a nation ruled by money-hating Bolsheviks!"
            else:
                chance = random.randint(1, 10)
                econ = utils.attrchange(nation.economy, 1)
                actions.update({                    
                    'budget': {'action': 'subtract', 'amount': cost},
                    'rm': {'action': 'subtract', 'amount': rmcost},
                    'economy': {'action': 'add', 'amount': econ}
                    })
                img = ""
                if chance > 7:
                    actions.update({
                        'FI': {'action': 'add', 'amount': fi},
                        'growth': {'action': 'add', 'amount': 1},
                        })
                    img += "foreigninvest.jpg"
                    result = "Foreign investment pours in which trickles down all over your economy, generating growth!"
                elif chance < 4:
                    actions.update({'FI': {'action': 'add', 'amount': fi}})
                    result = "Foreign investment pours in but unfortunately there is no trickling down on the domestic economy!"
                else:
                    result = "No one takes up your offer to invest!"

        elif 'mine' in request.POST:
            cost = 250+50*nation.mines
            cost = (int(cost/1.5) if nation.region() == 'Latin America' or nation.region() == 'Africa' else cost)

            if nation.budget < cost:
                result = "You do not have enough money!"
            elif nation.farmland() < nation.landcost('mines'):
                result = "You do not have enough unused land!"
            else:
                actions.update({                    
                    'budget': {'action': 'subtract', 'amount': cost},
                    'mines': {'action': 'add', 'amount': 1},
                })
                img += "mine2.jpg"
                result = "Your new mine increases raw material production by a hundred tons a month."

        elif 'closemine' in request.POST:
            if nation.approval < 10:
                result = "Approval is too low!"
            elif nation.mines == 0:
                result = "There are no mines to close!"
            else:
                actions.update({
                    'mines': {'action': 'subtract', 'amount': 1},
                    'closed_mines': {'action': 'add', 'amount': 1},
                    })
                img = "http://i.imgur.com/QerllfI.jpg"
                result = 'Thousands lose their jobs!'

        elif 'privatemine' in request.POST:
            cost = 250+50*nation.mines
            cost = (cost if nation.region() != 'Latin America' or nation.region() != 'Africa' else int(cost/1.5))/4
            if nation.FI < cost:
                result = "You do not have enough foreign investment!"
            elif nation.farmland() < nation.landcost('mines'):
                result = "You do not have enough unused land!"
            else:
                actions.update({
                    'FI': {'action': 'subtract', 'amount': cost},
                    'mines': {'action': 'add', 'amount': 1},
                    })
                img += "mine2.jpg"
                result = "Your new mine increases raw material production by a hundred tons a month."

        elif 'well' in request.POST:
            cost = 500+(100*nation.wells)
            cost = (cost if nation.region() != 'Middle East' else int(cost/1.5))
            if nation.budget < cost:
                result = "You do not have enough money!"
            elif nation.farmland() < nation.landcost('wells'):
                result = "You do not have enough unused land!"
            else:
                actions.update({
                    'budget': {'action': 'subtract', 'amount': cost},
                    'wells': {'action': 'add', 'amount': 1}, 
                    })
                img += "oil.jpg"
                result = "Your new well increases oil production by a million barrels a month."

        elif 'closewell' in request.POST:
            if nation.approval < 10:
                result = "Approval is too low!"
            elif nation.wells == 0:
                result = "There are no oil wells to close!"
            else:
                actions.update({
                    'wells': {'action': 'subtract', 'amount': 1},
                    'closed_wells': {'action': 'add', 'amount': 1},
                    })
                img = "http://i.imgur.com/QerllfI.jpg"
                result = "Thousands lose their jobs!"

        elif 'privatewell' in request.POST:
            cost = 500+(100*nation.wells)
            cost = (cost if nation.region() != 'Middle East' else int(cost/1.5))/4
            if nation.FI < cost:
                result = "You do not have enough foreign investment!"
            elif nation.farmland() < nation.landcost('wells'):
                result = "You do not have enough unused land!"
            else:
                actions.update({
                    'FI': {'action': 'subtract', 'amount': cost},
                    'wells': {'action': 'add', 'amount': 1},
                    })
                img += "oil.jpg"
                result = "Your new well increases oil production by a million barrels a month."

        elif 'forced' in request.POST:
            cost = 50
            rmcost = nation.growth/15
            rmcost = (rmcost if rmcost > 0 else 1)
            if nation.budget < cost:
                result = "You do not have enough money!"
            elif nation.rm < rmcost:
                result = "You do not have enough raw materials!"
            elif nation.government > 20:
                result = "Youre not tyrannical enough, unfortunately."
            else:
                chance = random.randint(1, 100)
                qol = utils.attrchange(nation.qol, -5)
                rep = utils.attrchange(nation.reputation, -3)
                appr = utils.attrchange(nation.approval, -3)
                actions.update({
                    'budget': {'action': 'subtract', 'amount': cost},
                    'rm': {'action': 'subtract', 'amount': rmcost},
                    'approval': {'action': 'add', 'amount': appr},
                    'qol': {'action': 'add', 'amount': qol},
                    'reputation': {'action': 'add', 'amount': rep},
                    })
                if chance < 95:
                    actions.update({'growth': {'action': 'add', 'amount': 1}})
                    img += "forced.jpg"
                    result = 'You have improved your economic growth! Enjoy the fruits of their forced labor.'
                else:
                    actions.update({'rebels': {'action': 'add', 'amount': 1}})
                    img += "rebel.jpg"
                    result = "Unfortunately they laborers fled and joined the rebels without doing any work..."

        elif 'sez' in request.POST and nation.region() == "Asia":
            cost = 100
            market = Market.objects.all().latest('pk')
            rmcost = (1 if nation.growth/4 < 1 else nation.growth/4)
            if nation.budget < cost:
                result = "You do not have enough money!"
            elif nation.rm < rmcost:
                result = "You do not have enough raw materials!"
            elif nation.economy > 66:
                result = "Your entire countrys economy is already free market!"
            else:
                chance = random.randint(1, 10)
                actions.update({
                    'budget': {'action': 'subtract', 'amount': cost},
                    'rm': {'action': 'subtract', 'amount': rmcost}
                    })
                if chance > 4:
                    econ = utils.attrchange(nation.economy, 2)
                    actions.update({
                        'growth': {'action': 'add', 'amount': market.change},
                        'economy': {'action': 'add', 'amount': econ},
                        })
                    img += "sez.jpg"
                    result = "Foreign owned factories pop up throughout the SEZ! Growth increases by the current global market!"
                else:
                    appr = utils.attrchange(nation.approval, -5)
                    actions.update({'approval': {'action': 'add', 'amount': appr}})
                    img = ""
                    result = "Opposition from hardliners stops the creation of an SEZ! Government popularity drops slightly..."


        if result:
            context.update({'result': result})
        if actions:
            utils.atomic_transaction(Nation, nation.pk, actions)
            nation.policylogging(request.POST, actions)
            nation.refresh_from_db()
            context.update({'img': img})
    context.update(econpolicycosts(nation))

    return render(request, 'nation/economics.html', context)


def econpolicycosts(nation):
    data = {
        'great_leap': (nation.growth/3 if nation.growth > 2 else 1),
        'labor_discipline': nation.factories * 2 * nation.econdata.labor,
        'forced_labor': (nation.growth/15 if nation.growth/15 > 0 else 1),
        'sez': (1 if nation.growth/4 < 1 else nation.growth/4),
        'FI': (nation.growth/6 if nation.growth > 2 else 1),
        }
    total = nation.factories + nation.universities
    if nation.region() != 'Asia':
        data.update({'industry': {
            'rm': total * 100 + 50,
            'oil': total * 50 + 25,
            'mg': total*2,
            }})            
    else:
        data.update({'industry': {
            'rm': total * 75 + 38,
            'oil': total * 38 + 19,
            'mg': int(total*2*0.75),
            }})
    if nation.region() != 'Middle East':
        data.update({'prospect': ((nation.econdata.prospects**2)*1000)+500})
        data.update({'wellcost': 500+(100*nation.wells)})
    else:
        data.update({'prospect': (((nation.econdata.prospects**2)*1000)+500)/2})
        data.update({'wellcost': int((500+(100*nation.wells))/1.5)})

    if nation.region() == 'Latin America' or 'African':
        data.update({'minecost': int((250+50*nation.mines)/1.5)})
    else:
        data.update({'minecost': 250+50*nation.mines})

    data.update({'privateminecost': data['minecost']/4})
    data.update({'privatewellcost': data['wellcost']/4})
    return data