from intelligenceforms import newspyform, extraditeform, surveillanceform
from .models import *
from .utilities import get_active_player
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from decorators import nation_required
from django.db.models import F
from math import sqrt
import random
import nation.news as news
import nation.utilities as utils

def namegen():
    return str(random.randint(111, 999))

@nation_required
@login_required
def overview(request):
    context = {}
    result = False
    nation = request.user.nation
    if request.method == 'POST':
        if 'train' in request.POST:
            cost = nation.spies.all().count()*1000
            if nation.budget < cost:
                result = "You cannot afford this! You need $%sk more!" % (cost - nation.budget)
            else:
                form = newspyform(request.POST)
                if form.is_valid():
                    if nation.settings.donor and form.cleaned_data['name']:
                        name = form.cleaned_data['name']
                    else:
                        name = namegen()
                    img = "spies/%s.png" % random.randint(1, 21)
                    spy = nation.spies.create(name=name, specialty=form.cleaned_data['specialty'], location=nation, portrait=img)
                    action = {'budget': {'action': 'subtract', 'amount': cost}}
                    utils.atomic_transaction(Nation, nation.pk, action)
                    #so it'll load the subtracted cost 
                    nation.budget -= cost
                    request.user.nation = nation
                    result = "Agent %s is available to serve his country proudly!" % spy.name
                else:
                    result = "Your spy cannot specialize in %s" % form['specialty']

        elif 'accept' in request.POST or 'deny' in request.POST:
            vers = 'deny'
            if 'accept' in request.POST:
                vers = 'accept'
            if nation.pending_requests.all().filter(pk=request.POST[vers]).exists():
                ext_request = nation.pending_requests.all().get(pk=request.POST[vers])
                if vers == 'accept':
                    #update spy location and insert newsitems
                    Spy.objects.filter(pk=ext_request.spy.pk).update(location=nation)
                    news.extraditioned(ext_request.nation, ext_request.target, 'accepted', ext_request.spy)
                    result = "Extradition request is accepted and agent %s arrives in a secure facility" % ext_request.spy.name
                else: #deny the request!
                    news.extraditioned(ext_request.nation, ext_request.target, 'denied', ext_request.spy)
                    result = "The request is denied"
                ext_request.delete()

    spies = Spy.objects.select_related('location').filter(nation=nation)
    extraditions = False
    if nation.pending_requests.all().exists():
        extraditions = nation.pending_requests.all()
    context.update({
        'newspy': newspyform(), 
        'cost': len(spies)*1000, 
        'spies': spies,
        'extraditions': extraditions,
        'enemyspies': nation.infiltrators.filter(discovered=True),
        'result': result,
        })
    return render(request, 'nation/intelligence.html', context)


@nation_required
@login_required
def details(request, spyid):
    nation = request.user.nation
    try:
        spy = nation.spies.all().select_related('location').get(pk=int(spyid))
        found = True
    except:
        found = False
    if not found:
        try: 
            spy = nation.infiltrators.all().filter(discovered=True).select_related('nation').get(pk=int(spyid))
        except:
            return redirect('nation:intelligence')
    context = {
    'spy': spy,
    'deployed': (True if spy.location and spy.location != nation else False),
    }
    enemyspy = False
    if spy.nation != nation:
        enemyspy = True
    actionlist = 'none'
    if context['deployed']:
        actionlist = 'deployed'
    elif not enemyspy:
        actionlist = 'home'
    context.update({'enemy': enemyspy, 'actionlist': actionlist})

    if request.method == "POST":
        context.update(spyactions(request, spy))
        try: #in case the spy was executed, otherwise this is a 500 internal error
            spy.refresh_from_db()
        except:
            pass

    if context['deployed']:
        context.update({
            'counterintel': spy.location.gdp/30,
            'mutiny': spy.location.gdp/30,
            'poison': spy.location.gdp/15,
            'sabotagemine': spy.location.gdp/30,
            'sabotagewell': spy.location.gdp/30,
            'terrorist': spy.location.gdp/15,
            'fund': spy.location.gdp/30,
            })
    elif context['enemy']:
        context.update({
            'surveillanceform': surveillanceform(nation),
            'transferform': extraditeform(),
            'surveilcost': surveilcost(spy),
            'accidentcost': int(sqrt(surveilcost(spy)*(5+spy.experience/10)))
            })
    else:
        context.update({'counterintel': nation.gdp/30})
    return render(request, 'nation/spy.html', context)

