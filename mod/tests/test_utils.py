from nation.models import *
from nation.mod.actions import *
import nation.variables as v
from django.test import TestCase
from django.db.models import Q
from nation.testutils import *  
from nation.mod.ip_magi import *

import random


class iptests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.subject = nation_generator(1)[0]
        #cls.subject.creationip = cls.ips[0].


    def test_nationgen(self):
        x = nation_generator(1)
        x = x[0]
        self.assertIsNotNone(x.settings)
        self.assertIsNotNone(x.military)
        self.assertIsNotNone(x.econdata)
        self.assertIsNotNone(x.researchdata)

    def test_ipgen(self):
        ips = ip_generator(40)
        self.assertEqual(len(ips), 40)
        for ip in ips:
            for count in ip.split('.'):
                count = int(count)
                self.assertGreaterEqual(count, 0)
                self.assertLessEqual(count, 255)



class ip_gathering_tests(TestCase):
    @classmethod
    def setUpTestData(cls):
        nationsets = [nation_generator(20) for x in range(2)]
        commons = [ip_generator(1) for x in range(2)]
        cls.creation = commons[1]
        # sets different IPs for each generated nation
        # with having 1 random IP in common
        for nations, common in zip(nationsets, commons):
            for nation in nations:
                nation.IPs.create(IP=common)
                ips = ip_generator(20)
                common = random.choice(ips)
                for ip in ips:
                    nation.IPs.create(IP=ip)
                common = random.choice(ips)
        cls.common = list(IP.objects.filter(IP=common).values_list('IP', flat=True))
        for n in nationsets[0]:
            Nation.objects.filter(pk=n.pk).update(creationip=commons[1])

        cls.set1 = nationsets[0]
        cls.set2 = nationsets[1]

    def test_deep_correlation(self):
        nations, ips = deep_correlation(self.common)
        #should find 20 nations
        self.assertEqual(nations.count(), 20)

    def test_correlation(self):
        nations, ips = correlated_ips(self.common)
        #should find 2 nations
        self.assertEqual(nations.count(), 2)

    def test_creations(self):
        nations, first = creation_ip_nations(self.creation)
        self.assertEqual(nations.count(), 20)

        nations, first = creation_ip_nations(self.common)
        self.assertEqual(nations.count(), 0)
        self.assertEqual(first, None)


    def test_iptoip(self):
        a = IP.objects.all()
        b = IP_to_ip(a)
        self.assertEqual(len(a), len(b))
        self.assertEqual(type(list()), type(b))








