from nation.models import *
from nation.eventmanager import Event_base, eventhandler
from random import randint
import random
import nation.utilities as utils

# writing new events 101
# Each event has a set of choices
# these choices will include a model and a set of actions
# 
# if the action modifies a variable that might be overflowed
# set the amount to 0 and use __init__ to define the amount and use utils.attrchange()
# 
# the conditions() function determines whether a given nation will recieve the event
# that means including the actual conditions and a chance condition for whether it will be given
# the conditions can use anything related to the nation
# including the event history
# 
# fields() is simply the display order
# 
# 
# if in doubt see other events for a point of reference
#EVENT TOTAL = 11

class Newbie_event(Event_base):
    def __init__(self, nation):
        super(Newbie_event, self).__init__(nation)
        self.choices['military']['actions']['training']['amount'] = utils.attrchange(nation.military.training, 50)
        
        self.choices['qol']['actions']['qol']['amount'] = utils.attrchange(nation.qol, 15)
        self.choices['qol']['actions']['approval']['amount'] = utils.attrchange(nation.approval, 15)
        self.choices['qol']['actions']['literacy']['amount'] = utils.attrchange(nation.approval, 15)

        self.choices['stability']['actions']['stability']['amount'] = utils.attrchange(nation.stability, 40)
        self.description = "%s " % nation.name + self.description
    img = 'newb.jpg' #needs a corresponding image in static/events/
    choices = {
        'military': {
            'model': Military, 
            'actions': {
                    'army': {'action': 'add', 'amount': 5},
                    'training': {'action': 'add', 'amount': 0},
                    'weapons': {'action': 'add', 'amount': 2},
                },
            },
        'economy': { 
            'model': Nation, 
            'actions': {
                    'budget': {'action': 'add', 'amount': 1000},
                },
            },
        'qol': {
            'model': Nation,
            'actions': {
                'approval': {'action': 'add', 'amount': 0},
                'qol': {'action': 'add', 'amount': 0},
                'literacy': {'action': 'add', 'amount': 0},
            },
        },
        'stability': {
            'model': Nation,
            'actions': {
                'stability': {'action': 'add', 'amount': 0},
            },
        },
    }

    tooltips = {
        'military': "Increases your military in size, 5k troops, \
            increases training, and gives the army a boost in military equipment.",
        'economy': "Adds $1000k to your budget.",
        'stability': "Will increase your governments stability.",
        'qol': "Will increase your nations quality of life and approval.",
    }

    buttons = {
        'military': 'A military is necessary to protect people.',
        'stability': 'Cement my rule.',
        'qol': 'Reforms to benefit the people!',
        'economy': 'Money. Just give me lots of money.',
    }

    result = {
        'military': 'Your glorious military will decimate your enemies!',
        'stability': 'All potential counterrevolutionaries are purged',
        'qol': 'Widesweeping reforms benefit the people!',
        'economy': 'Money! More glorious money!',
    }

    description = "has undergone a glorious revolution! Our new leader must now choose \
                 a path forward for the nation. Where will he lead us?"


    def conditions(self, nation):
        return False


    def fields(self):
        return ['military', 'economy', 'stability', 'qol']


eventhandler.register_event('newbie_event', Newbie_event)

