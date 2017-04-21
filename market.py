from django.shortcuts import render, redirect
from .models import *
from .forms import *
from django.contrib.auth.decorators import login_required
from .decorators import nation_required, novacation
from . import utilities as utils
from django.db.models import Q, Sum, Case, When, F, Value, IntegerField, BooleanField
from django.core.paginator import *
from django.db import transaction
import datetime as time
# Create your views here.


@login_required
@nation_required
@novacation
def free_market(request):
    nation = request.user.nation
    econ = nation.economy
    econ = econ/33
    econ = (2 if econ > 2 else econ)
    context = {}
    result = False
    if request.method == 'POST' and not nation.vacation:
        post = request.POST.dict()
        actions = {}
        with transaction.atomic():
            market = Market.objects.select_for_update(nowait=True).latest('pk')
            for field in post:
                if len(field.split('_')) == 2:
                    action, resource = field.split('_')
                    amount = post[field]
            amount = int(amount)
            amount = (amount if amount == 20 or amount == 5 or amount == 1 else 20)
            pricevar = '%sprice' % resource
            price = market.__dict__[pricevar]
            countervar = '%s_counter' % resource
            counter = market.__dict__[countervar]
            threshold = market.__dict__['%s_threshold' % resource]
            log = Marketlog.objects.get_or_create(nation=nation, turn=market.pk, resource=resource)[0]
            if action == 'buy':
                cost = int(price * v.marketbuy[econ]) * amount
                if nation.budget < cost:
                    result = "You cannot afford this! You need $%sk more!" % (cost - nation.budget)
                else:
                    if amount + counter < threshold : #doesn't move price
                        counter += amount
                    else:
                        counter = amount + counter - threshold
                        market.__dict__[pricevar] += 1
                    #set logs an shit, for generating market changes
                    log.cost += cost
                    log.volume += amount
                    log.save()
                    actions.update({
                        resource: {'action': 'add', 'amount': amount},
                        'budget': {'action': 'subtract', 'amount': cost},
                        })
                    result = "You buy %s for $%sk!" % (v.market(amount, resource), cost)

            else: #SELLING :DDDDDDDDDDD
                cost = int(price * v.marketsell[econ]) * amount
                if nation.__dict__[resource] < amount:
                    result = "You do not have %s!" % v.market(amount, resource)
                elif price < 1:
                    result = "The market has already been flooded with %s!" % v.depositchoices[resource]
                else:
                    if counter - amount > 0: #won't move the price
                        counter -= amount
                    else:
                        counter = threshold + counter - amount
                        market.__dict__[pricevar] -= 1
                    log.cost -= cost
                    log.volume -= amount
                    log.save()
                    actions.update({
                        resource: {'action': 'subtract', 'amount': amount},
                        'budget': {'action': 'add', 'amount': cost},
                        })
                    result = "You sell %s for $%sk!" % (v.pretty(amount, resource), cost)

            if actions:
                utils.atomic_transaction(Nation, nation.pk, actions)
                counter = (counter if counter < threshold else threshold/2)
                market.__dict__[countervar] = counter
                market.save()
                nation.refresh_from_db()
    if result:
        context.update({'result': result})
    market = Market.objects.all().latest('pk')
    sellmod = v.marketsell[econ]
    buymod = v.marketbuy[econ]
    context.update({
            'mgbuyprice': int(market.mgprice*buymod),
            'mgsellprice': int(market.mgprice*sellmod),
            'foodbuyprice': int(market.foodprice*buymod),
            'foodsellprice': int(market.foodprice*sellmod),
            'rmbuyprice': int(market.rmprice*buymod),
            'rmsellprice': int(market.rmprice*sellmod),
            'oilbuyprice': int(market.oilprice*buymod),
            'oilsellprice': int(market.oilprice*sellmod),
            'change': market.change,
        })
    return render(request, 'nation/market.html', context)


