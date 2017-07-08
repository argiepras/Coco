from django.db.models.signals import post_save
from django.dispatch import reciever
from nation.models import Nation, Initiatives, Permissiontemplate, Bank, Bankstats


@reciever(post_save, sender=Alliance, dispath_uid='nation.signals.alliance_creation')
def alliance_creation(sender, instance, created, **kwargs):
    #This handles populating related tables for alliance creation
    #this has the advantage that testing and shell actions doesn't need to explicitly set
    #related tables and such
    if created:
        nation = Nation.objects.get(name=instance.founder)
        nation.alliance = instance
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
        instance.permissions.create(member=nation, template=ft)
        nation.save(update_fields=['alliance'])