@nation_required
@login_required
def discoveredagents(request):
    nation = request.user.nation
    context = {}
    spies = nation.infiltrators.all().filter(discovered=True)

    context.update({
            'spies': spies,
        })
    return render(request, 'nation/discovered.html', context)


def spyactions(request, spy):
    #handles POST requests
    nation = request.user.nation
    context = False
    choices = {
        'withdraw': withdraw,
        'armrebels': armrebels,
        'fundopposition': fundopposition,
        'terroristattack': terroristattack,
        'sabotagemine': sabotagemine,
        'sabotagewell': sabotagewell,
        'poison': poison,
    }
    homechoices = {
        'counter': counter,
        'endsurveillance': endsurveillance,
    }
    enemychoices = {
        'surveillancing': surveillancing,
        'end_surveillance': end_surveillance,
        'arrest': arrest,
        'execute': execute,
        'deport': deport,
        'accident': accident,
        'extradite': extradite,

    }
    #if spy.actioned and spy.nation == nation:
        #context = {'result': 'Agent %s has already performed an action this turn!' % spy.name}
    if spy.arrested and spy.nation == nation:
        context = {'result': 'Agent %s is imprisoned and cannot perform any actions! Reported!' % spy.name}
    else:
        #use context has a boolean flag
        #for whether a spy actually 
        if request.POST['action'] in choices and spy.location.pk != nation.pk:
            context = choices[request.POST['action']](nation, spy.location, spy)
        elif request.POST['action'] in homechoices and spy.location.pk == nation.pk:
            context = homechoices[request.POST['action']](nation, spy)
        elif request.POST['action'] in enemychoices and (spy.nation != nation and spy.discovered):
            context = enemychoices[request.POST['action']](request, spy)
        else:
            context = {'result': 'Invalid POST data'}
    return context
    


def commitspy(spy, actions=False):
    if actions:
        actions.update({'actioned': {'action': 'set', 'amount': True}})
        utils.atomic_transaction(Spy, spy.pk, actions)
    else:
        spy.actioned = True
        spy.save()

def surveilcost(spy):
    if spy.experience == 0:
        spy.experience = 1
    return int(sqrt(spy.nation.population() / 100) * ((spy.experience/10 + (sqrt(spy.experience))/2)))

###################
#### Enemy choices
###################

def retractextradition(request, spy):
    img = ''
    nation = request.user.nation
    if Extradition_request.objects.filter(spy=spy).exists():
        spy.extradition_request.delete()
        result = "The extradition request has been withdrawn"
    else:
        result = "There is no extradition request for this agent!"
    return {'result': result, 'img': img}


def extradite(request, spy):
    img = ''
    nation = request.user.nation
    form = extraditeform(request.POST)
    if form.is_valid():
        target = get_active_player(form.cleaned_data['name'])
        if target:
            if target == spy.nation:
                result = "Sending the agent home is called a deportation!"
            elif target.pending_requests.all().filter(nation=nation).exists():
                result = "You have already requested an extradition to %s!" % target.name
            elif Extradition_request.objects.filter(spy=spy).exists():
                result = "There is already a pending extradition request for agent %s!" % spy.name
            else:
                nation.outgoing_requests.create(target=target, spy=spy)
                result = "An extradition request has been served to the leader of %s!" % target.name
        else:
            result = "Invalid nation"

    else:
        result = "Invalid input"
    return {'result': result, 'img': img}



def deport(request, spy):
    img = ''
    result = "Agent %s has been deported." % spy.name
    spy.move_home()
    news.deported(spy.nation, spy.location, spy)
    return {'result': result, 'img': img}


def execute(request, spy):
    img = ''
    gov = request.user.nation.government / 20
    actions = {'budget': {'action': 'subtract', 'amount': 50}}
    result = "Agent %s is marched in front of a firing squad and promptly executed!" % spy.name
    spy.delete()
    news.executed(spy.nation, spy.location, spy)
    return {'result': result, 'img': img}


