from collections import OrderedDict
import nation.variables as v
import json

class PolicyMeta(type):
    # we use __init__ rather than __new__ here because we want
    # to modify attributes of the class *after* they have been
    # created
    def __init__(cls, name, bases, dct):
        if not hasattr(cls, 'registry'):
            # this is the base class.  Create an empty registry
            cls.registry = OrderedDict()
        else:
            # this is a derived class.  Add cls to the registry
            interface_id = name.lower()
            if interface_id.split('_')[0] != 'base': #inheritance won't mess up the registry
                cls.registry[interface_id] = cls
                cls.policyname = interface_id
                for policytype in ['economic', 'domestic', 'military', 'foreign']:
                    if policytype in str(cls).split('.'):
                        cls.policytype = policytype
            
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
    description = ''
    name = ''
    costdesc = ''

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

    def can_apply(self): #is supplemented with extra() when it's not as simple 
                         #as a simple comparison like this
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

    def enact(self):
        self._log()
        self.apply(self.gain)
        if 'imgur' not in self.img and self.img != '':
            self.img = '/static/img/' + self.img


    def render_cost(self):
        if self.costdesc != '':
            return self.costdesc
        desc = ''
        mod = ', '
        for field in v.resources:
            if field in self.cost:
                desc += v.pretty(self.cost[field], field, True) + mod
        othercostfields = []
        for field in self.cost:
            if field in v.resources:
                continue
            else:
                othercostfields.append(field)
        if othercostfields:
            for field in self.cost:
                if not field in v.policycost_descriptions:
                    continue
                if field == "FI":
                    appendage = '$%sk' % self.cost[field]
                elif field == "growth":
                    appendage = '$%s' % self.cost[field]
                else:
                    appendage = '%s' % self.cost[field]
                desc += '%s %s' % (appendage, v.policycost_descriptions[field]) + mod

        return desc[:-2]


    def _log(self):
        #policy logging
        #logs policies so mods can see who did what, and when
        #oh and how many times lol
        log, created = self.nation.actionlogs.get_or_create(
            timestamp__gte=v.now() - v.timezone.timedelta(minutes=15),
            action=self.name)
        new_cost = self.cost
        if not created: 
            #updates the json encoded cost so it's a total
            cost = json.loads(log.cost)
            for field in new_cost:
                if field in cost:
                    cost[field] += new_cost[field]
                else:
                    cost[field] = new_cost[field]
            new_cost = cost
            log.amount += 1
        log.cost = json.dumps(new_cost)
        log.action = self.name
        log.policy = True
        log.save()

    def json(self):
        return {'result': self.result, 'img': self.img}