class RefugeeEvent(Event_base):
    def __init__(self, nation):
        super(RefugeeEvent, self).__init__(nation)
        self.choices['qol']['actions']['qol']['amount'] = utils.attrchange(nation.qol, -10)
        self.choices['qol']['actions']['approval']['amount'] = utils.attrchange(nation.approval, -20)
        self.choices['reputation']['actions']['reputation']['amount'] = utils.attrchange(nation.reputation, -15)
        self.description = "%s " % nation.name + self.description
        
    img = 'boatpeople.jpg'
    
    choices = {
        'qol': {
            'model': Nation,
            'actions': {
                'approval': {'action': 'add', 'amount': 0},
                'qol': {'action': 'add', 'amount': 0},
            },
        },
        'reputation': {
            'model': Nation,
            'actions': {
                'reputation': {'action': 'add', 'amount': 0},
            },
        },
    }
    buttons = {
        'qol': 'Let them in.',
        'reputation': 'Turn back their boats.',
    }
    
    tooltips = {
        'qol': 'Decreases growth and approval slightly.',
        'reputation': 'Decreases your international reputation.',
    }
    
    result = {
        'qol': 'Your growth takes a slight hit, while government approval sinks as your citizens xenophobia kicks in.',
        'reputation': 'Your global reputation takes a hit as first world liberals accuse your government of inhumanity.',
    }
    
    description = "has become the destination of thousands of refugees fleeing persecution in several neighboring countries.\
                Most arrive in leaky, packed boats. A large portion of your population loudly demands these foreigners be\
                denied entrance, claiming they are putting economic and social strain on the nation.\
                Should we let them in? This might increase our international \
                reputation but will likely result in a decrease in growth as we must now support these penniless refugees.\
                Or we could simply turn their boats away."
                
    def conditions(self, nation):
        chance = 0
        if nation.qol > 60 and nation.stability > 60:
            chance = 5
        #5% chance to trigger if qol and stability are over 60%
        if random.randint(1, 100) < chance:
            return True
        return False        

    def fields(self):
        return ['qol', 'reputation']
        
eventhandler.register_event('refugee_event', RefugeeEvent)
    
class UraniumEvent(Event_base):
    def __init__(self, nation):
        super(UraniumEvent, self).__init__(nation)
        self.description = "%s " % nation.name + self.description
        
    img = 'uranium.jpg'
    apply_instantly = True
    choices = {
        'natactions': {
            'model': Nation,
            'actions': {
                'uranium': {'action': 'add', 'amount': random.randint(1, 7)},
                #'uranium_deposit': {'action': 'add', 'amount': random.randint(1, 7)},
            },
        }
    }

    buttons = {
        'natactions': 'Awesome!',
    }
    
    tooltips = {
        'natactions': 'Gives you 1-7 tons of uranium',
    }
    
    result = {
        'natactions': "It's soo glowy."
    }
    
    description = "has dug up 1 ton of uranium. It'\s seems you have discovered a small deposit \
                of uranium that will last a few months."
                
    def conditions(self, nation):
        if random.randint(1, 1000) < 5:
            return True
        return False
        #which ever is higher, flat 1% or increasing percentage depending on how many mines you have
        #ex. 0.05% per mine so if you have like 39 or lower mines you have 1% chance to trigger. If you have 40-59 you have 2% chance to trigger
        #OR just a flat 1% at all times.
    def fields(self):
        return ['natactions']
        
eventhandler.register_event('uranium_event', UraniumEvent)


class StabilityReset(Event_base):
    def __init__(self, nation):
        super(StabilityReset, self).__init__(nation)
        self.choices['milactions']['actions']['army']['amount'] = (nation.military.army/2 if nation.military.army/2 > 10 else 10)
    apply_instantly = True
    
    img = 'revolution.png'
    
    choices = {
        'nationactions': {
            'model': Nation,
            'actions': {
                'growth': {'action': 'subtract', 'amount': 2},
                'reputation': {'action': 'set', 'amount': 51},
                'stability':  {'action': 'set', 'amount': 51},
                'approval': {'action': 'set', 'amount': 51},
            },
        },
        'milactions': {
            'model': Military,
            'actions': {
                'army': {'action': 'set', 'amount': 10},
            },
        'setactions': {
            'model': Settings,
            'actions': {
                'flag': {'action': 'set', 'amount': 'revolutionflag.png'},
                'donatorflag': {'action': 'set', 'amount': 'none'},
                'portrait': {'action': 'set', 'amount': 'revolutionportrait.jpg'},
                'donatoravatar': {'action': 'set', 'amount': 'none'},
                'anthem': {'action': 'set', 'amount': 'GBQPmSZr1QY'},
            }
        }
        },
    }

    buttons = {}
    tooltips = {}
    result = {}
    
    description = "Recent instability in your country has led to a revolution! You managed \
        to stay in power, but half of the military has deserted"
                
    def conditions(self, nation):
        if random.randint(1, 100) < (50 if nation.stability <= 10 else 0):
            return True
        return False
                
    def fields(self):
        return []

