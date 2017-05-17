from nation.models import *
import nation.utilities as utils
import nation.variables as v



def creation_ip_nations(ip):
    nations = Nation.objects.actives().filter(creationip=ip)
    first = None
    if nations:
        first = nations.order_by('creationtime')[0]
    return nations, first

def correlated_ips(ipset): #queryset of IP objects

    # fetches a list of all nations associated with a given IP
    # by cross referencing all associated IPs with a given
    # ie any nation who has an IP associated with it that's also found
    # in the set of IPs associated with the nation associated with the given IP
    """
           IPs
            |
         nations
            |
         all IPs
            |
        all nations
    """
    nations = Nation.objects.actives().filter(IPs__IP__in=ipset).distinct()
    ips = IP.objects.filter(nation__in=nations)
    ips = [ip.IP for ip in ips]
    return Nation.objects.actives().filter(IPs__IP__in=ips).distinct(), ips


def deep_correlation(ipset):
    nations, ips = correlated_ips(ipset)
    count = nations.count()
    while True:
        nations, ips = correlated_ips(ips)
        if count < nations.count():
            count = nations.count()
            continue
        break
    return nations, ips


def IP_to_ip(ipset):
    return [ip.IP for ip in ipset]