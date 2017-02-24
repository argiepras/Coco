from django.conf.urls import url
from . import modviews

urlpatterns = [
    url(r'^$', modviews.main, name='main'),
    url(r'^mods/$', modviews.mods, name='mods'),
    url(r'^mod/(?P<modid>[0-9]+)/$', modviews.mod, name='mod'),
    url(r'^war/(?P<war_id>[0-9]+)/$', modviews.wardetails, name='war'),
    url(r'^reports/overview/(?P<page>[0-9]+)/$', modviews.reports, name='reports'),
    url(r'^reports/(?P<report_id>[0-9]+)/$', modviews.reportpage, name='report'),
    url(r'^nations/(?P<nation_id>[a-zA-Z0-9_-]+)/$', modviews.nation_page, name='nation'),
    url(r'^nations/(?P<nation_id>[a-zA-Z0-9_-]+)/actions/(?P<page>[0-9]+)/$', modviews.nation_actions, name='nation_actions'),
    url(r'^nations/(?P<nation_id>[a-zA-Z0-9_-]+)/incoming/(?P<page>[0-9]+)/$', modviews.nation_incoming, name='nation_incoming'),
    url(r'^nations/(?P<nation_id>[a-zA-Z0-9_-]+)/outgoing/(?P<page>[0-9]+)/$', modviews.nation_outgoing, name='nation_outgoing'),
    url(r'^nations/(?P<nation_id>[a-zA-Z0-9_-]+)/allaid/(?P<page>[0-9]+)/$', modviews.nation_allaid, name='nation_allaid'),
    url(r'^nations/(?P<nation_id>[a-zA-Z0-9_-]+)/wars/(?P<page>[0-9]+)/$', modviews.nation_wars, name='nation_wars'),
    url(r'^nations/(?P<nation_id>[a-zA-Z0-9_-]+)/logins/(?P<page>[0-9]+)/$', modviews.nation_logins, name='nation_logins'),
    url(r'^nations/(?P<nation_id>[a-zA-Z0-9_-]+)/reports/(?P<page>[0-9]+)/$', modviews.nation_reports, name='nation_reports'),
    url(r'^nations/(?P<nation_id>[a-zA-Z0-9_-]+)/IPs/$', modviews.iplogs, name='nation_IPs'),
    url(r'^nations/overview/(?P<page>[0-9]+)/$', modviews.nation_overview, name='nations'),
]