eventhandler.register_event('stability_reset', StabilityReset)


class GDP_Reset(Event_base):
    def __init__(self, nation):
        super(GDP_Reset, self).__init__(nation)
        stealables = ['oilreserves', 'rm', 'mg', 'oil']
        stolen = False
        for resource in stealables:
            if self.nation.__dict__[resource] > 0:
                stolen = True
                self.choices['reset']['actions'][resource]['amount'] = self.nation.__dict__[resource]/2
        if stolen:
            self.description += " and helped themselves to our assets."

    apply_instantly = True

    img = ''
    choices = {
        'reset': {
            'model': Nation,
            'actions': {
                'gdp': {'action': 'set', 'amount': 250},
                'growth': {'action': 'set', 'amount': 10},
                'qol': {'action': 'set', 'amount': 51},
                'healthcare': {'action': 'set', 'amount': 51},
                'stability': {'action': 'set', 'amount': 51},
                'reputation': {'action': 'set', 'amount': 40},
                'approval': {'action': 'set', 'amount': 51},
                'maxgdp': {'action': 'set', 'amount': 250},
                'budget': {'action': 'set', 'amount': 300},
                'literacy': {'action': 'set', 'amount': 51},
                'food': {'action': 'add', 'amount': 200},
                'uranium': {'action': 'set', 'amount': 0},
                'oilreserves': {'action': 'subtract', 'amount': 0},
                'rm': {'action': 'subtract', 'amount': 0},
                'mg': {'action': 'subtract', 'amount': 0},
                'oil': {'action': 'subtract', 'amount': 0},
            }
        },
        'milactions': {
            'model': Military,
            'actions': {
                'chems': {'action': 'set', 'amount': 0},
                'army': {'action': 'set', 'amount': 10},
                'training': {'action': 'set', 'amount': 100},
                'planes': {'action': 'set', 'amount': 0},
                'navy': {'action': 'subtract', 'amount': 0},
                'reactor': {'action': 'set', 'amount': 0},
                'nukes': {'action': 'set', 'amount': 0},
            },
        }
    }

    buttons = {}
    tooltips = {}
    result = {}

    description = "The United Nations decided to intervene in our downward spiraling economy \
        and set us on the right track again. Unfortunately they also dismantled our military"

    def conditions(self, nation):
        if nation.gdp <= 200:
            return True
        return False

    def fields(self):
        return []



eventhandler.register_event('low_gdp_reset', GDP_Reset)

    
class FactoryEvent(Event_base):
    def __init__(self, nation):
        super(FactoryEvent, self).__init__(nation)
        self.choices['FI']['actions']['FI']['amount'] = nation.FI / 2
        self.choices['USpoints']['actions']['us_points']['amount'] = utils.attrchange(nation.us_points, -30)

       
    img = 'nike.jpg'
    
    choices = {
        'FI': {
            'model': Nation,
            'actions': {
                'FI': {'action': 'subtract', 'amount': 0},
                'factories': {'action': 'add', 'amount': 1},
            },
        },
        'USpoints': {
            'model': Nation,
            'actions': {
                'us_points': {'action': 'add', 'amount': 0},
            },
        },
    }
    buttons = {
        'FI': 'Just Do It.',
        'USpoints': 'Reject them.',
    }
    
    tooltips = {
        'FI': 'Will decrease quality of life and remove our foreign investment, but will add a new factory.',
        'USpoints': 'Will lower your US reputation drastically.'
    }
    
    result = {
        'FI': 'A factory is built, giving your economy a boost. Nike sells the shoes for 150% of an annual worker\'s salary to American kids.',
        'USpoints': 'The executives are furious at you for rejecting their offer. Unfortunately for you\
            they have some powerful friends in the US government, your relations with the US drop significantly.',
    }
    
    description = "We have recieved an offer from the Nike corporation to open a new factory in our \
                country due to our pro-business policies."
                
    def conditions(self, nation):
        chance = 0
        if (nation.factories+1)*1000 >= nation.FI and nation.farmland() > nation.landcost('factories'):
            chance = 5
        if random.randint(1, 100) <= chance:
            return True
        return False
        #5% chance if your foriegn investment is at $1000k per factory+ $1000k ex: you have 6 factories you need to have over 7000k foriegn investment. 
    def fields(self):
        return ['FI', 'USpoints']
        
