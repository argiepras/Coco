from nation.models import Nation, Econdata, Military, Market
from nation.variables import min_land
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Q, F
from django.db import transaction
from django.utils import timezone

import nation.utilities as utils
import nation.news as news
import nation.variables as v
from nation.forms import ajaxaidform


@login_required
def incoming(request):
    #takes incoming aid requests in AJAX format
    #checks if sender and recipient are even eligible
    #then we either deny the request or hand control to the appropriate function
    if Nation.objects.actives().filter(Q(pk=request.POST['target'])|Q(user=request.user)).exists():
        return delegate(request)
    return JsonResponse({'result': "'no'"})

@transaction.atomic
def delegate(request):
    options = {
        'aid': send_aid,
        'weapons': give_weapons,
        'cede': cede,
        'expedition': expeditionary,
        'uranium': uranium,
        'research': research,
        'nuke': nukes,
    }
    mils = ['nuke', 'weapons', 'expedition']
    if request.POST['action'] in mils:
        Military.objects.select_for_update().filter(Q(nation__user=request.user)|Q(nation__pk=request.POST['target']))
    nation = Nation.objects.select_for_update().get(user=request.user)
    target = Nation.objects.select_for_update().get(pk=request.POST['target'])
    if nation.pk == target.pk:
        return JsonResponse({'result': '"no"'})
    if request.POST['action'] in options:
        args = {'nation': nation, 'target': target, 'POST': request.POST}
        result = options[request.POST['action']](**args)
    else:
        result = {'result': 'NO'}
    return JsonResponse(result)


def send_aid(*args, **kwargs):
    nation = kwargs.pop('nation')
    target = kwargs.pop('target')
    POST = kwargs.pop('POST')
    form = ajaxaidform(nation, POST)
    if form.is_valid():
        resource = form.cleaned_data['resource']
        if resource in v.resources:
            aid_amount = form.cleaned_data['amount']
            if nation.outgoing_aidspam.filter(
                reciever=target, 
                resource=resource, 
                amount=aid_amount, 
                timestamp__gte=v.now() - timezone.timedelta(minutes=10)
                    ).count() > 5:
                return {'result': 'no'}
            market = Market.objects.latest('pk')
            tariff = 0
            if (nation.economy < 33 and target.economy > 66) or (target.economy < 33 and nation.economy > 66):
                tariff += 10
            if (nation.alignment == 3 and target.alignment == 1) or (target.alignment == 3 and nation.alignment  == 1):
                tariff += 10
            if resource != 'budget':
                tariff = aid_amount * tariff
                tb =  market.__dict__['%sprice' % resource] * aid_amount
            else:
                tariff = (int(aid_amount * 0.1) if tariff > 0 else 0)
                tb = aid_amount
            nation.__dict__[resource] -= aid_amount
            target.__dict__[resource] += aid_amount
            nation.trade_balance -= tb
            target.trade_balance += tb
            news.aidnews(nation, target, resource, aid_amount)
            #to decrease clutter, merge aidlogs < 10 minutes old
            #so instead of 2x $9999k aid logs, it's 1x $19998k log
            nation.outgoing_aidspam.create(resource= resource, reciever=target, amount=aid_amount)
            result = "%s has recieved %s!" % (target.name, v.pretty(aid_amount, resource))
            #feeeeees :D
            uf = [resource, 'trade_balance']
            if tariff > 0:
                result += " But the differences between our systems resulted in $%sk in tariffs!" % tariff
                nation.budget -= tariff
                if resource != 'budget':
                    uf.append('budget')
            nation.save(update_fields=uf)
            target.save(update_fields=uf)
            log_aid(nation, target, resource, aid_amount)
            result = {'result': result, 'update': True}
        else:
            result = {'result': '"nvalid resource'}
    else:
        try:
            result = {'result': form.errors.as_data()['amount'][0][0]}
        except:
            result = {'result': '"nvalid resource'}
    return result


def give_weapons(*args, **kwargs):
    nation = kwargs.pop('nation')
    target = kwargs.pop('target')
    if nation.military.weapons < 15:
        result = "We barely have any weapons as it is! We can't give any away!"
    elif utils.opposing_alignments(nation, target):
            result = "We cannot give weapons to nations aligned with the %s!" % v.alignment
    elif nation.military.weapons < 100 and target.military.weapons > 300:
        result = "Our equipment is worthless compared to what they have!"
    else:
        nation.military.weapons -= 5
        target.military.weapons += 5
        nation.military.save(update_fields=['weapons'])
        target.military.save(update_fields=['weapons'])
        if nation.has_alliance() and target.has_alliance():
            if nation.alliance == target.alliance and nation.alliance.initiatives.weapontrade:
                pass
        else:
            nation.reputation -= 2
            nation.save(update_fields=['_reputation'])
        news.sending_weapons(nation, target)
        log_aid(nation, target, 'weapons', 5)
        return {'result': "The weapons are packed in crates and shipped off. The UN didn't seem too happy.",
                'update': True,
            }
    return {'result': result}


