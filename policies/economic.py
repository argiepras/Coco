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

    def enact(self):
        chance = random.randint(1, 10)
        if chance > 4:
            self.img = 'glf.jpg'
            self.result = 'You have improved your economic growth! Let a thousand pig irons bloom!'
        elif chance < 2:
            self.gain = {'growth': -1}
            self.result = 'Poor pig iron! Economic growth decreases!'
        else:
            self.result = 'Mediocre pig iron! You have failed to improve economic growth!'
        super(great_leap, self).enact()

    name = 'Great Leap Forward'
    description = "The workers must produce more pig iron! Possibly increase economic growth. \
    Possibly backfire and associate your name with mass death for centuries. Not possible in free market economies."
    button = "Leap"


class reactor(Policy):
    cost = {
        'budget': 5000,
        'uranium': 1,
        'research': 50
    }
    requirements = cost
    name = "Develop Nuclear Reactor"
    button ="Develop"
    description = """Turn that yellow cake into magical electricity. Gives an extra 
        $1 million growth a turn while operational and allows for the 
        peaceful development of nuclear weapons."""

    def extra(self):
        return self.nation.military.reactor < 20

    def enact(self):
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
        super(reactor, self).enact()


class blood(Policy):
    def __init__(self, nation):
        super(blood, self).__init__(nation)
        self.gain = {
            'budget': (nation.gdp/3 if nation.gdp/3 > 100 else 100),
            'qol': -2,
            'reputation': -6,
        }
        self.result = 'Your agent makes the handoff to the de Beers agent in Antwerp and returns \
            with a nice suitcase of $%sk cash.' % self.gain['budget']
        self.description = """Sell tiny stones with a dark past for a lot of money to De Beers. 
            Reputation and quality of life will drop somewhat but will 
            receive $%sk""" % self.gain['budget']
    cost = {'qol': 2, 'reputation': 6}
    requirements = {'qol': 2, 'reputation': 10}
    name = "Blood Diamonds"
    button = "Sell"
    costdesc = "Nothing!"

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
        self.gain = {'budget': (nation.gdp if nation.gdp > 500 else 500)}
        self.low = {'reputation': -25, 'us_points': -20}
        self.description = """Mota, llello... you got it, the Gringos need it. Will give you $%sk, 
        but a high chance of getting caught. If caught it greatly decreases your reputation and 
        relations with the US.""" % self.gain['budget']

    name = "Smuggle drugs into the USA"
    button = "Deal"
    costdesc = "Nothing!"
    def extra(self):
        return self.nation.region() == 'Latin America' and self.nation.econdata.drugs >= 1


    def enact(self):
        Econdata.objects.filter(nation=self.nation).update(diamonds=F('drugs') - 1)
        chance = random.randint(1, 10)
        if chance > 6:
            self.img = "drugs.jpg"
            self.result = 'Your agent makes the handoff to some Cubans in Miami with no problems and returns with a nice suitcase of $$%sk cash.' % self.gain['budget']
        else:
            self.gain = self.low
            self.result = "The coastguard captures your shipment off the Florida coast and you are directly implicated! You are condemned by the American President who goes on to mention something about 'regime change'..."
        super(drugs, self).enact()


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
    name = "Forced Collectivization"
    button = "Grow"
    costdesc = "Reduction in stability and approval."
    description = """Liberate the peasants by burning down their homes, seizing their crops 
    and forcing them into giant barracks! Signficantly decreases approval and stability, has 
    a chance of doubling this months agricultural output."""

    def extra(self):
        return self.nation.economy <= 33

    def enact(self):
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
        super(collectivization, self).enact()


