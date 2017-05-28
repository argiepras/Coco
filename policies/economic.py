from .policybase import Policy
import nation.utilities as utils
import random
from nation.turnchange import mgbonus
from django.db.models import F
from nation.models import *


class great_leap(Policy):
    def __init__(self, nation):
        super(great_leap, self).__init__(nation)
        self.cost['rm'] = (nation.growth/3 if nation.growth > 2 else 1)

    cost = {'budget': 100, 'rm': 0}
    requirements = cost
    gain = {'growth': 1, 'economy': -6}

    def extra(self):
        return self.nation.economy <= 66

    def __call__(self):
        chance = random.randint(1, 10)
        if chance > 4:
            self.img = 'glf.jpg'
            self.result = 'You have improved your economic growth! Let a thousand pig irons bloom!'
        elif chance < 2:
            self.gain = {'growth': -1}
            self.result = 'Poor pig iron! Economic growth decreases!'
        else:
            self.result = 'Mediocre pig iron! You have failed to improve economic growth!'
        super(great_leap, self).__call__()


class reactor(Policy):
    cost = {
        'budget': 5000,
        'uranium': 1,
        'research': 50
    }
    requirements = cost

    def extra(self):
        return self.nation.military.reactor < 20

    def __call__(self):
        chance = random.randint(1, 10)
        progress = 0 
        if chance > 4:
            progress = utils.attrchange(self.nation.military.reactor, 1, upper=20)
            self.result += "Progress continues toward a working reactor!"
        elif chance < 2 and self.nation.military.reactor > 1:
            progress = utils.attrchange(self.nation.military.reactor, -1, upper=20)
            self.result = "A stealth bomber has struck your reactor in the middle of construction! Someone doesn't want you getting nuclear weapons... Progress is set back."
        else:
            self.result = "Your nuclear scientists unfortunately fail to make progress..."
        self.nation.military.reactor += progress
        self.nation.military.save(update_fields=['reactor'])
        super(reactor, self).__call__()


class blood(Policy):
    def __init__(self, nation):
        super(blood, self).__init__(nation)
        self.gain = {
            'budget': (nation.gdp if nation.gdp > 500 else 500),
            'qol': -2,
            'reputation': -6,
        }
        self.result = 'Your agent makes the handoff to the de Beers agent in Antwerp and returns with a nice suitcase of $%sk cash.' % self.gain['budget']

    def extra(self):
        return self.nation.region() == 'Africa' and self.nation.econdata.diamonds >= 1


class drugs(Policy):
    """
        Smuggle drugs policy
        gives you either GDP worth of budget (min 500) or loss of rep
        must be latino
    """
    def __init__(self, nation):
        super(drugs, self).__init__(nation)
        self.high = {'budget': (nation.gdp/4 if nation.gdp/4 > 100 else 100)}
        self.low = {'reputation': -25}


    def can_apply(self):
        return self.nation.region() == 'Latin America' and self.nation.econdata.drugs >= 1


    def __call__(self):
        Econdata.objects.filter(nation=self.nation).update(diamonds=F('drugs') - 1)
        chance = random.randint(1, 10)
        if chance > 6:
            self.apply(self.high)
            self.image("drugs.jpg")
            self.result = 'Your agent makes the handoff to some Cubans in Miami with no problems and returns with a nice suitcase of $$%sk cash.' % self.high['budget']
        else:
            self.apply(self.low)
            self.result = "The coastguard captures your shipment off the Florida coast and you are directly implicated! You are condemned by the American President who goes on to mention something about 'regime change'..."


class collectivization(Policy):
    """
        Policy to boost food production by 100% for the turn
        failure decreases by x1 baseline
    """
    cost = {
        'qol': 20,
        'approval': 20,
    }
    requirements = {
        'approval': 30,
        'qol': 30,
    }

    def extra(self):
        return self.nation.economy <= 33

    def __call__(self):
        fp = self.nation.econdata.foodproduction
        chance = random.randint(1, 100)
        if chance > 79:
            fp += utils.attrchange(fp, 100, upper=10000)
            self.img = "collectivization.jpg"
            self.result = 'The grains have never been grainer!'
        elif chance < 11:
            fp += utils.attrchange(fp, -100, upper=10000)
            self.result = 'Your forced collectivization is an utter disaster, reducing your agricultural output, reducing approval and quality of life.'
        else:
            self.result = "Your forced collectivization is a failure, reducing approval and quality of life."
        Econdata.objects.filter(nation=self.nation).update(foodproduction=fp)
        super(collectivization, self).__call__()


class labordiscipline(Policy):
    def __init__(self, nation):
        super(labordiscipline, self).__init__(nation)
        c = nation.factories * 2 * nation.econdata.labor
        self.cost = {
            'oil': c,
            'rm': c,
        }
        self.requirements = {'approval': 20}
        self.requirements.update(self.cost) #avoids writing the oil/rm dict twice
        self.cost.update({'approval': -10})
        self.gain =  {'mg': nation.factories + mgbonus(nation, nation.factories)} #apply tech bonus

    result = 'Your people take to the assembly lines!'
    img = "http://i.imgur.com/ZAxmwGG.jpg"

    def __call__(self):
        super(labordiscipline, self).__call__()
        Econdata.objects.filter(nation=self.nation).update(labor=F('labor') + 1)