eventhandler.register_event('factory_event', FactoryEvent)

class AsteroidEvent(Event_base):
    def __init__(self, nation):
        super(AsteroidEvent, self).__init__(nation)
        self.choices['gibsoviet']['actions']['soviet_points']['amount'] = utils.attrchange(nation.soviet_points, 25)
        self.choices['gibus']['actions']['us_points']['amount'] = utils.attrchange(nation.us_points, 25)
        self.description = "%s " % nation.name + self.description
       
    img = 'asteroid.jpg'
    
    choices = {
        'gibsoviet': {
            'model': Nation,
            'actions': {
                'budget': {'action': 'add', 'amount': 10000},
                'soviet_points': {'action': 'add', 'amount': 0},
            },
        },
        'gibus': {
            'model': Nation,
            'actions': {
                'budget': {'action': 'add', 'amount': 10000},
                'us_points': {'action': 'add', 'amount': 0},
            },
        },
        'keepit': {
            'model': Military,
            'actions': {
                'weapons': {'action': 'add', 'amount': 50},
            },
        },
    }
    buttons = {
        'gibsoviet': 'Give remains of this "asteroid" to the Soviets.',
        'gibus': 'Hand it off to the Americans.',
        'keepit': 'Keep it for ourselves.',
    }
    
    tooltips = {
        'gibsoviet': 'Will greatly increase your relations with the soviets for returning their asteroid. They\'ll also throw in 10 million bucks for the trouble.',
        'gibus': 'The US will pay you a cool 10 million for this important communist asteroid. Reputation with US will increase.',
        'keepit': 'Studying this asteroid will... somehow... significantly increase our military technology.',
    }
    
    result = {
        'gibsoviet': 'The Soviets graciously hand over a suitcase of cash and ask us to never mention this again.',
        'gibus': 'US asteroid experts pick it up to be stored at the Area 51 Asteroid Museum.',
        'keepit': 'Your researchers were able to understand the technology. and have implemented it. Your military is now much stronger.',
    }
    
    description = "has been the site of an asteroid strike! The location of the landing has \
                    been roped off by the government and truckloads of strange metallic pieces have been sighted being \
                    driven away from the site. In other news, the Soviet Union announced it was postponing its lunar mission for another year... "
                
    def conditions(self, nation):
        #0.1% chance to trigger.
        if random.randint(1, 1000) < 2:
            return True
        else:
            return False
                
    def fields(self):
        return ['gibsoviet', 'gibus', 'keepit']
        
eventhandler.register_event('asteroid_event', AsteroidEvent)
    
class JuntaEvent(Event_base):
    def __init__(self, nation):
        super(JuntaEvent, self).__init__(nation)
        self.choices['army']['actions']['training']['amount'] = utils.attrchange(nation.military.training, 25)
        self.choices['airforce']['actions']['planes']['amount'] = utils.attrchange(nation.military.planes, 2, upper=10)
        self.choices['special']['actions']['chems']['amount'] = utils.attrchange(nation.military.chems, 1, upper=10)
        self.choices['navy']['actions']['navy']['amount'] = utils.attrchange(nation.military.navy, 1)
        self.description = "%s " % nation.name + self.description
       
    img = 'junta.jpg'
    
    choices = {
        'army': {
            'model': Military,
            'actions': {
                'training': {'action': 'add', 'amount': 0},
                'army': {'action': 'add', 'amount': 5},
            },
        },
        'airforce': {
            'model': Military,
            'actions': {
                'planes': {'action': 'add', 'amount': 0},
            },
        },
        'special': {
            'model': Military,
            'actions': {
                'chems': {'action': 'add', 'amount': 0},
            },
        },
        'navy': {
            'model': Military,
            'actions': {
                'navy': {'action': 'add', 'amount': 0},
            },
        },
    }
    buttons = {
        'army': 'General of the Army.',
        'airforce': 'General of the Airforce.',
        'special': 'General of the Special Projects.',
        'navy': 'Admiral of the Navy.',
    }
    
    tooltips = {
        'army': 'Increase army size by 5k, training by a level.',
        'airforce': 'Increases air force size.',
        'special': 'Increases progress towards chemical weapons.',
        'navy': 'Increases navy size.',
    }
    
    result = {
        'army': 'Your army is the pride of the nation.',
        'airforce': 'Your air force is the pride of the nation.',
        'special': 'Your chemical weapons research has increased.',
        'navy': 'Your navy is the pride of the nation.',
    }
    
    description = "has had its top Junta brass convene to discuss the further \
                    development of the nation. Who should be listened to?"
                
    def conditions(self, nation):
        #must be junta political system and has a 5% chance to trigger.
        gov = (nation.government if nation.government > 0 else 1)
        gov = (gov/20 if gov % 20 != 0 else (gov/20)-1)
        chance = (5 if gov == 1 else 0)
        if random.randint(1, 100) <= chance:
            return True
        return False
                
    def fields(self):
        return ['army', 'airforce', 'special', 'navy']
        