def accident(request, spy):
    img = ''
    tot = spy.experience + spy.infiltration
    chance = 90 - tot/5
    if spy.surveillance:
        chance = 95
    if chance > random.randint(1, 100):
        Spy.objects.filter(pk=spy.pk).update(discovered=False, surveillance=False)
        news.avoidedaccident(spy)
        result = "The agent managed to avoid the 'accident' and disappeared!"
    else:
        result = "The agent was accidentally run over 3 times and poisoned on the way to the hospital."
        spy.delete()
        news.executed(spy.nation, spy.location, spy)
    Spy.objects.filter(surveilling=spy).update(surveilling=None)
    return {'result': result, 'img': img}


def surveillancing(request, spy):
    nation = request.user.nation
    img = ''
    form = surveillanceform(nation, request.POST)
    if form.is_valid():
        NSA = form.cleaned_data['spy']
        cost = surveilcost(spy)
        if nation.budget < cost:
            result = "We do not have the necessary funds!"
        else:
            Spy.objects.filter(pk=spy.pk).update(surveillance=True)
            Spy.objects.filter(pk=NSA.pk).update(surveilling=spy)
            utils.atomic_transaction(Nation, nation.pk, {'budget': {'action': 'subtract', 'amount': cost}})
            result = "Agent %s assembles a small team and sets up surveillance." % NSA.name
    else:
        result = "invalid spy selected!"
    return {'result': result, 'img': img}

def end_surveillance(request, spy):
    if spy.surveillance:
        spy = Spy.objects.get(surveilling=spy)
        return endsurveillance(request.user.nation, spy)
    else:
        return {'img': '', 'result': "The agent isn't under surveillance!"}



def arrest(request, spy):
    img = ''
    if spy.surveillance:
        chance = 100 - (spy.experience/10)
    else:
        factor = (int(spy.experience/10) if spy.experience >= 10 else 1)
        chance = int(sqrt(factor * (spy.infiltration + spy.experience) + spy.experience/10))
        timefactor = sqrt(1 * ((spy.experience + spy.infiltration) / 2))
        chance = int(chance + timefactor)
    #chance to avoid arrest
    if chance > random.randint(1, 100):
        news.avoidedarrest(spy.nation, spy.location, spy)
        Spy.objects.filter(pk=spy.pk).update(discovered=False)
        result = "The foreign agent evaded the arrest and disappeared!"
    else:
        news.arrested(spy.nation, spy.location, spy)
        Spy.objects.filter(pk=spy.pk).update(arrested=True)
        result = "The foreign agent was placed under arrest and transported to a secure facility!"
    return {'result': result, 'img': img}


#####################
#### Regular choices
#####################


def infiltrate(location, spy):
    chance = 1
    if location.spies.all().filter(location=location, specialty="Spy Hunter").exists():
        chance = 2
    if chance >= random.randint(1, 10): #10% chance of failure
        if location.alignment == spy.nation.alignment:
            news.caughtspyreturn(location)
            result = "Your spy was discovered at the border and sent back after \
            a thorough interrogation."
        else:
            news.caughtspyarrested(location)
            result = "Your spy was discovered at the border and immediately arrested."
            Spy.objects.filter(pk=spy.pk).update(arrested=True, discovered=True, actioned=True, location=location)
    else:
        Spy.objects.filter(pk=spy.pk).update(actioned=True, location=location)
        result = "Your spy slips across the border effortlessly and begins to set up set up \
                    an intelligence network."
    return result


def withdraw(nation, target, spy):
    img = ''
    if spy.infiltration < 10:
        result = "Agent do not have enough infiltration!"
    elif spy.arrested:
        result = "Agent has been arrested! We can't pull him out!"
    else:
        chance = 95
        if target.spies.filter(location=target, specialty="Spy Hunter").exists() or spy.discovered:
            chance = 75
        if spy.surveillance:
            chance = 10
            if spy.specialty == "Intelligence":
                chance = 25

        actions = {'infiltration': {'action': 'add', 'amount': utils.attrchange(spy.infiltration, -10)}}
            
        if chance > random.randint(1, 100):
            spy.move_home()
            result = "Agent %s quietly slips through the border and returns home." % spy.name
        else:
            news.caughtspyreturning(target, nation)
            spyactions.update({
                'arrested': {'action': 'set', 'amount': True},
                'discovered': {'action': 'set', 'amount': True},
                })
            commitspy(spy, actions)
            result = "Agent %s was caught while trying to move out of %s and was placed under arrest!" % (spy.name, target.name)
    return {'result': result, 'img': img}