class labordiscipline(Policy):
    def __init__(self, nation):
        super(labordiscipline, self).__init__(nation)
        c = nation.factories * 2 * nation.econdata.labor
        self.cost = {
            'oil': (c if nation.region != 'Asia' else int(c*0.75)),
            'rm': (c if nation.region != 'Asia' else int(c*0.75)),
        }
        self.requirements = {'approval': 20, 'factories': 1}
        self.requirements.update(self.cost) #avoids writing the oil/rm dict twice
        self.cost.update({'approval': -10})
        self.gain =  {'mg': nation.factories + mgbonus(nation, nation.factories)} #apply tech bonus
        #add dynamic descriptions so a person can always tell how much they'll get in return
        gain = round(float(self.gain['mg']) / (nation.factories if nation.factories > 0 else 1))
        #don't display decimal points for whole numbers
        gain = (int(gain) if ((gain * 10.0) % 10) == 0 else gain)
        self.description = """The random executions will continue until morale improves. 
        Produces %s ton%s of manufactured goods, %s per factory, but cost rises in oil and 
        raw materials for each time done in a single turn along with a decline in 
        approval. Cost is less in Asia.""" % (self.gain['mg'], ('s' if self.gain['mg'] > 1 else ''), gain)

    result = 'Your people take to the assembly lines!'
    img = "http://i.imgur.com/ZAxmwGG.jpg"
    name = "Labor Discipline"
    button = "Work!"
    def enact(self):
        super(labordiscipline, self).enact()
        Econdata.objects.filter(nation=self.nation).update(labor=F('labor') + 1)


class industrialize(Policy):
    def __init__(self, nation):
        super(industrialize, self).__init__(nation)
        faccos = nation.factories + nation.closed_factories
        self.cost = {
            'rm': faccos * (100 if nation.region() != 'Asia' else 75) + (50 if nation.region() != 'Asia' else 38),
            'oil': faccos * (50 if nation.region() != 'Asia' else 38) + (25 if nation.region() != 'Asia' else 19),
            'mg': faccos * (2 if nation.region() != 'Asia' else 2 * 0.75),
        }
        self.requirements = self.cost
        self.description = """Create a worker's paradise one sweatshop at a time. Builds a factory, 
    which permanently increases growth by $1 million a month as long as it is supplied with 
    1 Mbbl of oil and 1 HTons of raw material. Requires %skm<sup>2</sup> free land""" % nation.landcost('factories')

    contextual = False #always show build industry option
    gain = {'factories': 1}
    name = "Industrialize"
    button = "Progress"

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

    def enact(self):
        self.img = "industry.jpg" 
        self.result = 'Your people take to the assembly lines!'
        super(industrialize, self).enact()


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
    name = "Shut Down Factory"
    costdesc = "Nothing!"
    description = """Well that worker's paradise didn't exactly work out. Removes a factory, 
    costs nothing but decreases approval as unemployment increases.""" 
    button = "Fire"


class reindustrialize(Policy):
    cost = {'closed_factories': 1, 'budget': 1000}
    requirements = cost
    gain = {'factories': 1}
    result = "Thousands rejoice as the factory halls are reopened!"
    name = "Reopen Factory"
    button = "Renovate"
    description = """Grinding up the assembly lines and using them as fertilizer was a great idea, but
            now we need news ones! Re-opens a previously closed factory and increases approval"""


class nationalize(Policy):
    def __init__(self, nation):
        super(nationalize, self).__init__(nation)
        self.cost = {'FI': nation.FI, 'qol': 3, 'stability': 10, 'economy': 50}
        self.gain = {'budget': nation.FI}
        self.description = """Take from the rich yankees what is rightfully yours. 
        Seizure of all foreign investment, $%sk, is added directly to your budget, 
        but alienates the US and moves your nation closer towards the left. 
        Significantly reduces stability.""" % nation.FI

    requirements = {'FI': 20, 'stability': 20, 'qol': 10}
    img = "nationalize.jpg"
    result = "You seize what is yours! Foreign investment added to the budget. Spend it before the next turn or you'll lose it all!"
    name = 'Nationalize Foreign Investment'
    button = 'Steal'
    costdesc = 'Nothing!'
    def extra(self): #base class is not set up for related models
        return self.nation.econdata.nationalize == 0 and utils.econsystem(self.nation.economy) != 0

    def enact(self):
        super(nationalize, self).enact()
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
        self.description = """Sell off state assets to the highest bidder. Will add $%sk to 
        your budget, move you closer to the free market, and reduce your GDP by $%s million. 
        Significantly reduces stability.""" % (self.gain['budget'], self.cost['gdp'])
    
    requirements = {'gdp': 200}

    img = "privatization.jpg"
    name = "Privatize"
    button = "Sell"
    costdesc = "Free!"

    def extra(self):
        return self.nation.econdata.nationalize == 0 and self.nation.economy < 66

    def enact(self):
        super(privatize, self).enact()
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
    name = "Oil Exploration"
    button = "Prospect"
    description = "Punch a bunch of holes in the ground looking for crude. Will discover more oil in the Middle East"
    
    def enact(self):
        super(prospect, self).enact()
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
    name = "IMF Loan"
    button = "Borrow"
    description = "A Faustian Bargain. 100k in cold hard cash for a decrease in growth of $2 million."


