from django.utils import timezone

def now():
    return timezone.now()

def onlineleaders(): #threshold for showing online leaders
    return now() - timezone.timedelta(minutes=10)

#1 day war protection for newbies
def initprotection():
    return now() + timezone.timedelta(hours=24)

def warprotection():
    return now() + timezone.timedelta(hours=72)

resources = ['budget', 'rm', 'oil', 'mg', 'food']

delay = 10 
commlimit = 2

#limit for when economic collapse stability loss kicks in
econcollapse = -33

#hours until autovac mode
inactive_threshold = 168

def inactivedelta():
    return timezone.timedelta(hours=inactive_threshold)

declarationcost = 75

foodproduction = {
    500: 1,
}

#decay of approval, stability*, manpower* and growth*
faminecost = -10

regions = ['Africa', 'South America', 'Arabia', 'Asia']

#minimum buys/sells to move price at the global market
min_threshold = 20
 
#the minimum amount of land a nation can have
minland = 10000

#Flavor text for sending aid
_pretty = {
    'budget': "money",
    'rm': 'Tons of raw materials',
    'oil': 'mbbls of black gold',
    'mg': 'Tons of manufactured goods',
    'food': 'Tons of our best food',
    'troops': 'of our most average servicemen',
    'research': 'units of research',
}

units = {
    'rm': 'tons',
    'oil': 'mbbls',
    'mg': 'tons',
    'food': 'tons',
    'research': 'units',
}

#for free market offers
_marketpretty = {
    'budget': 'money',
    'rm': 'of raw materials',
    'oil': 'of oil',
    'mg': 'of manufactured goods',
    'food': 'of food',
    'army': 'troops',
    'weapons': 'weapons',
    'research': 'of research',
}

def pretty(amount, resource, trade=False):
    if resource == 'budget':
        return "$%sk" % amount
    elif resource == 'troops':
        return "%sk %s" % (amount, (_marketpretty[resource] if trade else _pretty[resource]))
    else:
        unit = ('' if not resource in units else units[resource])
        unit = (unit if amount > 1 else unit[:-1])
        if resource == 'army':
            amount = '%sk' % amount
        return "%s %s %s" % (amount, unit, (_marketpretty[resource] if trade else _pretty[resource]))


def market(amount, resource):
    if resource == 'food':
        return '%s Tons of food' % amount
    return pretty(amount, resource)

depositchoices = {
    'budget': 'Cash',
    'rm': 'Raw Materials',
    'mg': 'Manufactured Goods',
    'oil': 'Oil',
    'food': 'Food',
    'research': 'Research',
}

aidnames = {
    'budget': 'Cash',
    'rm': 'Raw Materials',
    'mg': 'Manufactured Goods',
    'oil': 'Oil',
    'food': 'Food',
    'research': 'Research',
    'troops': 'Troops',
    'nuke': 'Nukes',
}

researchflavor = {
	'foodtech': "The grains have never been grainer!",
	'prospecttech': 'Our scientists discover new ways to tell where plankton died millions of years ago',
	'urbantech': 'Your urban developers discover the latest and greatest research to increase population density!',
	'oiltech': 'Turns out if we pump unwanted toxic chemicals into the ground, we get more of the toxic chemicals we do want!',
	'industrialtech': 'A new gear in assembly lines increases worker production! Worker wages, not so much.',
	'miningtech': "New methods of digging holes in the ground have been discovered, increasing your mine's output..",
}

marketbuy = {
    0: 1.05,
    1: 1.03,
    2: 1.01,
}

marketsell = {
    0: 0.95,
    1: 0.97,
    2: 0.99,
}

agencies = {
    1: 'KGB',
    2: 'ISI',
    3: 'CIA',
}

landmin = 10000

unicost = 1 #mg per turn per uni
researchperuni = 4

