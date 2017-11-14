from django.shortcuts import render, redirect
from django.http import JsonResponse
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
    if request.is_ajax():
        return market_action(request)
    nation = request.user.nation
    market = Market.objects.all().latest('pk')
    context = market_prices(market, nation.economy)
    context.update({
            'change': market.change,
            'timestmap': market.last_updated,
        })
    return render(request, 'nation/market.html', context)


@transaction.atomic
def market_action(request):
    print request.POST
    market = Market.objects.select_for_update().latest('pk')
    nation = Nation.objects.select_for_update().get(user=request.user)
    econ = utils.econsystem(nation.economy)
    price_changed = False
    save = True
    returns = {}
    stats = {}
    action, resource = request.POST['action'].split('_')
    amount = int(request.POST['amount'])
    amount = (amount if amount == 20 or amount == 5 or amount == 1 else 20)
    pricevar = '%sprice' % resource
    countervar = '%s_counter' % resource

    price = getattr(market, pricevar)
    counter = getattr(market, countervar)
    threshold = getattr(market, '%s_threshold' % resource)

    log = Marketlog.objects.get_or_create(nation=nation, turn=market.pk, resource=resource)[0]
    
    if action == 'buy':
        cost = int(price * v.marketbuy[econ]) * amount
        if nation.budget < cost:
            save = False
            result = "You cannot afford this! You need $%sk more!" % (cost - nation.budget)
        else:
            if amount + counter < threshold : #doesn't move price
                counter += amount
            else:
                counter = amount + counter - threshold
                market.__dict__[pricevar] += 1
                price_changed = True
            #set logs an shit, for generating market changes
            log.cost += cost
            log.volume += amount
            log.save()

            setattr(nation, resource, getattr(nation, resource) + amount)
            nation.budget -= cost
            result = "You buy %s for $%sk!" % (v.market(amount, resource), cost)

    else: #SELLING :DDDDDDDDDDD
        cost = int(price * v.marketsell[econ]) * amount
        if getattr(nation, resource) < amount:
            save = False
            result = "You do not have %s!" % v.market(amount, resource)
        elif price < 1:
            save = False
            result = "The market has already been flooded with %s!" % v.depositchoices[resource]
        else:
            if counter - amount > 0: #won't move the price
                counter -= amount
            else:
                counter = threshold + counter - amount
                market.__dict__[pricevar] -= 1
                price_changed = True
            log.cost -= cost
            log.volume -= amount
            log.save()
            setattr(nation, resource, getattr(nation, resource) - amount)
            nation.budget += cost
            result = "You sell %s for $%sk!" % (v.pretty(amount, resource), cost)

    returns.update({
            'stats': {
                'budget': nation.budget,
                resource: getattr(nation, resource),
            },
            'result': result,
        })

    if price_changed:
        color = ('green' if action == 'buy' else 'red')
        prices = market_prices(market, nation.economy)
        buy = 'buy_%s' % resource
        sell = 'sell_%s' % resource
        returns.update({
                'prices': {
                    buy: {'price': prices[buy], 'color': color},
                    sell: {'price': prices[sell], 'color': color},
                },
            })

    if save:
        counter = (counter if counter < threshold else threshold/2)
        market.__dict__[countervar] = counter
        nation.save(update_fields=['budget', resource])
        market.save(update_fields=[countervar, pricevar])
    return JsonResponse(returns)


def market_prices(market, econ):
    econ = utils.econsystem(econ)
    sellmod = v.marketsell[econ]
    buymod = v.marketbuy[econ]
    return {
        'buy_mg': int(market.mgprice*buymod),
        'sell_mg': int(market.mgprice*sellmod),
        'buy_food': int(market.foodprice*buymod),
        'sell_food': int(market.foodprice*sellmod),
        'buy_rm': int(market.rmprice*buymod),
        'sell_rm': int(market.rmprice*sellmod),
        'buy_oil': int(market.oilprice*buymod),
        'sell_oil': int(market.oilprice*sellmod),
    }


def price_update(request):
    pass


@login_required
@nation_required
@novacation
def offers(request):
    context = {'filterform': filterform(),}
    page = (request.GET['page'] if 'page' in request.GET else 1)
    nation = request.user.nation
    econ = (nation.economy / 33 if nation.economy < 98 else 2)
    offers = Marketoffer.objects.annotate(
        econ=Case(
            When(nation___economy__gt=98, then=Value(2)), 
            When(nation___economy__lt=98, then=F('nation___economy')/33),
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

    if 'offer' in request.GET:
        form = filterform(request.GET)
        if form.is_valid():
            offers = offers.filter(offer=form.cleaned_data['offer'])
            context.update({'filterform': filterform(initial=request.GET)})
            if len(offers) == 0:
                if form.cleaned_data['offer'] == 'army':
                    filtered = "No trades for troops found"
                else:
                    filtered = "No trades for %s found" % v.depositchoices[form.cleaned_data['offer']].lower()
                context.update({'filtered': filtered}) 

    paginator, offerlist = utils.paginate_me(offers, 30, page)
    context.update({
        'offers': offerlist,
        'own_offers': nation.offers.all(),
        'offerform': offerform(),
        'remaining': 10 - nation.offers.all().count(),
        'pages': utils.pagination(paginator, offerlist),
        })
    return render(request, 'nation/marketoffers.html', context)


def make_offer(request, nation):
    form = offerform(request.POST)
    if form.is_valid():
        nation.offers.create(**form.cleaned_data)
        return {'result': 'Offer has been posted!'}
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
