from collections import OrderedDict
import nation.variables as v
import json
from nation.models import Baseattrs

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
    contextual = False #hides the policy when you can't use it
    img = ''
    cost = {}
    gain = {}
    requirements = {}
    result = ''
    description = ''
    name = ''
    costdesc = ''
    basefail = False
    error_overrides = {}

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

    def check(self): #is supplemented with extra() when it's not as simple 
        #as a simple comparison like this
        for field in self.requirements:
            if getattr(self.nation, field) < self.requirements[field]:
                self.basefail = True
                return False
        if hasattr(self, 'extra'):
            return self.extra()
        return True

    def can_apply(self):
        if not self.check():
            self.result = self.render_insufficient_cost()
            self.img = ''
        return self.check()

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

    def render_insufficient_cost(self):
        if hasattr(self, 'errors'):
            result = self.errors()
            if result:
                return result

        result = 'Not enough '
        lacking = []

        for field in self.requirements:
            if self.requirements[field] > getattr(self.nation, field) and field in v.policyinsufficient:
                lacking.append(field)

        if lacking:
            for field in lacking:
                index = lacking.index(field)
                if index+1 == len(lacking):
                    mod = ''
                elif index+1 == len(lacking) - 1:
                    mod = ' and '
                else:
                    mod = ', '
                desc = v.policyinsufficient[field]
                result += '%s%s' % (desc, mod)
        else:

            result = ''
                #if the lacking stat isn't a resource, like approval or qol
                #we assemble a different error message
            lacking = []
            for field in self.requirements:
                if self.requirements[field] > getattr(self.nation, field) and hasattr(Baseattrs, field):
                    if field in self.error_overrides:
                        return self.error_overrides[field]
                    field = '_%s' % field
                    lacking.append(Baseattrs._meta.get_field(field).verbose_name)

            for field in lacking:
                index = lacking.index(field)
                if index+1 == len(lacking):
                    mod = ''
                elif index+1 == len(lacking) - 1:
                    mod = 'and '
                else:
                    mod = ', '
                result += '%s%s' % (field, mod)
            if len(lacking) > 1:
                result += ' are too low!'
            else:
                result += ' is too low!'
        return result



"""
            keys = field.split('__')
            if len(keys) == 1:
                if getattr(self.nation, field) < self.requirements[field]:
                    self.basefail = True
                    return False
            else:
                if len(keys) == 2:
                    model = self.nation
                    modifier = keys[1]
                    key = keys[0]
                else:
                    model = getattr(self.nation, keys[0])
                    modifier = keys[2]
                    key = keys[1]

                if modifier == 'gt':
                    if getattr(model, key) < self.requirements[field]:
                        return False
                elif modifier == 'gte':
                    if getattr(model, key) <= self.requirements[field]:
                        return False
                elif modifier == 'lte':
                    if getattr(model, key) >= self.requirements[field]:
                        return False
                elif modifier == 'lt': 
                    if getattr(model, key) > self.requirements[field]:
                        return False 
                elif modifier == 'eq':
                    if getattr(model, key) != self.requirements[field]:
                        return False
            """