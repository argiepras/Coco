from django.contrib import admin
from nation.models import *
# Register your models here.




class econ(admin.StackedInline):
    model = Econdata

class mil(admin.StackedInline):
    model = Military

class research(admin.StackedInline):
    model = Researchdata

admin.site.register(War)

class nation(admin.ModelAdmin):
    model = Nation
    inlines = [econ, research, mil]


admin.site.register(Nation, nation)


class alliance(admin.ModelAdmin):
    model = Alliance


admin.site.register(Alliance, alliance)