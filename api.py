from django.conf.urls import url
from nation.aid import incoming
from nation.ajax import stats

urlpatterns = [
    url(r'^aid/', incoming, name="aid"),
    url(r'^stats/', stats, name="stats"),

]