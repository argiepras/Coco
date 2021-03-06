from django.db import transaction
from django.db.models import Sum, Q
from django.utils import timezone
import variables as v
from django.contrib.auth.models import User
from django.core.paginator import *

import random
import string

from nation.models import Nation


def timedeltadivide(timediff):
    'Splits a timedelta into h:m:s.'
    timedeltaseconds = timediff.seconds
    hours, remainder = divmod(timedeltaseconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    minutes = str(minutes).zfill(2)
    seconds = str(seconds).zfill(2)
    return hours, minutes, seconds


def attrchange(current, amount, lower=0, upper=100):
    if current + amount > upper: #return the amount required to reach 100 and lower respectively
        return upper - current
    elif current + amount < lower:
        return lower - current
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
                    setattr(
                        target, 
                        field, 
                        getattr(target, field) - actions[field]['amount']
                    )
                    setattr(
                        subject, 
                        field, 
                        getattr(subject, field) + actions[field]['amount']
                    )
                else:
                    setattr(
                        target, 
                        field, 
                        getattr(target, field) + actions[field]['amount']
                    )
                    setattr(
                        subject, 
                        field, 
                        getattr(subject, field) - actions[field]['amount']
                    )
                #then we assemble a list of fields to update
                updatelist.append(field)
            target.save(update_fields=updatelist)
        else:
            subject = modeltype.objects.select_for_update(nowait=True).get(pk=pk)
            for field in actions:
                if actions[field]['action'] is 'subtract':
                    setattr(
                        subject, 
                        field, 
                        getattr(subject, field) - actions[field]['amount']
                    )
                elif actions[field]['action'] is 'add':
                    setattr(
                        subject, 
                        field, 
                        getattr(subject, field) + actions[field]['amount']
                    )
                elif actions[field]['action'] is 'call':
                    subject.__dict__[field]()
                else:
                    setattr(
                        subject, 
                        field, 
                        actions[field]['amount']
                    )
                #then we assemble a list of fields to update
                #except for property fields
                #properties can't be saved to the database
                #but they're prefixed with _
                if 'property' in str(type(getattr(subject.__class__, field))):
                    field = '_%s' % field
                updatelist.append(field)
        subject.save(update_fields=updatelist)


def research(rtype, tier):
    return float(tier) * v.researchbonus[rtype]


def can_attack(nation, target):
    if target.vacation:
        reason = "This nation is inactive!"
    elif nation.offensives.filter(over=False).exists():
        reason = "You are already attacking someone!"
    elif nation.offensives.filter(defender=target, over=False).exists() or nation.defensives.filter(attacker=target, over=False).exists():
        reason = "We are already at war!"   
    elif not regioncheck(nation, target):
        reason = "This nation is not within our power projection range!"
    elif nation.gdp*2 < target.gdp:
        reason = "This nation is too strong to attack!"
    elif nation.gdp*0.75 > target.gdp:
        reason = "This nation is too weak to attack!"
    elif nation == target:
        reason = "You can't attack yourself!"
    elif nation.offensives.filter(over=True).exists():
        reason = "You have already declared war once in the last 2 months!"
    elif target.protection > timezone.now():
        reason = "They have recently lost a war and are recovering!"
    elif target.defensives.filter(over=False).exists():
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



def reset():
    #this one resets all nation related attributes
    #and deletes non-log stuff
    Nation.objects.all().update(
        name='',
        gdp=300,
        budget=1000,
        trade_balance=0,
        _approval=51,
        _stability=51,
        _literacy=51,
        _healthcare=51,
        _qol=51,
        growth=5,
        rebels=0,
        _reputation=51,
        _government=50,
        _economy=50,
        land=30000,
        oil=15,
        rm=30,
        mg=0,
        FI=0,
        food=100,
        uranium=0,
        _soviet_points=0,
        _us_points=0,
        mines=3,
        closed_mines=0,
        wells=0,
        closed_wells=0,
        factories=0,
        closed_factories=0,
        _manpower=100,
        alignment=2,
        research=0,
        universities=0,
        reset=True,
        alliance=None,
        )
    Military.objects.all().update(
        army=20,
        navy=0,
        planes=0,
        training=50,
        weapons=10,
        chems=0,
        reactor=0,
        nukes=0,
        )
    Researchdata.objects.all().update(
        miningtech=0,
        oiltech=0,
        foodtech=1,
        urbantech=0,
        industrialtech=0,
        prospecttech=0,
        )
    Econdata.objects.all().update(
        prospects=0,
        labor=1,
        nationalize=False,
        diamonds=1,
        drugs=1,
        expedition=False,
        cedes=0,
        foodproduction=100,
        )
    ID.objects.all().update(turn=1)
    War.objects.all().delete()
    Warlog.objects.all().delete()
    #deleting alliances triggers cascading deletions on invites/applications/chats/decs/permissions
    Alliance.objects.all().delete()
    Event.objects.all().delete()
    Aid.objects.all().delete()
    Loginlog.objects.all().delete()
    Logoutlog.objects.all().delete()
    Aidlog.objects.all().delete()
    Actionlog.objects.all().delete()
    Eventhistory.objects.all().delete()
    Declaration.objects.all().delete()
    Market.objects.all().delete()
    Marketlog.objects.all().delete()
    Market.objects.create()
    Marketoffer.objects.all().delete()
    Marketofferlog.objects.all().delete()
    Spy.objects.all().delete()
    Extradition_request.objects.all().delete()
    for n in Nation.objects.all():
        n.news.create(event=True, content='newbie_event', deletable=False)


#used in the mod section to keep track of what mods have viewed
def pagecheck(nation, target, pagename):
    #check if entry exists and if so, update timestamp
    #to avoid multiple entries in the database with repeated viewings
    #don't need the same person to be placed in 10 times
    if nation.mod_views.filter(timestamp__gte=v.now() - timezone.timedelta(hours=1), nation=target, page=pagename).exists():
        nation.mod_views.filter(timestamp__gte=v.now() - timezone.timedelta(hours=1), nation=target, page=pagename).update(timestamp=v.now())
    else:
        nation.mod_views.create(nation=target, page=pagename)




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
    return _getplayer(Nation.objects, ID)


def get_active_player(ID):
    return _getplayer(Nation.actives, ID)


def _getplayer(query, ID):
    nation = False
    for item in ['index', 'name__iexact', 'user__username__iexact']:
        try:
            nation = query.get(**{item: ID})
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


def opposing_alignments(nation1, nation2):
    if nation1.alignment + 2 == nation2.alignment or nation1.alignment - 2 == nation2.alignment:
        return True
    return False


def time_to_turns(timestamp):
    x = timezone.now() - timestamp
    

def econsystem(econ):
    if econ < 33:
        return 0
    elif econ < 66:
        return 1
    else:
        return 2


def string_list(iterable, field=False):
    #returns a neatly formatted string from a list
    #ie from ['1', '2', '3', '4'] you'll get
    #'1, 2, 3 and 4'
    #or '1 and 2' from ['1', '2']
    result = ''
    for entry, index in zip(iterable, range(len(iterable))):
        if index+1 == len(iterable):
            mod = ''
        elif index == len(iterable) - 2:
            mod = ' and '
        else:
            mod = ', '
        if field:
            entry = getattr(entry, field)
        result += '%s%s' % (entry, mod)
    return result


def link_me(model):
    return '<a href="%s"><b>%s</b></a>' % (model.get_absolute_url(), model.name)
