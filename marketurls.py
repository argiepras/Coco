from django.conf.urls import url, include
from nation.market import free_market, offers

urlpatterns = [
    url(r'^$', free_market, name="main"),
    url(r'^offers/(?P<page>[0-9]+)/$', offers, name='offers'),
    
]