specialities = {
    "Terrorist": "Terrorist - Increased chance at terrorism",
    "Intelligence": "Reveals nation's confidential information",
    "Gunrunner": "Gunrunner - Increased chance at arming rebels",
    "Launderer": "Launderer - Increased chance at funding opposition",
    "Agitator": "Agitator - Increased chance at mutiny",
    "Saboteur": "Saboteur - Increased chance at sabotage",
    "Spy Hunter": "Spy Hunter - Increased chance at finding other agents",
    "Assassin": "Assassin - Increased chance at assassinating other agents",
}
 
#chem damage in % of total
chems = {
    'gdp': 0.05,
    'army': 0.05,
}
 
 #instead of if else if else if chains just get the opposite here
opposite = {
    'attacker': 'defender',
    'defender': 'attacker',
 }



#research bonuses
 
researchbonus = {
    'oil': 0.1,
    'rm': 0.1,
    'mg': 0.1,
    'food': 1.0,
    'prospect': 0.1,
    'urbantech': 0.1,
}
 
landorder = ['mines', 'wells', 'factories', 'universities']

#tooltip display text flavor
landflavor = {
    'mines': "of land used by mines",
    'wells': "of land used by oil wells",
    'factories': "of land used by industry",
    'universities': "of land used by universities",
    'farmland': "of land is used for farmland",
 }

landsimple = {
    'mines': "mine",
    'wells': "oil well",
    'factories': "factory",
    'universities': "university",
    'farmland': "of",
 }

landcosts = {
    'mines': 500,
    'wells': 500,
    'factories': 1000,
    'universities': 1000,
}
 
landresearchbonus = ['factories', 'universities']
 
commprefix = {
    'leadership': 'LEADERSHIP COMM',
    'globalcomm': 'GLOBAL COMM',
    'modcomm': 'MOD COMM',
    'unread': 'UNREAD',
    'masscomm': 'ALLIANCE COMM',
}

regionshort = {
    'col': 'Gran Colombia', 'and': 'The Andes', 'bra': 'Brasilia', 'sco': 'Southern Cone',
    'eth': 'Ethiopia', 'nig': 'Nigeria', 'con': 'Congo', 'saf': 'Southern Africa',
    'naf': 'North Africa', 'ara': 'Arabia', 'mes': 'Mesopotamia', 'per': 'Persia',
    'sub': 'The Subcontinent', 'chi': 'China', 'pac': 'Pacific Rim', 'sea': 'Southeast Asia',
}

urlregions = {
    'middle_east': 'Middle East',
    'asia': 'Asia',
    'latin_america': 'Latin America',
    'africa': 'Africa',
}
 
regions = {
    'Asia': {'Pacific Rim': 1, 'Southeast Asia': 2, 'China': 3, 'The Subcontinent': 4},
    'Middle East': {'Persia': 5, 'Mesopotamia': 7, 'Arabia': 7, 'North Africa': 9},
    'Africa': {'Nigeria': 10, 'Ethiopia': 11, 'Congo': 12, 'Southern Africa': 13},
    'Latin America': {'Gran Colombia': 21, 'The Andes': 23, 'Brasilia': 23, 'Southern Cone': 25},
}

africa = ['Nigeria', 'Ethiopia', 'Congo', 'Southern Africa']
latin_america = ['Gran Colombia', 'The Andes', 'Brasilia', 'Southern Cone']
 
rangethreshold = 30
rangebonus = 2
 
rebels = {
    0: 'None',
    1: "Some dissent",
    2: "Terrorist acts",
    3: "Armed clashes",
    4: "Civil War",
}

#hours between initative toggles
initiative_timer = 72

#what news items will display when an initiative can't be paid for
initiative_loss  = {
    'freedom': 'freedom of information',
    'healthcare': 'healthcare',
    'literacy': 'literacy',
    'weapontrade': 'weapon trading',
}


