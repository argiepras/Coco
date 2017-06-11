from .policybase import Policy

class base_alignchange(Policy):
    cost = {'budget': 50, 'stability': 5}
    requirements = cost

class praise_ussr(basealignchange):
    name = "Praise USSR"
    img = "soviets.jpg"
    button = "Suck up"
    result = "You praise the glorious advances of the Soviet Union. They like that."
    description = "Give the General Secretary a bear hug in front of the cameras. \
    Sets your alignment as pro-Soviet. Stability decreases somewhat as the bourgeoisie bitches."

    def extra(self):
        return self.nation.alignment != 1 #can't realign if commie already

    def enact(self):
        self.nation.alignment = 1
        super(praise_ussr, self).enact()


class praise_us(basealignchange):
    name = "Praise the United States"
    img = "usa.jpg"
    button = "Kiss ass"
    result = "You praise the glorious advances of the Soviet Union. They like that."
    description = "Shake the Prez' hand on the tarmac. Sets your alignment as \
    pro-USA. Stability decreases somewhat as all the pinkos complain."

    def extra(self):
        return self.nation.alignment != 3

    def enact(self):
        self.nation.alignment = 3
        super(praise_us, self).enact()


class declareneutrality(basealignchange):
    name = "Declare Neutrality"
    img = "neutrality.jpg"
    button = "Stand strong"
    result = "You praise the beautiful freedom and independence of your people. They like that."
    description = "Show all the other countries that you're a proud \
    independent nation that don't need no superpower. Sets your alignment as neutral."

    def extra(self):
        return self.nation.alignment != 2

    def enact(self):
        self.nation.alignment = 2
        super(praise_us, self).enact()


class base_intervention(Policy):
    button = "Beg"
    def enact(self):
        self.nation.military.army += 10
        self.nation.military.save(update_fields=['army'])
        super(base_intervention, self).enact()


class soviet_intervention(base_intervention):
    cost = {'soviet_points': 35}
    requirements = cost
    img = 'sovietintervention.jpg'
    result = "10k Soviet troops arrive to liberate us from the capitalist oppressors"
    name = "Appeal to the Soviets for intervention"
    description = "Ask our comrades in the Soviet Union to help defend equality \
    and socialism from the evil capitalists. They will arrive with 10k troops."

    def extra(self):
        return self.nation.alignment != 3


class us_intervention(base_intervention):
    def __init__(self, nation):
        super(us_intervention, self).__init__(nation)
        self.cost = {'us_points': (35 if nation.region() != 'Latin America' else 25)}
        self.requirements = self.cost
    img = 'usintervention.jpg'
    result = "10k Americans troops arrive to spread freedom and blow stuff up."
    name = "Appeal to the United States for intervention"
    description = "Ask our friends and allies in the United States to help \
    defend freedom and democracy from the evil communists. They will arrive with 10k troops."

    def extra(self):
        return self.nation.alignment != 1

class base_aid(Policy):
    gain = {'growth': 5}
    button = "Beg"

class usaid(base_aid):
    cost = {'us_points': 10}
    requirements = cost
    name = "Appeal to the Soviets for development aid" 
    img = "usaid.jpg"
    result = "Growth increases as Americans give us free \
    stuff in the name of freedom because freedom isn't free or something."
    description = "Ask our capitalist allies to give us a little \
    taste of McDonalds. Will increase growth by $5 million."
    def extra(self):
        return self.nation.alignment != 1


class sovietaid(base_aid):
    cost = {'soviet_points': 10}
    requirements = cost
    name = "Appeal to the Soviets for development aid"
    img = "sovietaid.jpg"
    result = "Growth increases as the our Soviet \
    comrades shower us with the glorious benefits of socialism."
    description = "Ask our comrades to give us a little taste \
    of communism. Will increase growth by $2 million."
    def extra(self):
        return self.nation.alignment != 3


class create_alliance(Policy):
    cost = {'budget': 150}
    requirements = cost
    name = "Create an International Alliance"
    button = "Create"
    description = "Create an alliance of nations to beat up other \
    alliances of nations. Once an alliance is created it allows you \
    to invite others into it, creates a unique page for your alliance,"

    def extra(self):
        return not self.nation.has_alliance()