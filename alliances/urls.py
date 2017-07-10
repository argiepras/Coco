from django.conf.urls import url, include
from . import views


urlpatterns = [
    url(r'^rankings/$', views.alliancerankings, name='rankings'),
    url(r'^main/$', views.main, name='main'),
    url(r'^new/$', views.newalliance, name='new'),
    url(r'^declarations/$', views.alliancedeclarations, name='declarations'),
    url(r'^main/chat/$', views.chat, name='chat'),
    url(r'^main/statistics/$', views.stats, name='stats'),
    url(r'^(?P<alliancepk>[0-9]+)/$', views.alliancepage, name="alliance_page"),
    url(r'^main/bank/(?P<page>[0-9]+)/$', views.bankinterface, name="bank"),
    url(r'^main/control_panel/$', views.control_panel, name="control_panel"),
    url(r'^main/control_panel/change/$', views.change, name="templates"),
    url(r'^main/control_panel/applications/$', views.applications, name="applications"),
    url(r'^main/control_panel/invites/$', views.invites, name="invites"),
    ]