eventhandler.register_event('junta_event', JuntaEvent)
    
class RebelsEvent(Event_base):
    def __init__(self, nation):
        super(RebelsEvent, self).__init__(nation)
        self.choices['givein']['actions']['stability']['amount'] = utils.attrchange(nation.stability, -35)
        self.choices['givein']['actions']['approval']['amount'] = utils.attrchange(nation.approval, 15)
        self.choices['dont']['actions']['rebels']['amount'] = utils.attrchange(nation.rebels, 20, 0)
        self.description = "%s " % nation.name + self.description
        
    img = 'rebels.jpg'
    
    choices = {
        'givein': {
            'model': Nation,
            'actions': {
                'stability': {'action': 'add', 'amount': 0},
                'approval': {'action': 'add', 'amount': 0},
                'rebels': {'action': 'set', 'amount': 0},
            },
        },
        'dont': {
            'model': Nation,
            'actions': {
                'rebels': {'action': 'add', 'amount': 0},
            },
        },
    }
    buttons = {
        'givein': 'Give in to demands.',
        'dont': 'Demand they surrender.',
    }
    
    tooltips = {
        'givein': 'Large loss in stability, increase in approval, rebels disband.',
        'dont': 'Large growth in rebel forces. ',
    }
    
    result = {
        'givein': 'The rebels celebrate their victory.',
        'dont': 'The rebels refuse, and more join their cause against your tyrannical demands.',
    }
    
    description = "has thousands revolt against the hated government."
                
    def conditions(self, nation):
        #has terrorist acts (41% and higher) rebels. 5% chance to trigger
        if nation.rebels < 2:
            return False
        if random.randint(1, 100) <= 5:
            return True
        else:
            return False
                
    def fields(self):
        return ['givein', 'dont']
        
eventhandler.register_event('rebels_event', RebelsEvent)
    
class SinglePartyEvent(Event_base):
    def __init__(self, nation):
        super(SinglePartyEvent, self).__init__(nation)
        self.choices['industrial']['actions']['qol']['amount'] = utils.attrchange(nation.qol, -10)
        self.choices['consumer']['actions']['qol']['amount'] = utils.attrchange(nation.qol, 20)
        self.choices['agriculture']['actions']['manpower']['amount'] = utils.attrchange(nation.manpower, 50)
        self.description = "%s " % nation.name + self.description
        
    img = 'single_party_state.jpg'
    
    choices = {
        'industrial': {
            'model': Nation,
            'actions': {
                'qol': {'action': 'add', 'amount': 0},
                'growth': {'action': 'add', 'amount': 10},
            },
        },
        'consumer': {
            'model': Nation,
            'actions': {
                'qol': {'action': 'add', 'amount': 0},
                'growth': {'action': 'add', 'amount': 2},
            },
        },
        'agriculture': {
            'model': Nation,
            'actions': {
                'manpower': {'action': 'add', 'amount': 0},
                'growth': {'action': 'subtract', 'amount': 5},
            },
        },
    }
    buttons = {
        'industrial': 'Produce heavy industry.',
        'consumer': 'Produce consumer goods.',
        'agriculture': 'Increase agricultural production.',
    }
    
    tooltips = {
        'industrial': 'Increase economic growth by $10 million, decreases Quality of Life slightly ',
        'consumer': 'Increase Quality of Life, increase in growth by $2 million.',
        'agriculture': 'Greatly increases manpower, slight decrease to Quality of Life and a drop in growth of $5 million.',
    }
    
    result = {
        'industrial': 'Growth is greatly increased.',
        'consumer': 'Growth and Quality of Life increases as your people enjoy their new appliances.',
        'agriculture': 'Manpower is greatly increased at the expensive of economic growth.',
    }
    
    description = "has had the ruling Party apparatchiks meet to discuss next years economic focus."
                
    def conditions(self, nation):
        #must be single state party. has 5% chance to trigger.
        if not (nation.government > 40 and nation.government <= 60):
            return False
        if random.randint(1, 100) <= 5:
            return True
        else:
            return False
                
    def fields(self):
        return ['industrial', 'consumer', 'agriculture']
        
