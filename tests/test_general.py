from django.test import SimpleTestCase
from nation.utilities import *

class test_utils(SimpleTestCase):
    def test_stringlisting(self):
        l = ['a']
        result = string_list(l)
        self.assertEqual(result, 'a')
    
        l.append('b')
        result = string_list(l)
        self.assertEqual(result, 'a and b')

        l.append('c')
        result = string_list(l)
        self.assertEqual(result, 'a, b and c')

        l += l
        result = string_list(l)
        self.assertEqual(result, 'a, b, c, a, b and c')

        tmp = type('temp', (object,), {'name': ''})
        newlist = []
        for x in l:
            inst = tmp()
            inst.name = x
            newlist.append(inst)

        result = string_list(mewlist, 'name')
        self.assertEqual(result, 'a, b, c, a, b and c', msg="It should use field names")

    def test_econsystem(self):
        self.assertEqual(econsystem(0), 0)
        self.assertEqual(econsystem(20), 0)
        self.assertEqual(econsystem(30), 0)
        self.assertEqual(econsystem(40), 1)
        self.assertEqual(econsystem(60), 1)
        self.assertEqual(econsystem(70), 2)
        self.assertEqual(econsystem(90), 2)
        self.assertEqual(econsystem(100), 2)