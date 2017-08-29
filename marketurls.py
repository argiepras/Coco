from django.conf.urls import url, include
from nation.market import free_market, offers

urlpatterns = [
    url(r'^$', free_market, name="main"),
    url(r'^offers/$', offers, name='offers'),
    
]