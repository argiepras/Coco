from django.db import transaction
from django.db.models import Q
from django.utils import timezone
import variables as v
from django.contrib.auth.models import User
from nation.models import *
from django.core.paginator import *

import random
import string


def timedeltadivide(timediff):
    'Splits a timedelta into h:m:s.'
    timedeltaseconds = timediff.seconds
    hours, remainder = divmod(timedeltaseconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    minutes = str(minutes).zfill(2)
    seconds = str(seconds).zfill(2)
    return hours, minutes, seconds

def attrchange(current, amount, limit=0):
    if current + amount > 100: #return the amount required to reach 100 and limit respectively
        return amount - (current + amount - 100)
    elif current + amount < limit:
        return amount - (current + amount)
    return amount


def planechange(current, amount):
    if current + amount > 10: 
        return amount - (current + amount)
    elif current + amount < 0:
        return amount - (current + amount)
    return amount


def atomic_transaction(modeltype, pk, actions, targetpk=False):
    with transaction.atomic():
        updatelist = []
        if targetpk:
            subject = modeltype.objects.select_for_update(nowait=True).get(pk=pk)
            target = modeltype.objects.select_for_update(nowait=True).get(pk=targetpk)
            #first we do stuff
            for field in actions:
                if actions[field]['action'] is 'subtract':
                    target.__dict__[field] -= actions[field]['amount']
                    subject.__dict__[field] += actions[field]['amount']
                else:
                    target.__dict__[field] += actions[field]['amount']
                    subject.__dict__[field] -= actions[field]['amount']
                #then we assemble a list of fields to update
                updatelist.append(field)
            target.save(update_fields=updatelist)
        else:
            subject = modeltype.objects.select_for_update(nowait=True).get(pk=pk)
            for field in actions:
                if actions[field]['action'] is 'subtract':
                    subject.__dict__[field] -= actions[field]['amount']
                elif actions[field]['action'] is 'add':
                    subject.__dict__[field] += actions[field]['amount']
                else:
                    subject.__dict__[field] = actions[field]['amount']
                #then we assemble a list of fields to update
                updatelist.append(field)
        subject.save(update_fields=updatelist)


def research(rtype, tier):
    if tier == 0:
        return 1
    else:
        return 1 + tier * v.researchbonus[rtype]


def can_attack(nation, target):
    if target.vacation:
        reason = "This nation is inactive!"
    elif War.objects.filter(attacker=nation, over=False).exists():
        reason = "You are already attacking someone!"
    elif War.objects.filter(Q(attacker=nation, defender=target)|Q(attacker=target, defender=nation), over=False).exists():
        reason = "We are already at war!"   
    elif not regioncheck(nation, target):
        reason = "This nation is not within our power projection range!"
    elif nation.gdp*2 < target.gdp:
        reason = "This nation is too strong to attack!"
    elif nation.gdp*0.75 > target.gdp:
        reason = "This nation is too weak to attack!"
    elif nation == target:
        reason = "You can't attack yourself!"
    elif War.objects.filter(attacker=nation, over=True).exists():
        reason = "You have already declared war once in the last 2 months!"
    elif target.protection > timezone.now():
        reason = "They have recently lost a war and are recovering!"
    elif nation.protection > timezone.now():
        reason = "We have recently lost a war"
    elif War.objects.filter(defender=target, over=False).exists():
        reason = "They are already fighting a defensive war!"
    else:
        reason = ''
    if reason:
        return False, reason
    return True, reason





def regioncheck(nation, target):
    navy = nation.military.navy
    attackrange = (2 + (navy/v.rangethreshold)*v.rangebonus if navy < 50 else 25)
    targetnumber = v.regions[target.region()][target.subregion]
    nationnumber = v.regions[nation.region()][nation.subregion]
    if targetnumber > nationnumber:
        if nationnumber + attackrange >= targetnumber:
            return True
    elif targetnumber < nationnumber:
        if nationnumber - attackrange <= targetnumber:
            return True
    else: #same subregion
        return True
    return False


def pagination(paginator, page):
    pages = []
    if paginator.num_pages <= 5:
        for number in paginator.page_range:
            pages.append({'page': number})
    else:
        if page.number - 2 <= 1: #page 1, 2 or 3
            for number in xrange(1, 6):
                pages.append({'page': number})
        else:
            for number in xrange(page.number - 2, page.number + 3):
                pages.append({'page': number})
    return pages



def firstsetup(testing=False):
    ID.objects.create()
    Market.objects.create()
    if testing:
        User.objects.create(username="admin", password="admin")
        regions = []
        for region in v.regionshort:
            regions.append(region)
        for x in range(100):
            user = User.objects.create(username=''.join(random.choice(string.ascii_letters) for _ in range(6)))
            region = v.regionshort[regions[random.randint(0, len(regions) - 1)]]
            testey = Nation.objects.create(
                user=user,
                name=''.join(random.choice(string.ascii_letters) for _ in range(10)),
                creationip="127.0.0.1",
                government=random.randint(0,100),
                economy=random.randint(0, 100),
                subregion=region,
            )
            Settings.objects.create(nation=testey)
            Military.objects.create(nation=testey)
            Econdata.objects.create(nation=testey)
            Researchdata.objects.create(nation=testey)


def landcheck(nation, loss):
    close = {}
    closables = ['mines', 'wells', 'factories', 'universities']
    if nation.farmland() - loss < 0:
        for closable in closables:
            count = 0
            while nation.__dict__[closable] > 0:
                nation.__dict__[closable] -= 1
                nation.__dict__['closed_%s' % closable] += 1
                count += 1
                if nation.farmland() - loss > 0:
                    break
            close.update({
                'closable': {'action': 'subtract', 'amount': count},
                'closed_%s' % closable: {'action': 'add', 'amount': count},
            })
            if nation.farmland() > 0:
                return close

    return False


def get_player(ID):
    nation = False
    try:
        nation = Nation.objects.get(index=ID)
    except:
        pass
    try:
        nation = Nation.objects.get(name=ID)
    except:
        pass
    try:
        nation = Nation.objects.get(user__username=ID)
    except:
        pass
    return nation

def get_active_player(ID):
    nation = False
    query = Nation.objects.filter(vacation=False, deleted=False)
    try:
        nation = query.get(index=ID)
    except:
        pass
    try:
        nation = query.get(name=ID)
    except:
        pass
    try:
        nation = query.get(user__username=ID)
    except:
        pass
    return nation


def paginate_me(query, count, page):
    paginator = Paginator(query, count)
    page = int(page)
    try:
        listofstuff = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        listofstuff = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        listofstuff = paginator.page(paginator.num_pages)

    return paginator, listofstuff