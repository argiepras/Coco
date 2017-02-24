from django.conf.urls import url, include
from . import alliances


urlpatterns = [
    url(r'^rankings/(?P<page>[0-9]+)/$', alliances.alliancerankings, name='rankings'),
    url(r'^main/$', alliances.main, name='main'),
    url(r'^new/$', alliances.newalliance, name='new'),
    url(r'^declarations/(?P<page>[0-9]+)/$', alliances.alliancedeclarations, name='declarations'),
    url(r'^main/chat/(?P<page>[0-9]+)/$', alliances.chat, name='chat'),
    url(r'^main/statistics/$', alliances.stats, name='stats'),
    url(r'^(?P<alliancepk>[0-9]+)/$', alliances.alliancepage, name="alliance_page"),
    url(r'^main/bank/(?P<page>[0-9]+)/$', alliances.bankinterface, name="bank"),
    url(r'^main/control_panel/$', alliances.control_panel, name="control_panel"),
    url(r'^main/control_panel/change/$', alliances.change, name="templates"),
    url(r'^main/control_panel/applications/$', alliances.applications, name="applications"),
    url(r'^main/control_panel/invites/$', alliances.invites, name="invites"),
    ]