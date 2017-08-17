from django.conf.urls import url, include
from . import views
from .control_panel import view, change

urlpatterns = [
    url(r'^rankings/$', views.alliancerankings, name='rankings'),
    url(r'^main/$', views.main, name='main'),
    url(r'^new/$', views.newalliance, name='new'),
    url(r'^declarations/$', views.alliancedeclarations, name='declarations'),
    url(r'^main/chat/$', views.chat, name='chat'),
    url(r'^main/statistics/$', views.stats, name='stats'),
    url(r'^(?P<alliancepk>[0-9]+)/$', views.alliancepage, name="alliance_page"),
    url(r'^main/bank/$', views.bankinterface, name="bank"),
    url(r'^main/control_panel/$', view, name="control_panel"),
    url(r'^main/control_panel/change/$', change, name="templates"),
    url(r'^main/applications/$', views.applications, name="applications"),
    url(r'^main/invites/$', views.invites, name="invites"),
    ]