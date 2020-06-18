from django.conf.urls import url
from . import views
from . import detailviews
from . import reports

urlpatterns = [
    url(r'^$', views.main, name='main'),
    url(r'^mods/$', views.mods, name='mods'),
    url(r'^mod/(?P<modid>[0-9]+)/$', views.mod, name='mod'),
    url(r'^wars/$', views.wars, name='wars'),
    url(r'^war/(?P<war_id>[0-9]+)/$', views.wardetails, name='war'),
    url(r'^reports/$', reports.reports, name='reports'),
    url(r'^reports/(?P<report_id>[0-9]+)/$', reports.reportpage, name='report'),
    url(r'^nations/(?P<nation_id>[a-zA-Z0-9_-]+)$', views.nation_page, name='nation'),
    url(r'^nations/(?P<nation_id>[a-zA-Z0-9_-]+)/actions/$', detailviews.nation_actions, name='nation_actions'),
    url(r'^nations/(?P<nation_id>[a-zA-Z0-9_-]+)/aid$', detailviews.aidpage, name='nation_aid'),
    url(r'^nations/(?P<nation_id>[a-zA-Z0-9_-]+)/wars/$', detailviews.nation_wars, name='nation_wars'),
    url(r'^nations/(?P<nation_id>[a-zA-Z0-9_-]+)/logins/$', detailviews.nation_logins, name='nation_logins'),
    url(r'^nations/(?P<nation_id>[a-zA-Z0-9_-]+)/reports/$', detailviews.nation_reports, name='nation_reports'),
    url(r'^nations/(?P<nation_id>[a-zA-Z0-9_-]+)/IPs/$', detailviews.iplogs, name='nation_IPs'),
    url(r'^nations/$', views.nation_overview, name='nations'),
    url(r'^IP/(?P<ip>[0-9.]+)/$', views.ipview, name="ip_view"),
]