eventhandler.register_event('singleparty_event', SinglePartyEvent)
    
class EArtistEvent(Event_base):
    def __init__(self, nation):
        super(EArtistEvent, self).__init__(nation)
        self.choices['labor']['actions']['approval']['amount'] = utils.attrchange(nation.approval, -20)
        self.choices['labor']['actions']['stability']['amount'] = utils.attrchange(nation.stability, 10)
        self.choices['labor']['actions']['government']['amount'] = utils.attrchange(nation.government, 20)
        self.choices['slap']['actions']['stability']['amount'] = utils.attrchange(nation.stability, -20)
        self.choices['apologize']['actions']['approval']['amount'] = utils.attrchange(nation.approval, 10)
        self.choices['apologize']['actions']['stability']['amount'] = utils.attrchange(nation.stability, -15)
        self.choices['apologize']['actions']['government']['amount'] = utils.attrchange(nation.government, 20)
        self.description = "%s " % nation.name + self.description
       
    img = 'edgy_artist.jpg'
    
    choices = {
        'labor': {
            'model': Nation,
            'actions': {
                'approval': {'action': 'add', 'amount': 0},
                'stability': {'action': 'add', 'amount': 0},
                'government': {'action': 'add', 'amount': 0},
            },
        },
        'slap': {
            'model': Nation,
            'actions': {
                'stability': {'action': 'add', 'amount': 0},
            },
        },
        'apologize': {
            'model': Nation,
            'actions': {
                'approval': {'action': 'add', 'amount': 0},
                'stability': {'action': 'add', 'amount': 0},
                'government': {'action': 'add', 'amount': 0},
            },
        },
    }
    buttons = {
        'labor': 'Hard labor for a decade.',
        'slap': 'Slap on the wrist.',
        'apologize': 'Apologize and release.',
    }
    
    tooltips = {
        'labor': 'Will increase stability as people are less likely to challenge the government out of fear, but decreases approval and makes the government more authoritarian.',
        'slap': 'Decrease in stability as dissidents fear the government less.',
        'apologize': 'Increases approval but decreases stability somewhat as the government is now seen to tolerate openly dissent. Government becomes more democratic.',
    }
    
    result = {
        'labor': 'The malcontent is sent to pay for his crime and be forgotten by everyone else.',
        'slap': 'The dissidents in the nation become enboldened by the lack of punishment.',
        'apologize': 'A new sense of freedom sweeps over the nation as many gladly criticize the government.',
    }
    
    description = "has had a memorial to our brave soldiers defaced by a so-called artist, demanding \
                    greater freedoms and civil rights. Our state police forces have arrested the criminal \
                    and he awaits trial. What is to be done with him?"
                
    def conditions(self, nation):
        #must be single party or authoritarian democracy political system and has a 5% chance to trigger.
        if not (nation.government > 40 and nation.government <= 80):
            return False
        if random.randint(1, 100) <= 5:
            return True
        else:
            return False
                
    def fields(self):
        return ['labor', 'slap', 'apologize']

eventhandler.register_event('eartist_event', EArtistEvent)


