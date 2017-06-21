from .policybase import Policy
import random

class conscript(Policy):
    cost = {'growth': 1, 'manpower': 4}
    requirements = cost
    name = "Conscription"
    button = "Draft"
    result = "You conscript thousands of young men into your army."
    description = "Time to serve! Increase size of military at \
    the cost of economic growth, reduction in training and depletion of manpower."

    def enact(self):
        self.nation.military.army += 2
        trainingloss = int((200.0/self.nation.military.army if self.nation.military.army > 0 else 1))
        self.nation.military.training -= (trainingloss if trainingloss > 0 else 1)
        self.nation.military.save(update_fields=['army', '_training'])
        super(conscript, self).enact()


class train(Policy):
    def __init__(self, nation):
        super(train, self).__init__(nation)
        trainingcost = (nation.military.army**2 * nation.military.training**2) / 20000
        trainingcost = (trainingcost if nation.military.army < trainingcost else nation.military.army)
        self.cost = {'budget': trainingcost}
        self.requirements = self.cost

    contextual = False
    name = "Train your Conscripts"
    button = "Train"
    description = "Turn your half-rate peasant army into a mindless killing \
    machine. Cost is relative to the size of your army."

    def extra(self):
        return self.nation.military.army > 0

    def enact(self):
        if not self.can_apply():
            self.result = "You do not have enough money!"
        elif self.nation.military.training == 100:
            self.result = "Your men are the elite of the elite, there is no need to train them further!"
        else:
            self.nation.military.training += 10
            self.nation.military.save(update_fields=['_training'])
            self.img = "train.jpg"
            super(train, self).enact()


class demobilize(Policy):
    name = "Demobilize"
    button = "Fire"
    costdesc = "Nothing!"
    description = "Turn your half-rate peasant army into \
    a mindless killing machine. Cost is relative to the size of your army."
    def extra(self):
        return self.nation.military.army > 5

    def enact(self):
        self.nation.military.army -= 2
        self.nation.military.save()
        if random.randint(1, 10) > 5:
            self.gain = {'growth': 1}
            self.result = "Your soldiers lay down their rifles and \
                        pick up the hammer, boosting the economy."
        else:
            self.result = "Your soldiers lay down their rifles and \
                        pick up the bottle, with no affect on your economy."
        
        super(demobilize, self).enact()


class attackrebels(Policy):
    cost = {'budget': 10, 'rebels': 1}
    requirements = cost
    name = "Attack the rebel scum!"
    button = "Attack"
    description = """Launch an offensive against the rebels. 
    Might suffer casualties. Slight decrease in reputation"""

    def extra(self):
        return self.nation.military.army > 0

    def enact(self):
        chance = random.randint(1, 10)
        if chance > 5:
            self.nation.military.army -= 1
            self.result = "Your forces suffer casualties but they manage to weaken the rebels."
        elif chance < 2:
            self.nation.military.army -= 1
            self.cost.pop('rebels')
            self.result = """Your army is defeated and takes casualties! The 
            rebels make significant gains from their victory and grow in size."""
        else:
            self.result = "Your forces are victorious against the rebels."
        self.nation.military.save(update_fields=['army'])
        super(attackrebels, self).enact()


class gasrebels(Policy):
    def __init__(self, nation):
        super(gasrebels, self).__init__(nation)
        self.cost = {
            'rebels': (nation.rebels*0.25 if nation.rebels*0.25 > 2 else 2),
            'reputation': 15
        }
    requirements = {'rebels': 1}
    name = "Gas the rebel scum!"
    button = "Gas"
    costdesc = "Nothing"
    result = """Your attacks decimate the rebels, forcing what few 
    remain into hiding. However photographs of civilian casualties 
    soon circulate through international media, and foreigners 
    declare you to be a 'monster'."""
    description = """Unleash chemical weapons on your own people 
    for daring to take up arms against you. Will greatly diminish 
    your reputation but will decimate the rebels."""

    def extra(self):
        return self.nation.military.chems == 10


class base_weapons(Policy):
    def extra(self):
        return self.nation.military.weapons < 500


