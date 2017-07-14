from __future__ import unicode_literals

from django.apps import AppConfig


class NationConfig(AppConfig):
    name = 'nation'

    def ready(self):
        #this registers the signal handling functions
        #so they actually recieve the signals sent by django
        from nation.signals import *