class humanitarian(Policy):
    cost = {'budget': 75}
    requirements = cost
    gain = {'growth': 1}
    img = "humanitarian.jpg"
    result = "Your nation's economy has improved slighty!"
    name = "Humanitarian Aid"
    description = "Sometimes we all need a little help. Increases growth, no chance of \
    failure, only available if GDP is below $290 million."
    button = "Beg"

    def extra(self):
        return self.nation.gdp < 290


class foreigninvestment(Policy):
    def __init__(self, nation):
        super(foreigninvestment, self).__init__(nation)
        self.cost = {
            'budget': 75,
            'rm': (nation.growth/6 if nation.growth > 2 else 1)
        }
        self.requirements = self.cost
        self.low = {'FI': (5 if nation.growth <= 5 else nation.growth), 'economy': 1}
        self.gain = {'growth': 1}
        self.gain.update(self.low)

    name = 'Encourage Foreign Investment'
    description = """Invite rich yankees to exploit your cheap labor and resources. 
    Slight chance of increasing economic growth... but the rest could always be 
    nationalized later. Not available to communist countries."""
    button = "Pander"

    def extra(self):
            return utils.econsystem(self.nation.economy) > 0 #no commies allowed

    def enact(self):
        chance = random.randint(1, 10)
        if chance > 7:
            self.result = "Foreign investment pours in which trickles down all over your economy, generating growth!"
            self.img = "foreigninvest.jpg"
        elif chance < 4:
            self.gain = self.low
            self.result = "Foreign investment pours in but unfortunately there is no trickling down on the domestic economy!"
        else:
            self.result = "No one takes up your offer to invest!"
        super(foreigninvestment, self).enact()


class mine(Policy):
    def __init__(self, nation):
        super(mine, self).__init__(nation)
        self.cost = {'budget': (int((250+50*nation.mines)/1.5) if nation.region() == 'Africa' else 250+50*nation.mines)}
        self.requirements = self.cost
        self.description = """Ever play minecraft? It's kinda like that. Will increase raw 
            material production by one hundred tons a month, but is limited by territory with 
            one mine possible per %skm<sup>2</sup>.""" % self.nation.landcost('mines')

    def extra(self):
        return self.nation.farmland() >= self.nation.landcost('mines')

    gain = {'mines': 1}
    img = "mine2.jpg"
    result = "Your new mine increases raw material production by a hundred tons a month."
    name = "Dig Mine"
    button = "Dig"


class privatemine(mine):
    def __init__(self, nation):
        super(privatemine, self).__init__(nation)
        cost = 250+50*nation.mines
        self.cost = {'FI': (cost if nation.region() != 'Africa' else int(cost/1.5))/4}
        self.requirements = self.cost
    gain = {'mines': 1}
    name = "Subsidize Private Mine"
    button = "Offer"
    description = "Offer a foreign corporation some free money to begin mining."

    def extra(self):
        return utils.econsystem(self.nation.economy) > 0 and self.nation.farmland() >= self.nation.landcost('mines')


class closemine(Policy):
    cost = {'approval': 5, 'mines': 1}
    requirements ={'mines': 1, 'approval': 10}
    gain = {'closed_mines': 1}
    img = "closed_mine.jpg"
    result = 'Thousands lose their jobs!'
    name = 'Close Mine'
    button = 'Close'
    costdesc = 'Reduces approval'
    description = "Closes down a mine. Reduces approval as unemployment increases."