class soviet_weapons(Policy):
    def __init__(self, nation):
        super(soviet_weapons, self).__init__(nation)
        if nation.military.weapons < 500:
            self.weps = 2
            self.cost = {'soviet_points': 8}
            self.name = "AK-47s from the Soviets"
            self.result = "Thousands of AK-47s are airlifted straight to you from Moscow."
            self.description = """Ask for a lot of the finest guns ever wielded by everyone ever. 
                Must have good relations with the Soviets. Slight increase in technology."""
        elif nation.military.weapons < 2000:
            self.weps = 6
            self.cost = {'soviet_points': 16, 'oil': 3}
            self.name = "T-62s from the Soviets"
            self.result = "A couple T-62s arrive on the latest freighter from Odessa"
            self.description = """An old but sturdy main battle tank from the Soviet Union. 
            Will blast the bourgeois pigs to hell and back. Increase in technology."""
        else:
            self.weps = 11
            self.cost = {'soviet_points': 25, 'oil':  10}
            self.name = "T-90 from the Soviet Union"
            self.result = "A couple T-90s arrive on the latest freighter from Odessa"
            self.description = "A powerful, modern tank. Only available to comrades of the Soviet Union. Large increase in technology."
        self.requirements = self.cost

    button = "Ask"
    def extra(self):
        return self.nation.alignment != 3

    def enact(self):
        self.nation.military.weapons += self.weps
        self.nation.military.save(update_fields=['weapons'])
        super(soviet_weapons, self).enact()


class us_weapons(Policy):
    def __init__(self, nation):
        super(us_weapons, self).__init__(nation)
        if nation.military.weapons < 500:
            self.weps = 2
            self.cost = {'us_points': 8}
            self.name = "M-14s from the United States"
            self.result = "Thousands of M-14s are airlifted straight to you from a Nevada warehouse."
            self.description = """The latest in American-made riflery, only available to good 
                friends of Uncle Sam. Slight increase in technology."""
        elif nation.military.weapons < 2000:
            self.weps = 6
            self.cost = {'us_points': 16, 'oil': 3}
            self.name = "M60 Pattons from the United States"
            self.result = "A couple of Pattons arrive on the latest freighter from LA."
            self.description = """Named after Old Blood and Guts himself, ready to 
                be airlifted straight to friends of freedom. Increase in technology."""
        else:
            self.weps = 11
            self.cost = {'us_points': 25, 'oil':  10}
            self.name = "M1 Abrams from the United States"
            self.result = "A couple M1 abrams arrive on the latest freighter from LA."
            self.description = """A powerful, modern tank. Only available to allies 
                of the United States. Large increase in technology."""
        self.requirements = self.cost

    button = "Ask"

    def extra(self):
        return self.nation.alignment != 1

    def enact(self):
        self.nation.military.weapons += self.weps
        self.nation.military.save(update_fields=['weapons'])
        super(us_weapons, self).enact()


class weapons(Policy):
    def __init__(self, nation):
        super(weapons, self).__init__(nation)
        if nation.military.weapons < 500:
            self.weps = 2
            self.cost = {'mg': 5}
            self.requirements = {'mg': 5, 'factories': 2}
            self.name = "Manufacture AK-Presidente model rifles"
            self.result = "Your workers proudly stamp your face on each and every rifle."
            self.description = """Sure it may look and operate identically to the AK-47, but your own 
                people made it damnit! Must have a completed two factories. Slight increase in technology."""
        elif nation.military.weapons < 2000:
            self.weps = 7
            self.cost = {'mg': 13, 'oil': 5}
            self.requirements = {'mg': 13, 'oil': 5, 'factories': 4}
            self.name = "Manufacture Istan Main Battle Tanks"
            self.result = "Your workers proudly stamp your face on each and every tank."
            self.description = """A fine tank made right here in the homeland. 
                Must have a completed four factories. Increase in technology."""
        else:
            self.weps = 12
            self.cost = {'mg': 18, 'oil':  13}
            self.requirements = {'mg': 18, 'oil':  13, 'factories': 8}
            self.name = "Manufacture Despot Main Battle Tank"
            self.result = "Your workers proudly stamp your face on each and every tank."
            self.description = """Oppress the battlefield with this tank of 
                your own make. Must have a completed eight factories."""

    button = "Manufacture"

    def enact(self):
        self.nation.military.weapons += self.weps
        self.nation.military.save(update_fields=['weapons'])
        super(weapons, self).enact()