class industrialize(Policy):
    def __init__(self, nation):
        super(industrialize, self).__init__(nation)
        self.cost = {
            'rm': nation.factories * (100 if nation.region() != 'Asia' else 75) + (50 if nation.region() != 'Asia' else 38),
            'oil': nation.factories * (50 if nation.region() != 'Asia' else 38) + (25 if nation.region() != 'Asia' else 19),
            'mg': nation.factories * (2 if nation.region() != 'Asia' else 2 * 0.75),
        }
        self.requirements = self.cost

    contextual = False #always show build industry option
    gain = {'factories': 1}

    def can_apply(self):
        nation = self.nation
        rval = False
        if nation.farmland() < nation.landcost('factories'):
            self.result = "You do not have enough unused land!"
        elif nation.oil < self.cost['oil']:
            self.result = "You do not have enough oil!"
        elif nation.rm < self.cost['rm']:
            self.result = "You do not have enough raw material!"
        elif nation.mg < self.cost['mg']:
            self.result = "You do not have enough manufactured goods!"
        else:
            rval = True
        return rval

    def __call__(self):
        self.img = "industry.jpg" 
        self.result = 'Your people take to the assembly lines!'
        super(industrialize, self).__call__()


class deindustrialize(Policy):
    def __init__(self, nation):
        super(deindustrialize, self).__init__(nation)
        self.cost = {'factories': 1}
        self.requirements = {'approval': 10}
        self.requirements.update(self.cost)
        self.cost.update({'approval': 5})

    gain = {'closed_factories': 1}
    img = "http://i.imgur.com/QerllfI.jpg"
    result = "Thousands lose their jobs!"


class reindustrialize(Policy):
    cost = {'closed_factories': 1, 'budget': 1000}
    requirements = cost
    gain = {'factories': 1}
    result = "Thousands rejoice as the factory halls are reopened!"


class nationalize(Policy):
    def __init__(self, nation):
        super(nationalize, self).__init__(nation)
        self.cost = {'FI': nation.FI, 'qol': 3, 'stability': 10, 'economy': 50}
        self.gain = {'budget': nation.FI}

    requirements = {'FI': 20, 'stability': 20, 'qol': 10}
    img = "nationalize.jpg"
    result = "You seize what is yours! Foreign investment added to the budget. Spend it before the next turn or you'll lose it all!"

    def extra(self): #base class is not set up for related models
        return self.nation.econdata.nationalize == 0 and utils.econsystem(self.nation.economy) != 0

    def __call__(self):
        super(nationalize, self).__call__()
        Econdata.objects.filter(nation=self.nation).update(nationalize=1)


class privatize(Policy):
    def __init__(self, nation):
        super(privatize, self).__init__(nation)
        self.gain = { 
            'budget': int((nation.gdp * 0.25 if nation.gdp * 0.25 > 300 else 300)),
            'stability': -15,
            'economy': 40,
        }
        self.cost = {'gdp': (nation.gdp*0.05 if nation.gdp*0.05 > 15 else 15)}
        self.result = "Fire sale! Every social program must go! You get $%sk in the bank." % self.gain['budget']
    
    requirements = {'gdp': 200}

    img = "privatization.jpg"
    def extra(self):
        return self.nation.econdata.nationalize == 0 and self.nation.economy < 66

    def __call__(self):
        super(privatize, self).__call__()
        Econdata.objects.filter(nation=self.nation).update(nationalize=1)


class prospect(Policy):
    def __init__(self, nation):
        super(prospect, self).__init__(nation)
        basecost = ((nation.econdata.prospects**2)*1000)+500
        discovery = (random.randint(1000, 5000) if nation.region() == "Middle East" else random.randint(50, 500))
        discovery += int(discovery * utils.research('prospect', nation.researchdata.prospecttech))
        self.cost = {'budget': (basecost if nation.region() != "Middle East" else basecost/2)}
        self.requirements = self.cost
        self.gain = {'oilreserves': int(discovery)}

    img = 'oil.jpg'

    def __call__(self):
        super(prospect, self).__call__()
        self.result = 'Your exploration reveals %s mmbl of black gold below our otherwise worthless sand dunes.' % self.gain['oilreserves']
        Econdata.objects.filter(nation=self.nation).update(prospects=F('prospects') + 1)
    

class imf(Policy):
    gain = {
        'budget': 100,
        'economy': 6,
        'qol': -1,
    }
    cost = {'growth': 2}
    requirements = {'growth': 1, 'alignment': 1}
    img = 'imf.jpg'
    result = "You take out an IMF loan. Growth decreases as you must now pay off your debt. Spend the loan before the next turn or you'll lose it all!!"


class humanitarian(Policy):
    cost = {'budget': 75}
    gain = {'growth': 1}
    img = "humanitarian.jpg"
    result = "Your nation's economy has improved slighty!"

    def extra(self):
        return nation.gdp < 299 and nation.budget >= 75


