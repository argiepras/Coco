from django.http import HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.core.exceptions import ObjectDoesNotExist

def nologin_required(f):
    #Checks if the user has a nation, for redirect purposes.
    def wrap(request, *args, **kwargs):
        if request.user.is_anonymous():
            return f(request, *args, **kwargs)
        else:
            return redirect('nation:main')
    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap

#for alliance related stuff that requires an alliance
def alliance_required(f):
    def wrap(request, *args, **kwargs):
        if not request.user.nation.has_alliance():
            return redirect('nation:main')
        return f(request, *args, **kwargs)
    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap

def officer_required(f):
    def wrap(request, *args, **kwargs):
        if not request.user.nation.permissions.panel_access():
            return redirect('alliance:main')
        return f(request, *args, **kwargs)
    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap

def nation_required(f):
    def wrap(request, *args, **kwargs):
        try:
            request.user.nation
        except:
            return redirect('nation:new')
        if request.user.nation.reset:
            return redirect('nation:reset')
        return f(request, *args, **kwargs)
    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap

def nonation_required(f):
    def wrap(request, *args, **kwargs):
        try:
            request.user.nation
        except:
            return f(request, *args, **kwargs)
        return redirect('nation:main')
    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap

def reset_required(f):
    def wrap(request, *args, **kwargs):
        try:
            request.user.nation
        except:
            return redirect('nation:new')
        if request.user.nation.reset:
            return f(request, *args, **kwargs)
        return redirect('nation:main')
    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap

def novacation(f):
    def wrap(request, *args, **kwargs):
        if request.user.nation.vacation:
            return redirect('nation:main')
        return f(request, *args, **kwargs)
    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap


def mod_required(f):
    @nation_required
    def wrap(request, *args, **kwargs):
        if request.user.nation.settings.mod:
            return f(request, *args, **kwargs)
        return redirect('nation:main')
    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap


def headmod_required(f):
    @mod_required
    def wrap(request, *args, **kwargs):
        if request.user.nation.settings.head_mod:
            return f(request, *args, **kwargs)
        return redirect('nation:main')
    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap