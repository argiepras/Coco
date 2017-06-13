from .policybase import Policy
import nation.utilities as utils
import random
from nation.turnchange import mgbonus
from django.db.models import F
from nation.models import *


class arrest(Policy):
    cost = {'budget': 50, 'government': 6}
    requirements = {'budget': 50, 'government': 1}
    img = 'arrest.jpg'
    gain = {'stability': 3}
    name = "Arrest opposition"
    button = 'Arrest'
    description = """These imputent fools do nothing but criticize. Shut them up. \
    Your government will become more authoritarian. Chance of decreasing rebels. \
    Slightly increases stability but a small decrease in reputation."""

    def enact(self):
        chance = random.randint(1, 10)
        if chance > 5 and self.nation.rebels > 0:
            self.result = "You arrest the opposition. Turns out some of \
            them were working with the rebels! Rebel strength decreases."
            self.cost.update({'rebels': 1})
        else:
            self.result = "You arrest the opposition. Unfortunately \
            none of them seemed to be working with the rebels..."
        super(arrest, self).enact()


class release(Policy):
    cost = {'budget': 50, 'stability': 4}
    gain = {'government': 6}
    requirements = cost
    button = "Free"
    name = "Release political prisoners"
    description = "Free the poor souls. Your government becomes more democratic. \
    Small chance of the ungrateful fucks joining up with rebels. Decreases stability."

    def extra(self):
        return self.nation.government < 100

    def enact(self):
        chance = random.randint(1, 10)
        if chance > 6:
            self.gain.update({'rebels': 1})
            self.result = "You release the prisoners, but some of them go on to join the rebels!"
        else:
            self.result = "You release the prisoners and everything seems a bit freer."
        super(release, self).enact()


class martial(Policy):
    cost = {'budget': 100, 'manpower': 10, 'government': 50, 'reputation': 2, 'stability': 5}
    requirements = {'budget': 100, 'government': 21, 'manpower': 10}
    result = 'Your soldiers march down the street, conscripting men on the spot and arresting all dissenters.'
    img = 'martial.jpg'
    name = "Declare martial law"
    button = "Declare"
    description = "Dissent cannot be tolerated in wartime! Move decisively \
    authoritarian, increase military size. Decreases stability and reputation."

    def enact(self):
        self.nation.military.army += 10
        self.nation.military.training += 5
        self.nation.military.save(update_fields=['army', 'training'])


class elections(Policy):
    cost = {'budget': 200}
    requirements = {'budget': 200}
    gain = {'government': 30, 'approval': random.randint(1, 10)}
    name = "Hold free and fair elections"
    button = "Elect"
    img = "elections.jpg"
    description = """Sometimes it is necessary to let the people have a voice. \
    Rebels will possibily lay down their arms and your government will become \
    less authoritarian. Possibly increase growth but will cost some stability."""

    def enact(self):
        chance = random.randint(1, 10)
        if chance > 6 and self.nation.approval > 50:
            self.result = 'Elections are held, but the rebels continue their struggle, \
            dropping stability. Despite this your victory in the elections increases \
            your popularity.'
        elif self.nation.rebels > 2 and nation.aproval > 50:
            self.cost.update({'rebels': 3})
            self.result = "As you win the elections some rebels recognize the \
            legitimacy of your government and lay down their arms, while popularity increases."
        elif self.nation.approval > 50:
            self.gain.update({'growth': 1})
            self.result = 'After successful free elections investors invest, \
            hoping to benefit from your stability. Growth and popularity grow.'
        else:
            self.result = "You would have lost the election. Your electoral board \
            has of course rigged it so you stay in power... but be careful next time! Stability drops."
            self.cost.update({'stability': random.randint(0, 10)})
            self.img = ''
        super(enact, self).enact()


class housing(Policy):
    def __init__(self, nation):
        super(housing, self).__init__(nation)
        self.result = 'The people are overjoyed at their new cement box! Government popularity increases.'
        self.cost = {'budget': nation.gdp/2, 'economy': 2}
        self.gain = {'approval': 10}
        if random.randint(1, 10) > 6:
            self.gain.update({'qol': 2})
            self.result = self.result[:-1] + ', as does quality of life.'


    img = "housing.jpg"
    name = "Free Housing For the People"
    button = "Build"
    description = """Mass produced modular tenements for everyone! Sure, every \
    residential area in your country will look incredibly grey, boring and identical, \
    but it's better than scrap metal shacks. Increases government popularity. \
    Not available in Free Market economies.  Moves your economic system slightly \
    to the left. Cost is relative to GDP."""

    def extra(self):
        return utils.econsystem(self.nation.economy) < 2 and self.nation.approval < 100


class wage(Policy):
    def __init__(self, nation):
        super(wage, self).__init__(nation)
        self.cost = {'growth': int((nation.gdp*1.05)/400), 'economy': 2}
        self.requirements = {'growth': -5}
        self.gain = {'approval': 21}
        if random.randint(1, 10) > 8:
            self.gain.update({'qol': 2})
            self.result = 'Workers can now afford two and a half meals a \
            day! Government popularity increases, as does quality of life slightly.'
        else:
            self.result = 'Wage increases but unfortunately have few effects on the quality of life.'


    def extra(self):
        return utils.econsystem(self.nation.economy) > 0

    img = 'minimum.jpg'
    name = "Raise Minimum Wage"
    button = "Raise"
    description = """Apparently people need to eat. Increase their wages \
    by a couple cents and it might just increase your popularity. \
    Moves your economic system slightly to the left. Cost is relative to GDP."""


class freefood(Policy):
    def __init__(self, nation):
        super(freefood, self).__init__(nation)
        self.cost = {'food': (nation.qol/10*nation.approval/10*nation.gdp/200/4)}
        self.requirements = self.cost

    def extra(self):
        return self.nation.approval < 100

    gain = {'approval': 10, 'economy': -5}
    img = 'freefood.jpg'
    name = "Free Food for All!"
    button = "Give"
    result = "The poor rejoice at not having to worry about their next meal! Obesity increases by 1%."
    description = "Feed the poor and enjoy their loyalty. Increases approval. Moves government to the left."


class school(Policy):
    def __init__(self, nation):
        super(school, self).__init__(nation)
        multiplier = ((1 - 0.10)**nation.universities if nation.universities > 0 else 1)
        self.cost = {
            'rm': int((nation.literacy/8 + (nation.gdp/150)) * multiplier),
            'budget': int((nation.gdp/1.5) * multiplier),
        }
        self.requirements = self.cost

    gain = {'literacy': 5}
    name = "Construct Public School"
    button = "Build"
    result = 'Literacy increases! Yay!'
    img = "school.jpg"
    description = "A literate people make more money for you to tax. \
    Increases literacy. Cost is relative to GDP (.05%)."

    def extra(self):
        return self.nation.literacy < 100


class university(Policy):
    def __init__(self, nation):
        super(university, self).__init__(nation)
        total = nation.universities 
        self.cost = {
            'rm': (total*100+50 if nation.region() != 'Asia' else total*75+38),
            'oil': (total*50+25 if nation.region() != 'Asia' else total*38+19),
            'mg': (total*2 if nation.region() != 'Asia' else total*2*0.75),
        }
        self.requirements = self.cost

    def extra(self):
        return self.nation.farmland() >= v.landcost['universities']

    gain = {'universities': 1}
    name = 'Found University'
    button = 'Teach'
    img = 'university.jpg'
    result = "Your students take to the classrooms!"
    description = """Distract your annoying dissident eggheads with a few \
    shiny new buildings to pontificate to each other in. Provides 4 research \
    per turn, but consumes 1 mg per turn. Also provides $1 million in growth per \
    turn. Each university decreases the cost of raising literacy."""


class closeuni(Policy):
    cost = {'univiersities': 1}
    requirements = cost
    gain = {'closed_universities': 1}
    costdesc = "Free!"
    name = "Close University"
    button = "Board up"
    result = "Lecture halls get boarded up and students are sent to the fields"
    description = "Turns out those fancy buildings filled with so called \
    intellectuals was a bad idea. Shut them down and let the students do real work."


class reopenuni(Policy):
    cost = {'closed_universities': 1, 'budget': 1000}
    requirements = cost
    gain = {'universities': 1}
    name = "Reopen University"
    button = "Renovate"
    result = "Students pour into the re-opened lecture halls!"
    description = "It's time for more eggheads! This reopens a \
    previously closed university and provides the benefits if it again."


class hospital(Policy):
    def __init__(self, nation):
        super(hospital, self).__init__(nation)
        self.cost = {'rm': nation.qol/6 + nation.gdp/150, 'budget': nation.gdp/2}
        self.requirements = self.cost

    def extra(self):
        return self.nation.healthcare < 100

    gain = {'healthcare': 10}
    name = "Construct Free Hospital"
    button = "Build"
    img = 'hospital.jpg'
    result = "Deaths from preventative diseases drop significantly, and healthcare skyrockets."
    description = "Provide for all the ability to live past the age of 42. \
    Increases healthcare. Not available to free market economies. Cost is relative to GDP."


class medicalresearch(Policy):
    def __init__(self, nation):
        super(medicalresearch, self).__init__(nation)
        self.cost = {'research': nation.healthcare/10, 'budget': nation.gdp/2}
        self.requirements = self.cost

    def extra(self):
        return self.nation.healthcare < 100

    gain = {'healthcare': 10}
    name = "Fund Medical Research"
    img = "hospital.jpg"
    button = "Discover"
    result = "A new vaccine saves countless lives, and healthcare skyrockets."
    description = "Discover the latest vaccine for the Butt Pox. Increases \
                    healthcare. Cost is relative to GDP."


class cult(Policy):
    def __init__(self, nation):
        super(cult, self).__init__(nation)
        self.cost = {'budget': 500, 'government': nation.government}
        self.requirements = {'budget': 500, 'government': 41}

    name = "Cult of Personality"
    button = "Bask"
    img = "cult.jpg"
    result = 'Oh How The People Love Me. I Am Their Guardian \
    And Protector From Want And Fear. What A Great Leader I Am.'
    description = "The Great and Glorious Leader Provides For All. \
    He was Born Under a Smiling Sun and Rides a Pegasus On His Days \
    Off. Dear Leader Has Never Lost a Game of Ping-Pong. Increases \
    popularity, makes your country instantly a dictatorship."