class openmine(Policy):
    gain = {'mines': 1, 'approval':  5}
    requirements = {'closed_mines': 1, 'budget': 500}
    cost = requirements
    result = "Previously laid off miners have mixed reactions to the news"
    name = "Reopen Mine"
    button = "Open"
    description = "Reopens a previously closed down mine. Miners will be happy."
    def extra(self):
        return self.nation.farmland() >= self.nation.landcost('mines')


class well(Policy):
    def __init__(self, nation):
        super(well, self).__init__(nation)
        cost = 500+(100*nation.wells)
        self.cost = {'budget': (cost if nation.region() != 'Middle East' else int(cost/1.5))}
        self.requirements = self.cost

    def extra(self):
        return self.nation.farmland() >= self.nation.landcost('wells')

    gain = {'wells': 1}
    img = "oil.jpg"
    result = "Your new well increases oil production by a million barrels a month."
    name = "Drill New Well"
    button = "Drill"
    description = "Drill a new well to increase oil production"


class privatewell(well):
    def __init__(self, nation):
        super(privatewell, self).__init__(nation)
        cost = 500+(100*nation.wells)
        self.cost = {'FI': (cost if nation.region() != 'Middle East' else int(cost/1.5))/4}
        self.requirements = self.cost

    name = "Subsidize Private Well"
    button = "Offer"
    description = "Offer a foreign corporation some free money to begin drilling for oil."
    def extra(self):
        return utils.econsystem(self.nation.economy) > 0 and self.nation.farmland() >= self.nation.landcost('wells')


class closewell(Policy):
    cost = {'approval': 5, 'wells': 1}
    requirements = {'approval': 10, 'wells': 1}
    gain = {'closed_wells': 1}
    img = "http://i.imgur.com/QerllfI.jpg"
    result = "Thousands lose their jobs!"
    name = "Shutdown Well"
    button = "Shutter"
    description = "Closes down a well. Reduces approval as unemployment increases"
    costdesc = "Reduced approval"


class openwell(Policy):
    gain = {'approval':  5, 'wells': 1}
    requirements = {'closed_wells': 1, 'budget': 600}
    cost = requirements
    result = "pending"
    name = "Reopen Well"
    button = "Restore"
    description = "Reopens a previously closed well. Increases approval."
    def extra(self):
        return self.nation.farmland() >= self.nation.landcost('wells')


class forced(Policy):
    def __init__(self, nation):
        super(forced, self).__init__(nation)
        self.cost = {'budget': 50, 'rm': (nation.growth/15 if nation.growth/15 > 0 else 1)}
        self.requirements = {}
        self.requirements.update(self.cost)
        self.cost.update({
            'qol': 5, 
            'reputation': 3,
            'approval':  3,
            })
    gain = {'growth': 1}
    low = {'rebels': 1}
    name = "Forced Labor"
    button = "Force"
    description = """When you want something done right, force people at gunpoint. 
    Increases growth. Small chance of strengthening rebels, will also decrease reputation, 
    approval, stability and quality of life somewhat."""
    def extra(self):
        return self.nation.government <= 20

    def enact(self):
        chance = random.randint(1, 100)
        if chance < 95:
            self.img = 'forced.jpg'
            self.result = 'You have improved your economic growth! Enjoy the fruits of their forced labor.'
        else:
            self.img = "rebel.jpg"
            self.result = "Unfortunately they laborers fled and joined the rebels without doing any work..."
            self.gain = self.low
        super(forced, self).enact()


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

    name = "Special Economic Zone"
    button = "Do it"
    description = """Designate a region of your country where labor laws, minimum wage, and 
    regulations simply do not apply. Increases your growth according the current global market 
    change. Moves you toward the Free Market."""

    def extra(self):
        return self.nation.region() == "Asia" and self.nation.economy <= 66

    def enact(self):
        chance = random.randint(1, 10)
        if chance > 4:
            self.img = 'sez.jpg'
            self.result = "Foreign owned factories pop up throughout the SEZ! Growth increases by the current global market!"
        else:
            self.gain = self.low
            self.result = "Opposition from hardliners stops the creation of an SEZ! Government popularity drops slightly..."
        super(sez, self).enact()