from random import randint, choice
from nation.models import *
from django.contrib.auth.models import User
import string
import glob
import os


def ip_generator(amount=1):
    #simply returns a list of n length with randomly generated IPs
    return ['%s.%s.%s.%s' % tuple([randint(0, 255) for x in range(4)]) for x in range(amount)]

def namegen():
    return ''.join(choice(string.ascii_letters) for x in range(8))

def mailgen():
    return "%s@gmail.com" % namegen()


def nation_generator(amount=1, random=True):
    nations = []
    t = ID.objects.get_or_create()[0]
    for x in range(amount):
        index = x + t.index
        user = User.objects.create(username=namegen(), password='password')
        if random:
            q = Nation.objects.create(
                user=user,
                index=index, 
                name=''.join(choice(string.ascii_letters) for x in range(8)),
                creationip=ip_generator()[0],
                gdp=randint(300, 15000),
                factories=randint(0, 10),
                mines=randint(0, 20),
                wells=randint(0, 20),
                creationtime=timezone.now() - timezone.timedelta(hours=randint(1, 100)),
                universities=randint(0, 10),
                FI=randint(0, 15000),
                research=randint(0, 250),
                oilreserves=randint(0, 25000),
                uranium=randint(0, 10),
                )
            for field in Baseattrs._meta.fields:
                setattr(q, field.name, randint(0, 100))
            q.save()
        else:
            q = Nation.objects.create(
                user=user,
                index=index, 
                name=''.join(choice(string.ascii_letters) for x in range(8)),
                creationip=ip_generator()[0],
                )
        t.index += 1
        q.IPs.create(IP=q.creationip)
        nations.append(q)
    t.save()
    return (nations if amount > 1 else nations[0])


def alliance_generator(founder=None, members=0, officers=0):
    if founder == None:
        founder = nation_generator()
    alliance = Alliance.objects.create(name=namegen(), founder=founder.name)
    if members:
        for member in nation_generator(members):
            alliance.add_member(member)

    if officers:
        officer_template = alliance.templates.get(rank=3)
        for member in nation_generator(officers):
            alliance.add_member(member)
            member.permissions.template = officer_template
            member.permissions.save()
    return alliance



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



def snapshoot(nation):
    #Simple snapshot for easy comparison
    #like checking if costs are properly deducted
    x = Snapshot()
    for field in Nationattrs._meta.fields:
        setattr(x, field.name, getattr(nation, field.name))
    return x



def cost_check(self, nation, snap, cost):
    for field in cost:
        self.assertEqual(getattr(snap, field), getattr(nation, field) + cost[field], msg='%s not subtracting' % field)



def refresh(*args, **kwargs):
    related = False
    if 'related' in kwargs:
        related = kwargs.pop('related')
    for nation in args:
        nation.refresh_from_db()
        if related:
            for model in related:
                getattr(nation, model).refresh_from_db()



def find_prints():
    flist = []
    for directory, subdir, files in os.walk('.'):
        for filename in files:
            if filename[-3:] == '.py':
                if 'testutils' in filename:
                    continue
                if len(directory) == 1:
                    flist.append(filename)
                else:
                    flist.append(directory[2:] + '/' + filename)
    
    prints = {}
    for file in flist:
        with open(file, 'r') as open_file:
            for line in open_file:
                if 'print ' in line:
                    if not 'script' in file:
                        prints[file] = True

    return prints