class foreigninvestment(Policy):
    def __init__(self, nation):
        super(foreigninvestment, self).__init__(nation)
        self.cost = {
            'budget': 75,
            'rm': (nation.growth/6 if nation.growth > 2 else 1)
        }
        self.low = {'FI': (5 if nation.growth <= 5 else nation.growth),' economy': 1}
        self.gain = {'growth': 1}
        self.gain.update(self.low)

    def can_apply(self):
        if super(foreigninvestment, self).can_apply():
            return utils.econsystem(nation.economy) != 0 #no commies allowed
        return False

    def __call__(self):
        chance = random.randint(1, 10)
        if chance > 7:
            self.result = "Foreign investment pours in which trickles down all over your economy, generating growth!"
            self.img = "foreigninvest.jpg"
        elif chance < 4:
            self.gain = self.low
        else:
            self.result = "No one takes up your offer to invest!"
        super(foreigninvest, self).__call__()


class mine(Policy):
    def __init__(self, nation):
        super(mine, self).__init__(nation)
        self.cost = {'budget': (int((250+50*nation.mines)/1.5) if nation.region() == 'Africa' else 250+50*nation.mines)}
        self.requirements = self.cost

    def can_apply(self):
        if super(mine, self).can_apply():
            return nation.farmland() >= nation.landcost('mines')

    gain = {'mine': 1}
    img = "mine2.jpg"
    result = "Your new mine increases raw material production by a hundred tons a month."


class closemine(Policy):
    cost = {'approval': -5}
    requirements ={'mines': 1, 'approval': 10}
    img = "closed_mine.jpg"
    result = 'Thousands lose their jobs!'


class openmine(Policy):
    gain = {'mine': 1, 'approval':  5}
    requirements = {'closed_mines': 1, 'budget': 500}
    cost = requirements
    result = "Previously laid off miners have mixed reactions to the news"


class privatemine(mine):
    def __init__(self, nation):
        super(privatemine, self).__init__(nation)
        cost = 250+50*nation.mines
        self.cost = {'FI': (cost if nation.region() != 'Africa' else int(cost/1.5))/4}
        self.requirements = self.cost


class well(Policy):
    def __init__(self, nation):
        super(well, self).__init__(nation)
        cost = 500+(100*nation.wells)
        self.cost = (cost if nation.region() != 'Middle East' else int(cost/1.5))
        self.requirements = self.cost

    def can_apply(self):
        if super(well, self).can_apply():
            return nation.farmland() >= nation.landcost('wells')

    gain = {'wells': 1}
    img = "oil.jpg"
    result = "Your new well increases oil production by a million barrels a month."


class privatewell(well):
    def __init__(self, nation):
        super(privatewell, self).__init__(nation)
        cost = 500+(100*nation.wells)
        self.cost = {'FI': (cost if nation.region() != 'Middle East' else int(cost/1.5))/4}
        self.requirements = self.cost


class closewell(Policy):
    cost = {'approval': -5}
    requirements = {'approval': 10, 'wells': 1}
    gain = {'closed_wells': 1}
    img = "http://i.imgur.com/QerllfI.jpg"
    result = "Thousands lose their jobs!"


class openwell(Policy):
    gain = {'approval':  5, 'wells': 1}
    requirements = {'closed_wells': 1, 'budget': 600}
    cost = requirements
    result = "pending"


class forced(Policy):
    def __init__(self, nation):
        super(forced, self).__init__(nation)
        self.cost = {'budget': 50, 'rm': (nation.growth/15 if nation.growth/15 > 0 else 1)}
        self.requirements = self.cost
        self.cost.update({
            'qol': -5, 
            'reputation': -3,
            'approval':  -3,
            })
    gain = {'growth': 1}
    low = {'rebels': 1}

    def can_apply(self):
        if super(forced, self).can_apply():
            return self.nation.government <= 20

    def __call__(self):
        chance = random.randint(1, 100)
        if chance < 95:
            self.img = 'forced.jpg'
            self.result = 'You have improved your economic growth! Enjoy the fruits of their forced labor.'
        else:
            self.img = "rebel.jpg"
            self.result = "Unfortunately they laborers fled and joined the rebels without doing any work..."
            self.gain = self.low
        super(forced, self).__call__()

class sez(Policy):
    def __init__(self, nation):
        super(sez, self).__init__(nation)
        market = Market.objects.all().latest('pk')
        self.cost = {
            'budget': 100,
            'rm': (1 if nation.growth/4 < 1 else nation.growth/4)
        }
        self.requirements = self.cost
        self.gain = {'growth': market.change, 'economy': 2}
        self.low = {'approval': -5}

    def can_apply(self):
        if super(sez, self).can_apply():
            return self.nation.region() == "Asia" and nation.economy <= 66

    def __call__(self):
        chance = random.randint(1, 10)
        if chance > 4:
            self.img = 'sez.jpg'
            self.result = "Foreign owned factories pop up throughout the SEZ! Growth increases by the current global market!"
        else:
            self.gain = self.low
            self.result = "Opposition from hardliners stops the creation of an SEZ! Government popularity drops slightly..."
        super(sez, self).__call__()