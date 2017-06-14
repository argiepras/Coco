from nation.models import *
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
import nation.utilities as utils
from nation.decorators import nation_required, novacation
import nation.variables as v
import json


@login_required
@nation_required
@novacation
def econ_policies(request):
    if request.is_ajax():
        return ajax_handling(request)
    from .economic import Policy
    nation = request.user.nation
    policies = get_policies(Policy.registry, nation, 'economic')
    return render(request, 'nation/economics.html', {'policies': policies})


def militarypolicies(request):
    if request.is_ajax():
        return ajax_handling(request)
    from .military import Policy
    nation = request.user.nation
    policies = get_policies(Policy.registry, nation, 'military')
    return render(request, 'nation/economics.html', {'policies': policies})


def domesticpolicies(request):
    if request.is_ajax():
        return ajax_handling(request)
    from .domestic import Policy
    nation = request.user.nation
    policies = get_policies(Policy.registry, nation, 'domestic')
    return render(request, 'nation/economics.html', {'policies': policies})


def foreignpolicies(request):
    if request.is_ajax():
        return ajax_handling(request)
    from .foreign import Policy
    nation = request.user.nation
    policies = get_policies(Policy.registry, nation, 'foreign')
    return render(request, 'nation/economics.html', {'policies': policies})


def ajax_handling(request):
    from .economic import Policy
    from . import domestic
    from . import military
    from . import foreign
    policy = Policy.registry[request.POST['policy']](request.user.nation)
    if policy.can_apply():
        policy.enact()
        rval = policy.json()
    else:
        rval = {'result': "It won't work."}
    if policy.can_apply() == False and policy.contextual == False:
        rval = {'result': policy.result, 'img': policy.img}
    print rval
    return JsonResponse(rval)




def get_policies(registry, nation, ptype):
    p = []
    for policy in registry:
        x = registry[policy](nation)
        if (x.can_apply() or x.contextual == False) and x.policytype == ptype:
            p.append(x)
    return p