class RiotsEvent(Event_base):
    def __init__(self, nation):
        super(RiotsEvent, self).__init__(nation)
        self.choices['crush']['actions']['stability']['amount'] = utils.attrchange(nation.stability, 20)
        self.choices['crush']['actions']['reputation']['amount'] = utils.attrchange(nation.reputation, -20)
        self.choices['crush']['actions']['government']['amount'] = utils.attrchange(nation.government, -10)
        self.choices['promise']['actions']['approval']['amount'] = utils.attrchange(nation.approval, 5)
        self.description = "%s " % nation.name + self.description
        
    img = 'riots.jpg'
    choices = {
        'crush': {
            'model': Nation,
            'actions': {
                'stability': {'action': 'add', 'amount': 0},
                'reputation': {'action': 'add', 'amount': 0},
                'government': {'action': 'add', 'amount': 0},
            },
        },
        'promise': {
            'model': Nation,
            'actions': {
                'approval': {'action': 'add', 'amount': 0},
            },
        },
    }
    buttons = {
        'crush': 'Send in the army, brutally crush these vandals.',
        'promise': 'Promise future reforms.',
    }
    
    tooltips = {
        'crush': 'Stability will rise, but your government will become significantly more authoritarian and will lose reputation.',
        'promise': 'Approval increases slightly.',
    }
    
    result = {
        'crush': 'The army spares no protestors and order is restored.',
        'promise': 'Your people await their reforms.',
    }
    
    description = "has undergone widespread anti-government riots. Further protests are planned. What should we do?"
                
    def conditions(self, nation):
        #if stability below 40% has a 5% chance to trigger.
        if nation.stability < 40 and random.randint(1, 100) <= 5:
            return True
        else:
            return False
                
    def fields(self):
        return ['crush', 'promise']
        
eventhandler.register_event('riots_event', RiotsEvent)

    
class UNInterventionEvent(Event_base):
    def __init__(self, nation):
        super(UNInterventionEvent, self).__init__(nation)
        self.choices['milactions']['actions']['navy']['amount'] = utils.attrchange(nation.military.navy, -4)
        self.description = "%s " % self.description + nation.name
        
    apply_instantly = True
    
    img = 'united_nations.jpg'
    
    choices = {
        'nationactions': {
            'model': Nation,
            'actions': {
                'growth': {'action': 'set', 'amount': 2},
                'uranium': {'action': 'set', 'amount': 0},
                'reputation': {'action': 'set', 'amount': 51},
                'stability':  {'action': 'set', 'amount': 51},
                'qol': {'action': 'set', 'amount': 51},
            },
        },
        'milactions': {
            'model': Military,
            'actions': {
                'chems': {'action': 'set', 'amount': 0},
                'army': {'action': 'set', 'amount': 10},
                'training': {'action': 'set', 'amount': 100},
                'planes': {'action': 'set', 'amount': 0},
                'navy': {'action': 'subtract', 'amount': 0},
                'reactor': {'action': 'set', 'amount': 0},
                'nukes': {'action': 'set', 'amount': 0},
            },
        'setactions': {
            'model': Settings,
            'actions': {
                'flag': {'action': 'set', 'amount': 'interventionflag.png'},
                'donatorflag': {'action': 'set', 'amount': 'none'},
                'portrait': {'action': 'set', 'amount': 'interventionportrait.jpg'},
                'donatoravatar': {'action': 'set', 'amount': 'none'},
            }
        }
        },
    }
    buttons = {}
    
    tooltips = {}
    
    result = {}
    
    description = "The United Nations has arrested you for the atrocities you have committed.\
                They have dismantled your military and have occupied your capital city"
                
    def conditions(self, nation):
        chance = 0
        if nation.reputation > 10 and nation.reputation <= 20:
            chance = 10
        elif nation.reputation <= 10:
            chance = 50
        if random.randint(1, 100) < chance:
            return True
        #if reputation is mad dog (11-20) 10% chance to trigger, elseif reputation is axis of evil(0-10) 50% chance to trigger.
        return False
                
    def fields(self):
        return []
        
eventhandler.register_event('UNInterventionEvent', UNInterventionEvent)