@login_required
@nation_required
@novacation
def offers(request, page):
    context = {}
    filtered = False
    nation = request.user.nation
    econ = (nation.economy / 33 if nation.economy < 98 else 2)
    offers = Marketoffer.objects.annotate(
        econ=Case(
            When(nation__economy__gt=98, then=Value(2)), 
            When(nation__economy__lt=98, then=F('nation__economy')/33),
            output_field=IntegerField()
                ) #end case
            ).annotate(
                opposite=Case(
                    When(Q(nation__alignment=nation.alignment + 2)|Q(nation__alignment=nation.alignment - 2), then=True),
                    default=False,
                    output_field=BooleanField(),
                        ) #end case
                    ).annotate(
                        tariff=Case(
                            When((Q(nation__alignment=nation.alignment + 2)|Q(nation__alignment=nation.alignment - 2))&(Q(econ=econ + 2)|Q(econ=econ - 2)), then=Value(20)),
                            When((Q(nation__alignment=nation.alignment + 2)|Q(nation__alignment=nation.alignment - 2))|(Q(econ=econ + 2)|Q(econ=econ - 2)), then=Value(10)),
                            default=0,
                            output_field=IntegerField(),
                                ) #end case
                            ).exclude(
                                allow_tariff=False, 
                                tariff__gt=0
                                    ).exclude(
                                        offer='army',
                                        opposite=True,
                                            ).exclude(
                                                nation__econdata__expedition=True,
                                                offer='army',
                                                    ).exclude(
                                                        nation=nation)
    if request.method == 'POST':
        if 'postoffer' in request.POST:
            if nation.offers.all().count() < 10:
                context.update(make_offer(request, nation))
            else:
                context.update({'result': 'You can only have 10 open trades!'})
        elif 'accept_offer' in request.POST:
            if offers.filter(pk=request.POST['accept_offer']).exists():
                tariff = offers.get(pk=request.POST['accept_offer']).tariff
                context.update(accept_offer(request.POST['accept_offer'], nation, tariff))
            else:
                if Marketoffer.objects.filter(pk=request.POST['accept_offer']).exists():
                    context.update({'result': 'That trade is not available to you!'})
                else:
                    context.update({'result': "That trade doesn't exist"})

        elif 'revoke_offer' in request.POST:
            if nation.offers.filter(pk=request.POST['revoke_offer']).delete()[0] > 0:
                context.update({'result': 'Trade has been revoked!'})
            else:
                context.update({'result': 'That trade does not exist!'})

        elif 'filter' in request.POST:
            form = filterform(request.POST)
            if form.is_valid():
                print offers
                offers = offers.filter(offer=form.cleaned_data['offer'])
                if len(offers) == 0:
                    if form.cleaned_data['offer'] == 'army':
                         filtered = "No trades for troops found"
                    else:
                        filtered = "No trades for %s found" % v.depositchoices[form.cleaned_data['offer']].lower()
                    

    paginator = Paginator(offers, 30)
    page = int(page)
    try:
        offerlist = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        offerlist = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        offerlist = paginator.page(paginator.num_pages)
    context.update({
        'offers': offerlist,
        'own_offers': nation.offers.all(),
        'offerform': offerform(),
        'remaining': 10 - nation.offers.all().count(),
        'pages': utils.pagination(paginator, offerlist),
        'filterform': filterform(),
        'filtered': filtered,
        })
    return render(request, 'nation/marketoffers.html', context)


def make_offer(request, nation):
    form = offerform(request.POST)
    if form.is_valid():
        nation.offers.create(**form.cleaned_data)
        return {'result': 'Offer has been posted!'}
    print form.errors
    return {'errors': form.errors}


def accept_offer(offerpk, nation, tariff):
    result = ''
    try:
        with transaction.atomic():
            offer = Marketoffer.objects.select_for_update().get(pk=offerpk)
            buyer, seller = offer.approved(nation)
            if buyer and seller: #if both have the necessary resources for a transfer
                #transfer the offer stuff first
                action = {offer.offer: {'action': 'subtract', 'amount': offer.offer_amount}}
                if offer.offer in nation.__dict__:
                    utils.atomic_transaction(Nation, offer.nation.pk, action)
                    action[offer.offer]['action'] = 'add'
                    utils.atomic_transaction(Nation, nation.pk, action)
                else:
                    utils.atomic_transaction(Military, offer.nation.military.pk, action)
                    action[offer.offer]['action'] = 'add'
                    utils.atomic_transaction(Military, nation.military.pk, action)
                #transfer request stuff
                action = {offer.request: {'action': 'subtract', 'amount': offer.request_amount}}
                if offer.request in nation.__dict__:
                    utils.atomic_transaction(Nation, nation.pk, action)
                    action[offer.request]['action'] = 'add'
                    utils.atomic_transaction(Nation, offer.nation.pk, action)
                else:
                    utils.atomic_transaction(Military, nation.military.pk, action)
                    action[offer.request]['action'] = 'add'
                    utils.atomic_transaction(Military, offer.nation.military.pk, action)
                
                if tariff > 0:
                    selleraction = {
                        'budget': {'action': 'subtract', 'amount': (tariff * offer.offer_amount if offer.offer != 'army' else 10)}
                    }
                    buyeraction = {
                        'budget': {'action': 'subtract', 'amount': (tariff * offer.request_amount if offer.request != 'army' else 10)}
                    }
                    utils.atomic_transaction(Nation, offer.nation.pk, selleraction)
                    utils.atomic_transaction(Nation, nation.pk, buyeraction)
                offer.delete()
                Marketofferlog.objects.create(
                    buyer=nation,
                    seller=offer.nation,
                    sold=offer.offer,
                    bought=offer.request,
                    sold_amount=offer.offer_amount,
                    bought_amount=offer.request_amount,
                    posted=offer.timestamp)
            else:
                if not buyer:
                    result = "You do not have the necessary resources to accept this trade!"
                else:
                    result = "The seller doesn't have the necessary resources to fulfill this offer!\
                                Seller has been fined."
                    utils.atomic_transaction(Nation, offer.nation.pk, {'budget': {'action': 'subtract', 'amount': 50}})
                    offer.delete()

    except Marketoffer.DoesNotExist:
        result = 'This trade is not available!'
    else:
        if not result:
            result = "Trade has been accepted!"
            if tariff > 0:
                result += " $%sk in tariffs has been paid" % (tariff * offer.offer_amount)
    return {'result': result}
