from nation.models import Nation, Military

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

@login_required
def stats(request):
    nationstats = Nation.objects.filter(user=request.user).values(
            'budget', 
            'rm', 
            'mg', 
            'food', 
            'oil',
            'research').get() #returns a dictionary with these stats
    nationstats.update(Military.objects.filter(nation__user=request.user).values('weapons').get())
    return JsonResponse(nationstats)