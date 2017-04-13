from django.conf.urls import url
from . import views
from . import intelligence
from . import policies

urlpatterns = [
    url(r'^$', views.main, name='main'),
    url(r'^comms/(?P<page>[0-9]+)/$', views.commpage, name='comms'),
    url(r'^comms/sent/(?P<page>[0-9]+)/$', views.sentcomms, name='sentcomms'),
    url(r'^foreign/$', policies.foreignpolicies, name='foreign'),
    url(r'^economic/$', policies.economicpolicies, name='economic'),
    url(r'^military/$', policies.militarypolicies, name='military'),
    url(r'^domestic/$', policies.domesticpolicies, name='domestic'),
    url(r'^intelligence/$', intelligence.overview, name='intelligence'),
    url(r'^intelligence/(?P<spyid>[0-9]+)$', intelligence.details, name='spy'),
    url(r'^intelligence/discovered$', intelligence.discoveredagents, name='discovered'),
    url(r'^research/$', views.research, name='research'),
    url(r'^settings/$', views.settings, name='settings'),
    url(r'^news/$', views.newspage, name='news'),
    url(r'^new/$', views.new_nation, name='new'),
    url(r'^reset/$', views.reset_nation, name='reset'),
]