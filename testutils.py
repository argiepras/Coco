from random import randint, choice
from nation.models import *
import string

def ip_generator(amount=1):
    #simply returns a list of n length with randomly generated IPs
    return ['%s.%s.%s.%s' % tuple([randint(0, 255) for x in range(4)]) for x in range(amount)]


def nation_generator(amount=1):
    nations = []
    for x in range(amount):
        q = Nation.objects.create(
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