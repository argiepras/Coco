from .models import *
from .registrationforms import loginform
from . import variables as v


#creates a dictionary available to every template rendered ever
def boilerplate(request):
    c = {'mobile': request.mobile}
    if request.user.is_anonymous():
        c.update({'logged_in': False, 'login_form': loginform()})
    else:
        c.update({'logged_in': True})
        try:
            nation = request.user.nation
            stats = {}
            commcount = nation.comms.all().filter(unread=True).count()
            for resource in v.resources: #list of resources displayed in the footer
                stats.update({resource: nation.__dict__[resource]})
            for region in v.regionshort:
                if v.regionshort[region] == nation.subregion:
                    c.update({'subreg': region})
            stats.update({'research': nation.research, 'weapons': nation.military.weapons})
            c.update({
                'stats': stats, 
                'nation': nation, 
                'commcount': commcount,
                'username': request.user.username,
                'newscount': nation.news.all().filter(seen=False).count(),
                'alliancedeclarations': Alliancedeclaration.objects.all().count(),
                'globaldecs': Declaration.objects.filter(region='none').count(), 
                'regionaldecs': Declaration.objects.filter(region=nation.region()).count(), 
                'marketoffers': Marketoffer.objects.all().count(),
                'onlineleaders': Nation.objects.filter(last_seen__gte=v.onlineleaders()).count(),
                'curtime': v.now(),
            })
            try:
                c.update({'alliancename': nation.member.alliance.name, 'allydecs': nation.member.alliance.declarations.all().count()})
            except:
                c.update({'has_alliance': False})
        except:
            c.update({'nonation': True})
            pass #no nation means nation creation page
    return c
    