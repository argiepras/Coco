from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^new$', views.newnation, name='new'),
    url(r'^(?P<url>[a-zA-Z0-9_-]+)$', views.nation_page, name='nationpage'),
]