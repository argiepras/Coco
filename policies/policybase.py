class PolicyMeta(type):
    # we use __init__ rather than __new__ here because we want
    # to modify attributes of the class *after* they have been
    # created
    def __init__(cls, name, bases, dct):
        if not hasattr(cls, 'registry'):
            # this is the base class.  Create an empty registry
            cls.registry = {}
        else:
            # this is a derived class.  Add cls to the registry
            interface_id = name.lower()
            cls.registry[interface_id] = cls
            
        super(PolicyMeta, cls).__init__(name, bases, dct)



class Policy(object):
    def __init__(self, nation):
        self.nation = nation

    __metaclass__ = PolicyMeta
    contextual = True #hides the policy when you can't use it
    img = ''
    cost = {}
    gain = {}
    requirements = {}
    result = ''

    def image(self, url):
        self.img = '/static/img/' + url

    def costdeduction(self):
        for field in self.cost:
            setattr(self.nation, field, getattr(self.nation, field) - self.cost[field])

    def apply(self, applyage):
        #supposed to only be called within an atomic select for update
        #so this should be safe
        self.costdeduction()
        for field in applyage:
            setattr(self.nation, field, getattr(self.nation, field) + applyage[field])

        self.nation.save()

    def can_apply(self): #is overwritten when it's not as simple as a simple comparison like this
        for field in self.requirements:
            if getattr(self.nation, field) < self.requirements[field]:
                return False
        if hasattr(self, 'extra'):
            return self.extra()
        return True

    def _eligible(self): #not in use
        """
            determines if a policy can be executed by a given nation
            uses a big ol dict to make the determination; formed as such
            {
                'nation': {'field': value},
                'related': {
                                'settings': {'field': value},
                                'military': {'field': value},
                        }
            }
        """    
        for field in self.requirements['nation']:
            if getattr(self.nation, field) < self.requirements['nation'][field]:
                return False
        if 'related' in self.requirements: #if requirements need variables from related models
            for target in self.requirements['related']:
                model = getattr(self.nation, target)
                for field in self.requirements['related'][target]:
                    if getattr(model, field) < self.requirements['related'][target][field]:
                        return False

    def __call__(self):
        self.apply(self.gain)
        if 'imgur' not in self.img and self.img != '':
            self.img = '/static/img/' + self.img
