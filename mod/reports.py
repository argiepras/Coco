from django.shortcuts import render, redirect
from django.db.models import Count, Q
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.core.paginator import *
from django.http import HttpResponseRedirect

from nation.models import *
from nation.decorators import mod_required, headmod_required
from .forms import *
import nation.utilities as utils
import nation.variables as v



## General overview page for reports made by players
## Actions made

@mod_required
def reports(request, page):
    context = {}
    nation = request.user.nation
    result = False
    if request.method == "POST":
        if 'claim' in request.POST:
            claimed = Report.objects.get(pk=request.POST['claim'])
            result = claim(claimed, nation)

        elif 'release' in request.POST:
            claimed = nation.investigated.get(pk=request.POST['release'])
            claimed.investigator = None
            claimed.save(update_fields=['investigator'])
            result = "Report has been released."


    reportquery = Report.objects.all().order_by('investigated')
    paginator, actionlist = utils.paginate_me(reportquery, 50, page)
    context.update({
            'result': result,
            'pages': utils.pagination(paginator, actionlist),
            'reports': actionlist,
        })

    return render(request, 'mod/reports.html', context)

@mod_required
def reportpage(request, report_id):
    context = {}
    result = False
    nation = request.user.nation
    try:
        report = Report.objects.get(pk=report_id)
    except:
        return render(request, 'mod/reportpage.html', {'notfound': True})
    if request.method == "POST":
        if 'claim' in request.POST:
            result = claim(report, nation)

        elif 'release' in request.POST:
            report.investigator = None
            report.save(update_fields=['investigator'])
            result = "Report has been released."

        elif 'close' in request.POST:
            form = closereportform(request.POST)
            if form.is_valid():
                report.investigated = True
                report.conclusion = form.cleaned_data['conclusion']
                report.guilty = form.cleaned_data['guilty']
                report.save()
                result = "Report has been closed"
            else:
                result = "invalid POST data (forget a reason?)"
    context.update({
        'result': result,
        'report': report,
        'closereportform': closereportform(),
    })
    return render(request, 'mod/reportpage.html', context)




def claim(report, claimee):
    if report.open():
        report.investigator = claimee
        report.save(update_fields=['investigator'])
        result = "Report has been claimed."
    else:
        result = "This report has already been claimed by %s!" % report.investigator.name
    return result