def armrebels(nation, target, spy):
    img = ''
    if spy.infiltration < 10:
        result = "Agent do not have enough infiltration!"
    elif nation.military.weapons < 20:
        result = "We do not have the weaponry for this!"
    else:
        spyactions = {'infiltration': {'action': 'add', 'amount': utils.attrchange(spy.infiltration, -10)}}
        strength = spy.experience + spy.infiltration - target.approval
        if spy.specialty != 'Gunrunner':
            strength /= 2
        chance = random.randint(-750, 500)
        if strength < chance:
            result = "%s was caught arming the rebels. Agent %s has been arrested." % (spy.name, spy.name)
            #no news report
            img = "spy.jpg"
            spyactions.update({
                'arrested': {'action': 'set', 'amount': True},
                'discovered': {'action': 'set', 'amount': True}
                })
        else:
            img = "rebel.jpg"
            result = "%s has successfully armed the rebels." % spy.name
            spyactions = {
                'experience': {'action': 'add', 'amount': utils.attrchange(spy.experience, 5)},
            }
            nationactions = {
                'weapons': {'action': 'subtract', 'amount': 5}
            }
            targetactions = {
                'rebels': {'action': 'add', 'amount': 2},
            }
            utils.atomic_transaction(Nation, target.pk, targetactions)
            utils.atomic_transaction(Military, nation.military.pk, nationactions)
        commitspy(spy, spyactions)
    return {'result': result, 'img': img}


def fundopposition(nation, target, spy):
    img = "spy.jpg"
    cost = target.gdp/30
    if spy.infiltration < 10:
        result = "Agent do not have enough infiltration!"
    elif nation.budget < cost:
        result = "We do not have enough funds for this!"
    else:
        strength = spy.experience + spy.infiltration - target.approval
        spyactions = {
            'actioned': {'action': 'set', 'amount': True},
            'infiltration': {'action': 'add', 'amount': utils.attrchange(spy.infiltration, -10)}
        }
        if spy.specialty != 'Launderer':
            strength /= 2
        chance = random.randint(-500, 500)
        if strength < chance:
            result = "%s was caught trying to fund the opposition. The agent has been arrested." % spy.name
            #no news report
            spyactions.update({
                'arrested': {'action': 'set', 'amount': True},
                'discovered': {'action': 'set', 'amount': True}
                })
        else:
            result = "%s has successfully funded the opposition, decreasing government approval." % spy.name
            spyactions = {
                'experience': {'action': 'add', 'amount': utils.attrchange(spy.experience, 5)},
                'infiltration': {'action': 'add', 'amount': utils.attrchange(spy.infiltration, -10)}
            }
            nationactions = {
                'budget': {'action': 'subtract', 'amount': cost}
            }
            targetactions = {
                'approval': {'action': 'add', 'amount': utils.attrchange(target.approval, -10)},
            }
            utils.atomic_transaction(Nation, target.pk, targetactions)
            utils.atomic_transaction(Nation, nation.pk, nationactions)
        commitspy(spy, spyactions)
    return {'result': result, 'img': img}


def terroristattack(nation, target, spy):
    img = ''
    cost = target.gdp/15
    if spy.infiltration < 50:
        result = "Agent do not have enough infiltration!"
    elif nation.budget < cost:
        result = "We do not have enough funds for this!"
    elif nation.military.weapons < 20:
        result = "We do not have the weapons to do this!"
    else:
        strength = spy.experience + spy.infiltration - target.approval
        spyactions = {
            'actioned': {'action': 'set', 'amount': True},
            'infiltration': {'action': 'add', 'amount': utils.attrchange(spy.infiltration, -50)}
        }
        if spy.specialty != 'Terrorist':
            strength /= 2
        chance = random.randint(-300, 500)
        if strength < chance:
            result = "%s has been caught planning a terrorist attack! The agent responsible has been detained." % spy.name
            news.terroristattack(target)
            img = "spy.jpg"
            spyactions.update({
                'arrested': {'action': 'set', 'amount': True},
                'discovered': {'action': 'set', 'amount': True}
                })
        else:
            img = "spy.jpg"
            news.terroristattacked(target)
            result = "%s has successfully pulled off a terrorist attack and framed it on an internal\
             faction, killing countless innocent civilians and decreasing stability in the country." % spy.name
            spyactions = {
                'experience': {'action': 'add', 'amount': utils.attrchange(spy.experience, 5)},
            }
            nationactions = {
                'budget': {'action': 'subtract', 'amount': cost},
            }
            nationmilactions = {
                'weapons': {'action': 'subtract', 'amount': 10},
            }
            targetactions = {
                'stability': {'action': 'add', 'amount': utils.attrchange(target.approval, -15)},
            }
            utils.atomic_transaction(Nation, target.pk, targetactions)
            utils.atomic_transaction(Nation, nation.pk, nationactions)
            utils.atomic_transaction(Military, nation.military.pk, nationmilactions)
        commitspy(spy, spyactions)
    return {'result': result, 'img': img}