class migs(Policy):
    def __init__(self, nation):
        super(migs, self).__init__(nation)
        planes = nation.military.planes
        self.cost = {'oil': planes + 5, 'soviet_points': 11 + ((planes**2)-10)}
        self.requirements = self.cost

    name = "Buy MiGs"
    button = "Buy"
    result = "Several MiGs are flown in from Moscow!"
    description = """Soviets are willing to offload some of their older model 
    fighter jets to your airforce as long as you're not in bed with the imperialist 
    Americans. Increase in air power."""

    def extra(self):
        return self.nation.alignment != 3 and self.nation.military.planes < 10

    def enact(self):
        self.nation.military.planes += 1
        self.nation.military.save(update_fields=['planes'])
        super(migs, self).enact()


class f8(Policy):
    def __init__(self, nation):
        super(f8, self).__init__(nation)
        planes = nation.military.planes
        self.cost = {'oil': planes + 5, 'us_points': 11 + ((planes**2)-10)}
        self.requirements = self.cost

    name = "Buy F-8 Crusaders"
    button = "Buy"
    result = "The finest of American death machines are flown in from Nevada!"
    description = """America will sell their finest of the last decade only 
    to their closest allies. Increase in air power."""

    def extra(self):
        return self.nation.alignment != 1 and self.nation.military.planes < 10

    def enact(self):
        self.nation.military.planes += 1
        self.nation.military.save(update_fields=['planes'])
        super(f8, self).enact()


class aircraft(Policy):
    def __init__(self, nation):
        super(aircraft, self).__init__(nation)
        planes = nation.military.planes
        self.cost = {'oil': planes + 5, 'mg': 11 + ((planes**2)/2)}
        self.requirements = {'oil': planes + 5, 'mg': 11 + ((planes**2)/2), 'factories': 3}
    contextual = False
    name = "Manufacture Aircraft"
    button = "Make"
    result = "Several cropdusters are rigged with machine guns!"
    description = """If the US and USSR won't let you have their planes, well you 
    can make your own damn planes! Requires at least three factories."""

    def extra(self):
        return self.nation.military.planes < 10

    def enact(self):
        self.nation.military.planes += 1
        self.nation.military.save(update_fields=['planes'])
        super(aircraft, self).enact()


class navy(Policy):
    def __init__(self, nation):
        super(navy, self).__init__(nation)
        self.cost = {'mg': nation.military.navy + 10, 'oil': 10 + nation.military.navy/2}
        self.requirements = {'factories': 2}
        self.requirements.update(self.cost)
        self.description = """Commission your very own SS %s to 
        sail the sea and maybe shoot at other floating hunks of 
        metal! Will increase your naval level by a single ship.""" % nation.name

    name = "Manufacture ship"
    button = "Make"
    result = "A brand new ship is launched from the shipyards!"
    img = "newship.jpg"

    def extra(self):
        return self.nation.military.navy < 100

    def enact(self):
        self.nation.military.navy += 1
        self.nation.military.save(update_fields=['navy'])
        super(navy, self).enact()


class chems(Policy):
    cost = {'budget': 500, 'reputation': 10, 'research': 5}
    requirements = cost

    name = "Develop Chemical Weapons"
    button = "Cook"
    description = """The Geneva Protocol is just a mere piece of paper, 
    and your military NEEDS some Sarin and Mustard Gas... just in case. 
    Decreases reputation, takes five successful developments to actually 
    create usuable chemical weapons."""

    def extra(self):
        return self.nation.military.chems < 10

    def enact(self):
        chance = random.randint(1, 10)
        if chance > 4:
            self.nation.military.chems += 2
            self.nation.military.save(update_fields=['chems'])
        super(chems, self).enact()


class nuke(Policy):
    cost = {'uranium': 20, 'budget': 100000, 'research': 200}
    requirements = cost

    result = 'You have a nuke.'
    button = "build"
    img = "http://i.imgur.com/wLtwYXi.jpg"
    description = "nukes baby"
    name = "NUKE "

    def extra(self):
        return self.nation.military.reactor == 20


    def enact(self):
        self.nation.military.nukes += 1
        self.nation.military.save(update_fields=['nukes'])