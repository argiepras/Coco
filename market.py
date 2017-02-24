from django.shortcuts import render, redirect
from .models import *
from .forms import *
from django.contrib.auth.decorators import login_required
from .decorators import nation_required
from . import utilities as utils
from django.db.models import Q
from django.core.paginator import *
from django.db import transaction
import datetime as time
# Create your views here.


@login_required
@nation_required
def free_market(request):
    nation = request.user.nation
    econ = nation.economy
    econ = econ/33
    econ = (2 if econ > 2 else econ)
    context = {}
    result = False
    if request.method == 'POST':
        post = request.POST.dict()
        actions = {}
        with transaction.atomic():
            market = Market.objects.select_for_update().latest('pk')
            for field in post:
                if len(field.split('_')) == 2:
                    action, resource = field.split('_')
                    amount = post[field]
            amount = int(amount)
            pricevar = '%sprice' % resource
            price = market.__dict__[pricevar]
            countervar = '%s_counter' % resource
            counter = market.__dict__[countervar]
            threshold = market.threshold
            try:
                log = Marketlog.objects.get(nation=nation, turn=market.pk, resource=resource)
            except:
                log = Marketlog.objects.create(nation=nation, turn=market.pk, resource=resource)
            if action == 'buy':
                cost = int(price * v.marketbuy[econ]) * amount
                if nation.budget < cost:
                    result = "You cannot afford this! You need $%sk more!" % (cost - nation.budget)
                else:
                    if amount + counter < market.threshold : #doesn't move price
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



def offers(request, page):
    context = {}
    nation = request.user.nation
    if request.method == 'POST':
        if 'postoffer' in request.POST:
            form = offerform(request.POST)
            if form.is_valid():
                nation.offers.create(content=form.cleaned_data['offer'])
                result = "Offer made!"
            else:
                result = form.errors
            context.update({'result': result})
    offers = Marketoffer.objects.select_related('nation', 'nation__settings').all().order_by('-pk')
    paginator = Paginator(offers, 10)
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
        'offerform': offerform(),
        'pages': utils.pagination(paginator, offerlist)
        })
    return render(request, 'nation/marketoffers.html', context)