def sabotagewell(nation, target, spy):
    img = ''
    cost = target.gdp/15
    if spy.infiltration < 20:
        result = "Agent do not have enough infiltration!"
    elif nation.budget < cost:
        result = "We do not have enough funds for this!"
    elif nation.military.weapons < 20:
        result = "We do not have the weapons to do this!"
    elif target.wells == 0:
        result = "They have no oil wells!"
    else:
        strength = spy.experience + spy.infiltration - target.approval
        spyactions = {
            'actioned': {'action': 'set', 'amount': True},
            'infiltration': {'action': 'add', 'amount': utils.attrchange(spy.infiltration, -20)}
        }
        if spy.specialty != 'Saboteur':
            strength /= 2
        chance = random.randint(-300, 500)
        if strength < chance:
            result = "%s was caught sabotaging an oil well. The agent responsible has been detained." % spy.name
            news.sabotagewell(target)
            img = "spy.jpg"
            spyactions.update({
                'arrested': {'action': 'set', 'amount': True},
                'discovered': {'action': 'set', 'amount': True}
                })
        else:
            img = "spy.jpg"
            result = "%s has successfully sabotaged an oil well, decreasing their production." % spy.name
            news.sabotagedwell(target)
            spyactions = {
                'experience': {'action': 'add', 'amount': utils.attrchange(spy.experience, 5)},
            }
            nationactions = {
                'budget': {'action': 'subtract', 'amount': cost},
            }
            nationmilactions = {
                'weapons': {'action': 'subtract', 'amount': 10},
            }
            targetactions = {
                'wells': {'action': 'subtract', 'amount': 1},
            }
            utils.atomic_transaction(Nation, target.pk, targetactions)
            utils.atomic_transaction(Nation, nation.pk, nationactions)
            utils.atomic_transaction(Military, nation.military.pk, nationmilactions)
        commitspy(spy, spyactions)
    return {'result': result, 'img': img}


def sabotagemine(nation, target, spy):
    img = ''
    cost = target.gdp/30
    if spy.infiltration < 20:
        result = "Agent do not have enough infiltration!"
    elif nation.budget < cost:
        result = "We do not have enough funds for this!"
    elif nation.military.weapons < 20:
        result = "We do not have the weapons to do this!"
    elif target.mines == 0:
        result = "They have no mines!"
    else:
        strength = spy.experience + spy.infiltration - target.approval
        spyactions = {
            'actioned': {'action': 'set', 'amount': True},
            'infiltration': {'action': 'add', 'amount': utils.attrchange(spy.infiltration, -20)}
        }
        if spy.specialty != 'Saboteur':
            strength /= 2
        chance = random.randint(-300, 500)
        if strength < chance:
            result = "Agent %s was caught sabotaging a mine. He has been placed under arrest." % spy.name
            news.sabotagemine(target)
            spyactions.update({
                'arrested': {'action': 'set', 'amount': True},
                'discovered': {'action': 'set', 'amount': True}
                })
            img = "spy.jpg"
        else:
            img = "spy.jpg"
            result = "%s has successfully sabotaged a mine, decreasing their production." % spy.name
            news.sabotagedmine(target)
            spyactions = {
                'experience': {'action': 'add', 'amount': utils.attrchange(spy.experience, 5)},
            }
            nationactions = {
                'budget': {'action': 'subtract', 'amount': cost},
            }
            nationmilactions = {
                'weapons': {'action': 'subtract', 'amount': 2},
            }
            targetactions = {
                'mines': {'action': 'subtract', 'amount': 1},
            }
            utils.atomic_transaction(Nation, target.pk, targetactions)
            utils.atomic_transaction(Nation, nation.pk, nationactions)
            utils.atomic_transaction(Military, nation.military.pk, nationmilactions)
        commitspy(spy, spyactions)
    return {'result': result, 'img': img}



