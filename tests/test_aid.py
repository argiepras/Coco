from django.test import TestCase
from nation.testutils import *
from nation.models import *
from nation.aid import *
import nation.news as news



class test_aid(TestCase):
    def setUp(self):
        self.sender = nation_generator(random=False)
        self.sender.subregion = "China"
        self.recipient = nation_generator(random=False)
        self.recipient.subregion = "China"
        Market.objects.get_or_create()

    def test_uranium_aid(self):
        self.sending_stuff('uranium', 1, uranium)
        self.log_check(self.sender, self.recipient)

    def test_research_aid(self):
        self.sending_stuff('research', 50, research)
        self.log_check(self.sender, self.recipient)

    def sending_stuff(self, resource, amount, aidfunc):
        send = self.sender
        rec = self.recipient
        newscount = rec.news.all().count()
        args = {'nation': send, 'target': rec}
        result = aidfunc(**args)
        self.assertEqual(getattr(rec, resource), 0, msg="Shouldn't recieve %s with sender having 0" % resource)
        self.assertTrue(result != '')

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
        self.log_check(send, rec)


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
        self.assertGreater(rec.land, send.land, msg="Land didn't cede: %s" % result)
        self.assertGreater(reference, send.land, msg="Land didn't get subtracted")
        self.assertGreater(rec.land, reference, msg="Land didn't get added")
        self.assertGreater(rec.news.all().count(), newscount, msg="Newsitem should be created")
        self.log_check(send, rec)


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
        self.log_check(send, rec)

    
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
            self.aid_tariffs(resource, 'alignment', 1)
            self.aid_tariffs(resource, 'economy', 27)
            self.spamming(resource)


    def vanilla_aid(self, resource):
        #all aid should behave the same so single, recyclable function should work just fine
        send = nation_generator(random=False)
        send.mg = 10
        send.save()
        rec = nation_generator(random=False)
        rec.mg = 10
        rec.save()
        send_snap = snapshoot(send)
        rec_snap = snapshoot(rec)
        newscount = rec.news.all().count()
        #vanilla nations for now

        payload = {'amount': send.__dict__[resource]*2, 'resource': resource}
        args = {'nation': send, 'target': rec, 'POST': payload}
        #expected failure
        result = send_aid(**args)['result']
        refresh(send, rec)
        self.assertTrue(result != '', msg="Result shouldn't be empty")
        self.assertTrue(result != 'invalid resource', msg="POST data is invalid")
        self.assertTrue(result == 'You cannot send off more than you have!')
        self.assertEqual(getattr(send, resource), getattr(send_snap, resource), msg="Failed %s aid shouldn't send" % resource)
        self.assertEqual(getattr(rec, resource), getattr(rec_snap, resource), msg="Failed %s aid shouldn't send" % resource)
        self.assertEqual(rec.news.all().count(), newscount, msg="newscount shouldn't increase for a failure")

        payload = {'amount': send.__dict__[resource], 'resource': resource}
        args = {'nation': send, 'target': rec, 'POST': payload}
        #expected success
        result = send_aid(**args)
        refresh(send, rec)
        self.assertTrue(result != '', msg="Result shouldn't be empty")
        self.assertTrue(result != 'invalid', msg="Result shouldn't be invalid")
        self.assertLess(getattr(send, resource), getattr(send_snap, resource), msg="Failed %s aid should've sent" % resource)
        self.assertGreater(getattr(rec, resource), getattr(rec_snap, resource), msg="Failed %s aid should've been recieved" % resource)
        self.assertGreater(rec.news.all().count(), newscount, msg="newscount should increase")
        self.log_check(send, rec)


    def aid_tariffs(self, resource, t_type, t_val):
        send = nation_generator(random=False)
        rec = nation_generator(random=False)
        setattr(send, resource, 500)
        setattr(rec, resource, 500)
        send.budget = 5000
        setattr(send, t_type, t_val)
        setattr(rec, t_type, t_val * 3)
        send_snap = snapshoot(send)
        rec_snap = snapshoot(rec)
        send.save()
        rec.save()

        payload = {'amount': 100, 'resource': resource}
        send_aid(**{'nation': send, 'target': rec, 'POST': payload})
        refresh(send, rec)
        if resource == 'budget':
            self.assertGreater(send_snap.budget - 100, send.budget, msg="Tariff should subtract for %s" % t_type)
        else:
            self.assertGreater(send_snap.budget, send.budget, msg="Tariff should subtract for %s" % t_type)

    
    def spamming(self, resource):
        send = nation_generator(random=False)
        send.mg = 20
        send.save()
        rec = nation_generator(random=False)
        rec.mg = 20
        rec.save()

        for p in xrange(10):
            send_aid(**{'nation': send, 'target': rec, 'POST': {'amount': 1, 'resource': resource}})
        self.assertEqual(rec.incoming_aid.all().count(), 1, msg="Spamming %s aid should only give 1 log entry" % resource)
        self.assertEqual(send.outgoing_aid.all().count(), 1, msg="Spamming %s aid should only give 1 log entry" % resource)
        self.assertEqual(send.actionlogs.all().count(), 1, msg="Spamming %s should only generate 1 actionlog entry" % resource)


    def log_check(self, send, rec):
        self.assertGreater(send.outgoing_aid.all().count(), 0, msg="outgoing aidlogs should be created")
        self.assertGreater(rec.incoming_aid.all().count(), 0, msg="Incoming aidlogs should be created")
        self.assertGreater(send.actionlogs.all().count(), 0, msg="Actionlogs should be created")
        for log in send.outgoing_aid.all():
            self.assertGreater(log.value, 0, msg="Value of aid should be set")


    def test_nukes(self):
        send = nation_generator(random=False)
        rec = nation_generator(random=False)
        #vanilla nation have 0 nukes so calling it right off the bat should yield a failure
        result = nukes(**{'nation': send, 'target': rec})
        self.assertTrue(result != '')
        refresh(send, rec, related=['military'])
        self.assertEqual(send.military.nukes, 0, msg="Shouldn't have nukes")
        self.assertEqual(rec.military.nukes, 0, msg="Shouldn't have nukes")

        send.military.nukes = 1
        send.reputation = 100
        send.save()
        send.military.save()
        result = nukes(**{'nation': send, 'target': rec})
        self.assertEqual(send.military.nukes, 0, msg="Shouldn't have nukes after transfer")
        self.assertEqual(rec.military.nukes, 1, msg="Nuke didn't transfer")
        self.assertGreater(100, send.reputation, msg="Reputation didn't subtract")
        self.log_check(send, rec)


    def test_value_setting_base(self):
        value = get_value('rm', 1)
        price = Market.objects.latest().rmprice
        self.assertEqual(value, price, msg="Value should be market price")


    def test_value_setting_low(self):
        for x in range(10):
            Marketofferlog.objects.create(
                sold="uranium", 
                bought="budget", 
                sold_amount=1, 
                bought_amount=1500)
        value = get_value("uranium", 1)
        self.assertGreater(value, 1500, msg="Minimum value of uranium is 5000")


    def test_value_setting_low(self):
        for x in range(10):
            Marketofferlog.objects.create(
                sold="uranium", 
                bought="budget", 
                sold_amount=1, 
                bought_amount=7500)
        value = get_value("uranium", 1)
        self.assertGreater(value, 5000)

