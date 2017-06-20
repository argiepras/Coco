from django.conf.urls import url
from nation.aid import incoming

urlpatterns = [
    url(r'^aid/', incoming, name="aid"),
]