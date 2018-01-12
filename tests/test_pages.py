from django.test import TestCase, Client

"""
Basic tests of urls, mostly checking that they are redirecting when they should
and they don't return 500 errors
pages to test:
index/
api?
nations/<index>
main/
    comms/
    comms/sent/
    foreign/
    economic/
    military/
    domestic/
    intelligence/
    intelligence/<spy id>
    intelligence/discovered       ?
    settings/
    news/
    new/
    reset/
modcenter/
    stuff here
market/
    offers/
alliances/
    /rankings
    /main
    /new
    /main/chat
    /main/statistics
    /<alliance id>
    /main/bank
    /main/control_panel
    /main/control_panel/change
    /main/applications
    /main/invites
register/
logout/
login/
map/
recover/
rankings/
rankings/<region>
declarations/
regiondiscussion/
chat/
legal/
about/
news/
"""



class logged_out(TestCase):
