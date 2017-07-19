from django.db.models.signals import post_save
from django.dispatch import receiver
from nation.models import Nation, Alliance, Initiatives, Permissiontemplate, Bank, Bankstats


@receiver(post_save, sender=Alliance, dispatch_uid='nation.signals.alliance_creation')
def alliance_creation(sender, instance, created, **kwargs):
    #This handles populating related tables for alliance creation
    #this has the advantage that testing and shell actions doesn't need to explicitly set
    #related tables and such
    if created:
        Initiatives.objects.create(alliance=instance)
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



