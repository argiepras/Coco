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
    trainingcost = (mildata.army**2 * mildata.training**2) / 20000
    trainingcost = (trainingcost if mildata.army < trainingcost else mildata.army)
    if request.method == 'POST':
        actions = {}
        img = "/static/img/"



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
            if nation.alignment == 3:
                result = "The soviet union doesn't deal with the likes of you"
            elif nation.oil < oilcost:
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
            elif nation.factories < 3:
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
            if nation.alignment == 1:
                result = "The united states refuses to respond"
            elif nation.oil < oilcost:
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


        elif 'nuke' in request.POST:
            if mildata.reactor < 20:
                result = "You do not have a nuclear reactor!"
            elif nation.budget < 100000:
                result = "You do not have enough money!"
            elif nation.uranium < 20:
                result = "You do not have enough uranium!"
            elif nation.research < 200:
                result = "You do not have enough research!"
            else:
                actions.update(
                    {
                    'budget': {'action': 'subtract', 'amount': 100000},
                    'uranium': {'action': 'subtract', 'amount': 20},
                    'research': {'action': 'subtract', 'amount': 200},
                    })
                Military.objects.filter(nation__pk=nation.pk).update(nukes=F('nukes') + 1)
                img = "http://i.imgur.com/wLtwYXi.jpg"
                result = 'You have a nuke.'

        elif 'aks' in request.POST:
            if nation.alignment == 3:
                result = "The soviet union doesn't deal with the likes of you"
            elif nation.soviet_points < 8:
                result = "You do not have close enough relations with the Soviets!"
            elif mildata.weapons > 500:
                result = "You have better equipment! These are worthless!"
            else:
                actions.update({'soviet_points': {'action': 'subtract', 'amount': 8}})
                mildata.weapons += 2
                mildata.save(update_fields=['weapons'])
                img = ""
                result = "Thousands of AKMs are airlifted straight to you from Moscow."

        elif 'm14' in request.POST:
            if nation.alignment == 1:
                result = "The united states refuses to respond"
            elif nation.us_points < 8:
                result = "You do not have close enough relations with the US!"
            elif mildata.weapons > 500:
                result = "You have better equipment! These are worthless!"
            else:
                actions.update({'us_points': {'action': 'subtract', 'amount': 8}})
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
            cost = 16
            oilcost = 3
            if nation.alignment == 3:
                result = "The soviet union doesn't deal with the likes of you"
            elif nation.soviet_points < cost:
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
            cost = 16
            oilcost = 3
            if nation.alignment == 1:
                result = "The united states refuses to respond"
            elif nation.us_points < cost:
                result = "You do not have enough relationship points with the United States!"
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
            cost = 25
            oilcost = 10
            if nation.alignment == 3:
                result = "The soviet union doesn't deal with the likes of you"
            elif nation.soviet_points < cost:
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
            cost = 25
            oilcost = 10
            if nation.alignment == 1:
                result = "The united states refuses to respond"
            elif nation.us_points < cost:
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
            'trainingcost': trainingcost,
            'migcost': {'oil': mildata.planes + 5, 'points': 11 + ((mildata.planes**2)-10)},
            'planecost': {'mg': 11 + ((mildata.planes**2)/2), 'oil': mildata.planes + 5},
            'shipcost': {'mg': 10+mildata.navy, 'oil': 10+mildata.navy/2},  
        })

    return render(request, 'nation/military.html', context)


@nation_required
@login_required
@novacation
def foreignpolicies(request):

    if result:
        context.update({'result': result})
    context.update({'intervention': (25 if nation.region() == 'Latin America' else 35)})
    return render(request, 'nation/foreign.html', context)


