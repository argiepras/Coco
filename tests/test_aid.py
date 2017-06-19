from django.test import TestCase
from nation.testutils import *
from nation.models import *
from nation.aid import *
import nation.news as news



class test_aid(TestCase):
    def setUp(self):
        self.sender = nation_generator()
        self.recipient = nation_generator()
        Market.objects.get_or_create()

    def test_uranium_aid(self):
        self.sending_stuff('uranium', 1, uranium)

    def test_research_aid(self):
        self.sending_stuff('research', 50, research)

    def sending_stuff(self, resource, amount, aidfunc):
        send = self.sender
        rec = self.recipient
        newscount = rec.news.all().count()
        args = {'nation': send, 'target': rec}
        result = aidfunc(**args)
        self.assertEqual(getattr(rec, resource), 0, msg="Shouldn't recieve %s with sender having 0" % resource)
        self.assertTrue(result != '')
        +69

        setattr(send, resource, amount)
        send.save()
        self.assertGreater(getattr(send, resource), getattr(rec, resource), msg="sender should have more %s" % resource)
        result = aidfunc(**args)
        send.refresh_from_db()
        rec.refresh_from_db()
        self.assertFalse(result == '')
        self.assertGreater(getattr(rec, resource), getattr(send, resource), msg="%s didn't transfer" % resource)
        self.assertGreater(rec.news.all().count(), newscount, msg="Newsitem should be created")


    def test_sending_troops(self):
        send = self.sender
        rec = self.recipient
        args = {'nation': send, 'target': rec}
        send.military.army = 5
        self.assertFalse(send.econdata.expedition)
        result = expeditionary(**args)
        send.refresh_from_db()
        send.econdata.refresh_from_db()
        newscount = rec.news.all().count()
        self.assertTrue(result != '')
        self.assertEqual(send.military.army, 5, msg="shouldn't send troops below 10k")
        send.military.army = 20
        rec.military.army = 20
        training = rec.military.training
        send.military.save()
        rec.military.save()
        result = expeditionary(**args)
        send.military.refresh_from_db()
        rec.military.refresh_from_db()
        self.assertGreater(rec.military.army, send.military.army, msg="Troops didn't transfer")
        send.econdata.refresh_from_db()
        self.assertTrue(send.econdata.expedition)
        self.assertGreater(rec.news.all().count(), newscount, msg="Newsitem should be created")
        if training > send.military.training:
            self.assertGreater(training, rec.military.training, msg="Training should decrease")
        elif training < send.military.training:
            self.assertGreater(training, rec.military.training, msg="Training should increase")
        else:
            self.assertEqual(training, rec.military.training, msg="Training should remain the same")
        self.assertGreater(rec.news.all().count(), newscount, msg="Newsitem should be created")


    def test_ceding(self):
        send = self.sender
        rec = self.recipient
        newscount = rec.news.all().count()
        args = {'nation': send, 'target': rec}
        reference = rec.land
        send.land = min_land + 50
        send.save()
        result = cede(**args)
        self.assertTrue(result != '')
        self.assertEqual(send.land, min_land + 50)
        self.assertEqual(rec.land, reference)

        #land should cede now
        send.land = reference
        send.save()
        result = cede(**args)
        self.assertTrue(result != '')
        send.refresh_from_db()
        rec.refresh_from_db()
        self.assertGreater(rec.land, send.land, msg="Land didn't cede")
        self.assertGreater(reference, send.land, msg="Land didn't get subtracted")
        self.assertGreater(rec.land, reference, msg="Land didn't get added")
        self.assertGreater(rec.news.all().count(), newscount, msg="Newsitem should be created")



    def test_sending_weapons(self):
        send = self.sender
        rec = self.recipient
        newscount = rec.news.all().count()
        args = {'nation': send, 'target': rec}
        reference  = rec.military.weapons
        send.military.weapons = 5
        send.military.save()
        result = give_weapons(**args)
        self.assertTrue(result != '')
        self.assertEqual(send.military.weapons, 5, msg="Weapons shouldn't send with only 5")

        send.military.weapons = 100
        rec.military.weapons = 100
        send.military.save()
        rec.military.save()

        rep_ref = send.reputation
        reference = rec.military.weapons
        result = give_weapons(**args)
        send.refresh_from_db()
        send.military.refresh_from_db()
        rec.military.refresh_from_db()
        self.assertGreater(rec.military.weapons, send.military.weapons, msg="Weapons didn't transfer")
        self.assertTrue(result != '')
        self.assertGreater(rep_ref, send.reputation, msg="reputation didn't subtract")
        self.assertGreater(rec.news.all().count(), newscount, msg="Newsitem should be created")

    
    def test_sending_weapons_opposite_alignments(self):
        send = self.sender
        rec = self.recipient
        newscount = rec.news.all().count()
        args = {'nation': send, 'target': rec}
        rec.alignment = 1
        send.alignment = 3
        rep = rec.reputation
        send.save()
        rec.save()
        send.military.weapons = 100
        rec.military.weapons = 100
        send.military.save()
        rec.military.save()
        result = give_weapons(**args)
        send.military.refresh_from_db()
        rec.military.refresh_from_db()
        send.refresh_from_db()
        self.assertEqual(send.military.weapons, rec.military.weapons, msg="Weapons shouldn't transfer for opposite alignments")
        self.assertEqual(rec.news.all().count(), newscount, msg="Newsitem shouldn't be created")
        self.assertEqual(rec.reputation, rep, msg="reputation shouldn't subtract on failure")


    def test_aid(self):
        from nation.variables import resources
        for resource in resources:
            self.vanilla_aid(resource)


    def vanilla_aid(self, resource):
        #all aid should behave the same so single, recyclable function should work just fine
        send = self.sender
        rec = self.recipient
        send_snap = snapshoot(send)
        rec_snap = snapshoot(rec)
        newscount = rec.news.all().count()
        #vanilla nations for now

        payload = {resource: send.__dict__[resource]*2}
        args = {'nation': send, 'target': rec, 'POST': payload}
        #expected failure
        result = send_aid(**args)
        refresh(send, rec)
        self.assertTrue(result != '', args="Result shouldn't be empty")
        self.assertEqual(getattr(send, resource), getattr(send_snap, resource), msg="Failed %s aid shouldn't send" % resource)
        self.assertEqual(getattr(rec, resource), getattr(rec_snap, resource), msg="Failed %s aid shouldn't send" % resource)
        self.assertEqual(rec.news.all().count(), newscount, msg="newscount shouldn't increase for a failure")


        payload = {resource: send.__dict__[resource]}
        args = {'nation': send, 'target': rec, 'POST': payload}
        #expected failure
        result = send_aid(**args)
        refresh(send, rec)
        self.assertTrue(result != '', args="Result shouldn't be empty")
        self.assertLesser(getattr(send, resource), getattr(send_snap, resource), msg="Failed %s aid should've sent" % resource)
        self.assertGreater(getattr(rec, resource), getattr(rec_snap, resource), msg="Failed %s aid should've sent" % resource)
        self.assertGreater(rec.news.all().count(), newscount, msg="newscount shouldn't increase for a failure")
