from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from nation.models import *


@receiver(post_save, sender=Alliance, dispatch_uid='nation.signals.alliance_creation')
def alliance_creation(sender, instance, created, **kwargs):
    #This handles populating related tables for alliance creation
    #this has the advantage that testing and shell actions doesn't need to explicitly set
    #related tables and such
    if created:
        ini = Initiatives.objects.create(alliance=instance)
        Timers.objects.create(initiatives=ini)
        Bank.objects.create(alliance=instance)
        Bankstats.objects.create(alliance=instance)
        ft = instance.templates.create()
        instance.templates.create(title='member') #default rank is 5
        instance.templates.create(title='officer',
                                    kick=True, 
                                    mass_comm=True, 
                                    invite=True, 
                                    applicants=True, 
                                    rank=3, 
                                    promote=True)
        if instance.founder != 'admin':
            nation = Nation.objects.get(name=instance.founder)
            nation.alliance = instance
            instance.permissions.create(member=nation, template=ft)
            instance.memberstats.create(nation=nation)
            nation.invites.all().delete()
            nation.applications.all().delete()
            nation.save(update_fields=['alliance'])



@receiver(post_save, sender=Nation, dispatch_uid='nation.signals.nation_creation')
def nation_creation(sender, instance, created, **kwargs):
    if created:
        if instance.index == 0:
            x = ID.objects.get_or_create()[0]
            instance.index = x.index
            x.next()
            instance.save(update_fields=['index'])
        Settings.objects.create(nation=instance)
        Military.objects.create(nation=instance)
        Econdata.objects.create(nation=instance)
        Researchdata.objects.create(nation=instance)
        Multimeter.objects.create(nation=instance)
        instance.news.create(content='newbie_event', event=True)


#easiest way to completely reset a snapshot, circumventing defaults
@receiver(pre_save, sender=Snapshot, dispatch_uid='nation.signals.snapshot_creation')
def create_snapshot(*args, **kwargs):
    instance = kwargs['instance']
    for field in Snapshot._meta.fields:
        if getattr(instance, field.name) == field.default:
            setattr(instance, field.name, 0)