def poison(nation, target, spy):
    img = ''
    cost = target.gdp/15
    if spy.infiltration < 50:
        result = "Agent do not have enough infiltration!"
    elif nation.budget < cost:
        result = "We do not have enough funds for this!"
    elif nation.military.weapons < 20:
        result = "We do not have the weapons to do this!"
    elif target.econdata.foodproduction == 0:
        result = "Their food production has already been decimated!"
    else:
        strength = spy.experience + spy.infiltration - target.approval
        spyactions = {
            'actioned': {'action': 'set', 'amount': True},
            'infiltration': {'action': 'add', 'amount': utils.attrchange(spy.infiltration, -20)}
        }
        if spy.specialty != 'Saboteur':
            strength /= 2
        chance = random.randint(-300, 500)
        if strength < chance:
            result = "%s was caught preparing to poison the crops. He was subsequently placed under arrest." % spy.name
            img = "spy.jpg"
            spyactions.update({
                'arrested': {'action': 'set', 'amount': True},
                'discovered': {'action': 'set', 'amount': True}
                })
        else:
            img = "spy.jpg"
            result = "%s successfully poisoned the target nation's crops, decreasing their food production." % spy.name
            spyactions = {
                'experience': {'action': 'add', 'amount': utils.attrchange(spy.experience, 5)},
            }
            nationactions = {
                'budget': {'action': 'subtract', 'amount': cost},
            }
            nationmilactions = {
                'weapons': {'action': 'subtract', 'amount': 2},
            }
            targetactions = {
                'foodproduction': {'action': 'subtract', 'amount': (1 if target.econdata.foodproduction > 0 else 0)},
            }
            utils.atomic_transaction(Econdata, target.econdata.pk, targetactions)
            utils.atomic_transaction(Nation, nation.pk, nationactions)
            utils.atomic_transaction(Military, nation.military.pk, nationmilactions)
        commitspy(spy, spyactions)
    return {'result': result, 'img': img}


##################
### Home choices
##################

def endsurveillance(nation, spy):
    img = ''
    result = "Agent %s isn't surveilling anyone!"
    if spy.surveilling != None:
        Spy.objects.filter(pk=spy.surveilling.pk).update(surveillance=False)
        Spy.objects.filter(pk=spy.pk).update(surveilling=None)
        result = "Agent %s ceases the surveillance." % spy.name
    return {'result': result, 'img': img}


def counter(nation, spy):
    img = ''
    cost = nation.gdp/30
    if spy.infiltration < 10:
        result = "Agent does not have enough infiltration!"
    elif nation.budget < cost:
        result = "You do not have the funding for this!"
    else:
        Nation.objects.filter(user=nation.user).update(budget=F('budget') - cost)
        strength = spy.experience + spy.infiltration - utils.attrchange(nation.stability, 100)
        spyactions = {
            'actioned': {'action': 'set', 'amount': True},
            'infiltration': {'action': 'add', 'amount': utils.attrchange(spy.infiltration, -10)}
        }
        if spy.specialty != "Spy Hunter":
            strength /= 2
        chance = random.randint(-300, 300)
        img = 'spy.jpg'
        count = 0
        for guy in nation.infiltrators.all().exclude(nation=nation):
            chance = random.randint(0, 100)
            nstrength = spy.infiltration + spy.experience
            tstrength = guy.infiltration + guy.experience
            if spy.specialty == "Spy Hunter":
                nstrength = int(1.5 * nstrength)
            if nstrength > tstrength:
                Spy.objects.filter(pk=guy.pk).update(discovered=True, discovered_timestamp=v.now())
                count += 1
        if count > 0:
            result = "We found %s infiltrators!" % count
        else:
            result = "The sweep didn't find any enemy infiltrators."
    return {'result': result, 'img': img}