


class Baseactionmeta(type):
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
        super(Baseactionmeta, cls).__init__(name, bases, dct)


class BaseAction(object):
    def __init__(self, nation):
        self.nation = nation

    __metaclass__ = Baseactionmeta
    required_rank = 5
    permissions_required = []
    generate_events = False


    def execute(self, *args, **kwargs):
        outcome, success = self.action(*args, **kwargs)

        if success:
            if self.log_msg:
                self.log_action()
            if self.generate_events:
                self.generate_events()
        return outcome

    def log_action(self):
        args = {
            'policy': False,
            'action': self.log_msg,
        }
        if self.log_extra:
            args.update({'extra': self.log_extra})
        self.nation.actionlogs.create(**args)