initiativedisplay = {
    #'focus': 'Economic Focus:',
    'healthcare': { 
        'display': 'Healthcare Initiative:',
        'tooltip': 'Decreases costs of building hospitals and developing vaccines \
                    by 50% for all nations in alliance.'
        },
    'literacy': {
        'display': 'Literacy Initative:',
        'tooltip': 'Decreases costs of building schools by 50% for all nations in alliance.'
        },
    'open_borders': {
        'display': 'Open Borders:',
        'tooltip': 'Manpower increases by +1k men a turn, +$2m growth per turn, decreases \
                    stability by -1% per turn for all member states.'
    },
    'freedom': {
        'display': 'Freedom of Information Initiative:',
        'tooltip': '+1 research for all nations in alliance for each university in alliance \
         member states. -1 approval per turn for authoritarian governments.'
    },
    'redistribute': {
        'display': 'Redistribution of Wealth:',
        'tooltip': 'Nations above the average GDP of the alliance lose growth each turn, while \
                    those below it gain growth each turn. Can lose or gain $5 or $3 million \
                    growth per turn depending on how far above or below the average you are. '
    },
    'weapontrade': {
        'display': 'Weapon Trading:',
        'tooltip': 'No reputation loss from the trade of weapons to fellow alliance member states.'
    },
}

 
 
#These are all divisors -1 if % 10 == 0 (no remainder) so 0-10 = 0
approval = {
    0: 'The people are getting the rope',
    1: 'Literally Hitler',
    2: 'Despised',
    3: 'Disliked',
    4: 'Slightly disliked',
    5: 'Indifferent',
    6: 'Liked',
    7: 'Very liked',
    8: 'Revered',
    9: 'Idolized',
}
 
descriptor = {
    0: "The Great Revolutionary Democratic People's Republic of ",
    1: "The Revolutionary Democratic People's Republic of ",
    2: "The Democratic People's Republic of ",
    3: "The Democratic Republic of ",
    4: 'The Republic of ',
}

title = {
	0: 'Dear Leader',
	1: 'Generalissimo',
	2: 'Premier',
	3: 'Prime Minister',
	4: 'President',
}
 
government = {
    0: "Dictatorship",
    1: "Military State",
    2: "Single Party State",
    3: "Authoritarian Democracy",
    4: "Democracy",
}
 
stability = {
    0: "Total Collapse",
    1: "Violent protests in the streets",
    2: "Rioting",
    3: "Peaceful protests",
    4: "Public disapproval",
    5: "Mostly Calm",
    6: "Orderly",
    7: "Stable",
    8: "Secure",
    9: "Unshakable",
}
 
qol = {
    0: "Destitute",
    1: "Stone broke",
    2: "Sprawling slums",
    3: "Below the poverty line",
    4: "Poor",
    5: "Mediocre",
    6: "Average",
    7: "Decent",
    8: "Great",
    9: "First world",
}
 
healthcare = {
    0: "Mass graves",
    1: "Bring out your dead",
    2: "Disease runs rampant",
    3: "Desperate",
    4: "Inadequate",
    5: "Adequate",
    6: "Average",
    7: "Good",
    8: "Above Average",
    9: "Flawless",
}
 
reputation = {
    0: 'Axis of Evil',
    1: 'Mad Dog',
    2: 'Pariah',
    3: 'Isolated',
    4: 'Questionable',
    5: 'Normal',
    6: 'Good',
    7: 'Nice',
    8: 'Angelic',
    9: 'Gandhi-like',
}
 
economy = {
    0: 'Command economy',
    1: 'Mixed economy',
    2: 'Capitalist economy',
}
 
alignment = {
    1: 'Soviet Union',
    2: 'Neutral',
    3: 'United States',
}
 
manpower = {
    0: 'Depleted',
    1: 'Near Depletion',
    2: 'Low',
    3: 'Halved',
    4: 'Plentiful',
    5: 'Untapped',
}
 