def cede(*args, **kwargs):
    nation = kwargs.pop('nation')
    target = kwargs.pop('target')
    if nation.land < 10100:
        result = "You do not have enough land to cede!"
    elif nation.region() != target.region():
        result = "We cannot cede land to a country in a different part of the world!"
    elif nation.stability < 20 or nation.approval < 20:
        result = "The people already hate you! Ceding land might result in your death!"
    elif nation.econdata.cedes == 3:
        result = "We can't cede land more than 3 times a month!"
    else:
        nation.stability -= 10
        nation.approval -= 10
        nation.land -= 100
        nation.save(update_fields=['_stability', '_approval', 'land'])
        target.land += 100
        target.save(update_fields=['land'])
        result = "We cede the land and lose respect of the people!"
        news.ceding_territory(nation, target)
        log_aid(nation, target, 'land', 100)
    return {'result': result}


def expeditionary(*args, **kwargs):
    nation = kwargs.pop('nation')
    target = kwargs.pop('target')
    if nation.econdata.expedition:
        result = "You have already sent an expeditionary force this turn!"
    elif utils.opposing_alignments(nation, target):
        result = "We cannot send troops to nations aligned with the %s!" % v.alignment[target.alignment]
    elif nation.military.army < 10:
        result = "You do not have enough active personnel for this!"
    else:
        nation.military.army -= 10
        target.military.army += 10
        nation.military.save(update_fields=['army'])
        target.military.save(update_fields=['army'])
        Econdata.objects.filter(nation__pk=nation.pk).update(expedition=True)
        news.aidnews(nation, target, 'troops', 10)
        log_aid(nation, target, 'troops', 10)
        result = "10k of our active personnel are shipped off to %s" % target.name
    return {'result': result}


def nukes(*args, **kwargs):
    nation = kwargs.pop('nation')
    target = kwargs.pop('target')
    if nation.military.nukes == 0:
        result = "You have no nukes to send!"
    else:
        nation.reputation -= 50
        nation.save(update_fields=['_reputation'])
        nation.military.nukes -= 1
        target.military.nukes += 1
        nation.military.save(update_fields=['nukes'])
        target.military.save(update_fields=['nukes'])
        news.nukesent(nation, target)
        log_aid(nation, target, 'nukes', 1)
        result = "A nuclear bomb is carefully disgused and transported to %s" % target.name
    return {'result': result}


def research(*args, **kwargs):
    nation = kwargs.pop('nation')
    target = kwargs.pop('target')
    if nation.research < 50:
        return {'result': "stop it"}
    else:
        nation.research -= 50
        target.research += 50
        nation.save(update_fields=['research'])
        target.save(update_fields=['research'])
        news.aidnews(nation, target, 'research', 50)
        log_aid(nation, target, 'research', 50)
    return {'result': "50 research gets transferred to %s!" % target.name, 'update': True}


def uranium(*args, **kwargs):
    nation = kwargs.pop('nation')
    target = kwargs.pop('target')
    if nation.uranium < 1:
        result = "You do not have any uranium!"
    else:
        nation.uranium -= 1
        nation.reputation -= 5
        target.uranium += 1
        nation.save(update_fields=['uranium', '_reputation'])
        target.save(update_fields=['uranium'])
        news.uraniumaid(nation, target)
        log_aid(nation, target, 'uranium', 1)
        result = "You send off the yellow cake to %s" % target.name
    return {'result': result}   


def log_aid(nation, target, resource, amount):
    query = nation.outgoing_aid.filter(
        resource=resource,
        reciever=target,
        timestamp__gte=v.now() - timezone.timedelta(minutes=10))
    if query.exists():
        query.update(amount=F('amount') + amount)
    else:
        nation.outgoing_aid.create(reciever=target, resource=resource, amount=amount)

    #now for action logging
    query = nation.actionlogs.filter(
        action='Sent %s' % resource, 
        timestamp__gte=v.now() - timezone.timedelta(minutes=10))
    if query.exists():
        query.update(amount=F('amount') + 1)
    else:
        nation.actionlogs.create(action='Sent %s' % resource)   