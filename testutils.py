from random import randint, choice
from nation.models import *
from django.contrib.auth.models import User
import string

def ip_generator(amount=1):
    #simply returns a list of n length with randomly generated IPs
    return ['%s.%s.%s.%s' % tuple([randint(0, 255) for x in range(4)]) for x in range(amount)]


def nation_generator(amount=1):
    nations = []
    ID.objects.get_or_create()
    for x in range(amount):
        q = Nation.objects.create(
            user=User.objects.create(username=namegen()),
            index=x, 
            name=''.join(choice(string.ascii_letters) for x in range(8)),
            creationip=ip_generator()[0],
            )
        Settings.objects.create(nation=q)
        Military.objects.create(nation=q)
        Econdata.objects.create(nation=q)
        Researchdata.objects.create(nation=q)
        q.IPs.create(IP=q.creationip)
        nations.append(q)
    return nations


def namegen():
    return ''.join(choice(string.ascii_letters) for x in range(8))


def set_nation(nation, newvals):
    """
        Takes a dictionary and sets the fields of the supplied nation
        uses setattr because it respects properties
        unlike __dict__
    """
    if not isinstance(newvals, dict):
        raise TypeError
    for field in newvals:
        setattr(nation, field, newvals[field])