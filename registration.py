from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.views.generic.base import TemplateView
from nation.decorators import nologin_required
from .models import *
import random
import string
from django.core.mail import send_mail
from .registrationforms import *
from nation.decorators import nologin_required




@nologin_required
def register(request):
    context = {}
    result = ''
    print request.POST
    if request.method == 'POST':
        form = registrationform(request.POST)
        if 'submit' in request.POST:
            if form.is_valid():
                if User.objects.filter(email=form.cleaned_data['email']).exists():
                    result = "Player with that email already exists"
                else:
                    if Confirm.objects.filter(email=form.cleaned_data['email']).exists():
                        result = "An email has already been sent to %s!" % form.cleaned_data['email']
                    else:
                        reg = Confirm.objects.create(email=form.cleaned_data['email'])
                        result = send_registrationmail(reg)  
            else:
                result = 'Not a valid email'

        elif 'retry' in request.POST:
            print "retried"
            if form.is_valid():
                try:  
                    reg = Confirm.objects.get(email=form.cleaned_data['email'])
                except:
                    result = "Email doesn't exist!"
                else:
                    result = send_registrationmail(reg)
                    print result
                    if result[0] == 'S':
                        result = "Signup email has been re-sent!"
            else:
                result = 'Not a valid email'
    context.update({
        'form': registrationform(),
        'result': result,
        })
    print context
    return render(request, 'registration/register.html', context)


def send_registrationmail(reg):
    msg = tmp.replace('activationlink', reg.code)
    mails = send_mail('Cold Conflict account signup', msg, "admin@coldconflict.com", [reg.email])
    if mails > 0: #if django successfully sent the email
        result = "Signup email has been sent!"
    else:
        result = "An error occured when trying to send the email. If this problem persists please contact the admin."
    return result

@nologin_required
def newuser(request, regid):
    context = {'form': newuserform()}
    try:
        con = Confirm.objects.get(code=regid)
    except:
        return render(request, 'registration/newnation.html', {'result': 'Registration code invalid'})        
    if request.method == 'POST':
        nationid = ID.objects.get(pk=1)
        form = newuserform(request.POST)
        if form.is_valid():
            while True:
                if Nation.objects.filter(index=nationid.index).exists():
                    nationid.index += 1
                else:
                    break
            user = User.objects.create(
                username=form.cleaned_data['username'],
                email=con.email)
            user.set_password(form.cleaned_data['password'])
            user.save()
            nation = Nation.objects.create(user=user, 
                index=nationid.index,
                name=form.cleaned_data['name'],
                creationip=request.META.get('REMOTE_ADDR'),
                government=form.cleaned_data['government'],
                economy=form.cleaned_data['economy'],
                subregion=form.cleaned_data['subregion'])
            Settings.objects.create(nation=nation)
            IP.objects.create(nation=nation, IP=request.META.get('REMOTE_ADDR'))
            Military.objects.create(nation=nation)
            Econdata.objects.create(nation=nation)
            Researchdata.objects.create(nation=nation)
            context.update({'result': "Your nation has been successfully created!"})
            #now we log the user in ;)
            user = authenticate(username=user.username, 
                password=form.cleaned_data['password'])
            login(request, user)
        else:
            return render(request, 'registration/newnation.html', {'form': form})
    return render(request, 'registration/newnation.html', context)


@login_required
def log_out(request):
    logout(request)
    return redirect('index')

@nologin_required
def log_in(request):
    if request.method == 'POST':
        form = loginform(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            try:
                user = User.objects.get(email__iexact=username)
            except:
                try:
                    user = User.objects.get(username__iexact=username)
                except:
                    pass
                else:
                    username = user.username
            else:
                username = user.username
            user = authenticate(username=username, 
                password=form.cleaned_data['password'])
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return redirect('nation:main')
                else:
                    return render(request, 'registration/login.html', {'inactive': True})
            else:
                return render(request, 'registration/login.html', {'incorrect': True})
    return render(request, 'registration/login.html', {'form': loginform()})


@nologin_required
def recover(request):
    context = {'form': emailform()}
    if request.method == "POST":
        form = emailform(request.POST)
        if form.is_valid():
            q = User.objects.filter(email__iexact=form.cleaned_data['email'])
            if q:
                user = q[0]
                a = Recovery.objects.create(user=user)
                recovermsg = recovertemplate.replace('insert', a.code)
                send_mail('Password recovery request', recovermsg, 'admin@coldconflict.com', [user.email])
                context.update({'result': 'An email has been sent!'})
            else:
                context.update({'result': 'There is no user with that email!'})
        else:
            context.update({'result': 'Not a valid email!'})
    return render(request, 'registration/recovery.html', context)


def complete_recover(request, recid):
    try:
        rec = Recovery.objects.get(code=recid)
    except:
        return render(request, 'registration/recover.html', {'result': 'Invalid password recovery token'})
    context = {'form': newpasswordform()}
    if request.POST:
        form = newpasswordform(request.POST)
        if form.is_valid():
            rec.user.set_password(form.cleaned_data['password'])
            rec.user.save()
            rec.delete()
            context.update({'result': 'Password for %s has successfully been reset!' % rec.user.username})
            return render(request, 'registration/recover.html', context)
        else:
            context.update({'result': 'Password is invalid (too long or short)'})
            render(request, 'registration/recover.html', context)
    return render(request, 'registration/recover.html', context)



recovertemplate = """Follow the link to reset your password
http://coldconflict.com/recover/insert
"""

tmp = """You (or someone pretending to be you) have asked to register an account at
http://coldconflict.com.  If this wasn't you, please ignore this email
and your address will be removed from our records.

To complete registration, please click the following link within the next 
7 days:

http://coldconflict.com/register/new/activationlink

Sincerely,
The badmin"""

tmpcret = """
    Thank you for signing up to Cold Conflict! Your username is $user and your
    generated password is $pass, and can
    be changed at any time in your user settings.
"""