#more or less arbitrary number
techlevel = {
    0: 'Sticks and Stones',
    1: 'A Few Muskets and Swords',
    2: "Great War surplus",
    3: "World War Two surplus",
    4: "Korean War surplus",
    5: "Indochina surplus",
    6: "Modern Age",
    7: "Futuristic Technology"
}
 
techlimits = {
    0: 'Sticks and Stones',
    1: 'A Few Muskets and Swords',
    10: "Great War surplus",
    50: "World War Two surplus",
    150: "Korean War surplus",
    300: "Indochina surplus",
    500: "Modern Age",
    1000: "Fururistic Technology",
    2000: "Futuristic Technology",
}
 
training = {
    0: "Mobs of disobedient conscripts",
    1: "Inexperienced",
    2: "Average",
    3: "Cohesive",
    4: "Well Organized",
}
 
airforce = {
    0: 'None',
    1: 'Hot Air Balloons',
    2: 'Biplanes',
    3: 'Biplanes and Zeppelin Gunships',
    4: 'Light Attack Aircraft',
    5: 'Medium Attack Aircraft',
    6: 'Heavy Attack Aircraft',
    7: 'Twin Engine Fighters',
    8: 'Bomber Gunships',
    9: 'Modern Jets and Bombers',
    10: 'Advanced Multirole Aircraft'
}
 
navy = {
    0: 'None',
    10: 'Patrol Class',
    30: 'Frigate Class',
    50: 'Destroyer Class',
    70: 'Cruiser Class',
    100: 'Carrier Group',
}


#action log equivalents
policychoices = {
    'arrest': 'Arrest Opposition',
    'release': 'Release Prisoner',
    'martial': 'Martial Law',
    'elections': 'Hold Election',
    'housing': 'Free Housing',
    'wage': 'Minimum Wage',
    'cult': 'Cult of Personality',
    'school': 'Free schools',
    'university': 'Build University',
    'hospital': 'Free Hospital',
    'medicalresearch': 'Medical Research',
    'freefood': 'Free food',
    'greatleap': 'Great Leap Forward',
    'blood': 'Blood Diamonds',
    'drugs': 'Smuggled Drugs',
    'collectivization': 'Collectivization',
    'labordiscipline': 'Labor Discipline',
    'industrialize': 'Industrialize',
    'deindustrialize': 'Deindustrialize',
    'nationalize': 'Nationalize',
    'privatize': 'Privatize',
    'prospect': 'Prospect',
    'imf': 'IMF Loan',
    'humanitarian': 'Humanitarian Aid',
    'foreigninvestment': 'Foreign Investment',
    'mine': 'Build Mine',
    'closemine': 'Close Mine',
    'privatemine': 'Build Private Mine',
    'well': 'Build Well',
    'closewell': 'Close Well',
    'privatewell': 'Build Private Well',
    'forced': 'Forced Labor',
    'sez': 'Special Economic Zone',
    'praise_ussr': 'Praise USSR',
    'praise_us': 'Praise US',
    'declareneutrality': 'Declare Neutrality',
    'sovietintervention': 'Soviet Intervention',
    'sovietaid': 'Soviet Aid',
    'usintervention': 'US Intervention',
    'usaid': 'US Aid',
    'train': 'Train Troops',
    'conscript': 'Conscript',
    'demobilize': 'Demobilize',
    'attackrebels': 'Attack Rebels',
    'gasrebels': 'Gas Rebels',
    'migs': 'Buy MIGs',
    'manufactureaircraft': 'Build Aircraft',
    'f8': 'buy F8s',
    'chem': 'Develop Chems',
    'reactor': 'Develop Reactor',
    'nuke': 'Build Nuke',
    'aks': 'Buy AKs',
    'm14': 'Buy M14s',
    'presidente': 'Build Presidentes',
    't62': 'Buy T62s',
    'm60': 'Buy M60s',
    'istan': 'Build Istans',
    't90': 'Buy T90s',
    'm1': 'Buy M1s',
    'despot': 'Build Despots',
    'manufacturenavy': 'Build Ship',
}
