from django.conf.urls import url
from . import views
from . import intelligence
from .policies import views as policyviews

urlpatterns = [
    url(r'^$', views.main, name='main'),
    url(r'^comms/$', views.commpage, name='comms'),
    url(r'^comms/sent/$', views.sentcomms, name='sentcomms'),
    url(r'^foreign/$', policyviews.foreignpolicies, name='foreign'),
    url(r'^economic/$', policyviews.econ_policies, name='economic'),
    url(r'^military/$', policyviews.militarypolicies, name='military'),
    url(r'^domestic/$', policyviews.domesticpolicies, name='domestic'),
    url(r'^intelligence/$', intelligence.overview, name='intelligence'),
    url(r'^intelligence/(?P<spyid>[0-9]+)$', intelligence.details, name='spy'),
    url(r'^intelligence/discovered$', intelligence.discoveredagents, name='discovered'),
    url(r'^research/$', views.research, name='research'),
    url(r'^settings/$', views.settings, name='settings'),
    url(r'^news/$', views.newspage, name='news'),
    url(r'^new/$', views.new_nation, name='new'),
    url(r'^reset/$', views.reset_nation, name='reset'),
]