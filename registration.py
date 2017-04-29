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
    msg = emailtemplate.replace('{{ headline }}', 'Account sign up')
    content = tmp.replace('activationlink', reg.code)
    msg = msg.replace('{{ content }}', content)
    mails = send_mail('Cold Conflict account signup', '', "admin@coldconflict.com", [reg.email], html_message=msg)
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
            if 'id' in form.cleaned_data:
                index = form.cleaned_data['id']
            try:
                index = int(index)
            except:
                while True:
                    if Nation.objects.filter(index=nationid.index).exists():
                        nationid.index += 1
                    else:
                        index = nationid.index
                        nationid.save(update_fields=['index'])
                        break
            user = User.objects.create(
                username=form.cleaned_data['username'],
                email=con.email)
            user.set_password(form.cleaned_data['password'])
            user.save()
            nation = Nation.objects.create(user=user, 
                index=index,
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
            nation.news.create(content='newbie_event', event=True)
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
    request.user.nation.logout_times.create(IP=request.META.get('REMOTE_ADDR'))
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
                    try:
                        user.nation
                    except:
                        pass
                    else:
                        user.nation.login_times.create(IP=request.META.get('REMOTE_ADDR'))
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
                recovermsg = emailtemplate.replace('{{ headline }}', 'Password recovery')
                recovermsg = recovermsg.replace('{{ content }}', recovertemplate.replace('insert', a.code))
                send_mail('Password recovery request', '', 'admin@coldconflict.com', [user.email], html_message=recovermsg)
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



recovertemplate = """So you've forgotten your password huh? Simply follow <a href="http://coldconflict.com/recover/insert" style="color: rgb(255, 238, 227)"><b>this link</b></a>
    in order to reset your password</a>
        
"""

tmp = """You (or someone pretending to be you) have asked to register an account at
http://coldconflict.com.  If this wasn't you, please ignore this email
and your address will be removed from our records.

To complete registration, simply click below within the next 
7 days:
    <center>
    <a href="http://coldconflict.com/register/new/activationlink">
                    <button style="color: rgb(255, 238, 227); background-color: rgba(255, 238, 227, 0.2);
                      padding: 8px 12px;
                      font-size: 16px;
                      border: 0px solid transparent;
                      border-radius: 4px;
                      margin: 50px;">
                        Create nation
                    </button>
                </a>
    </center>
"""

emailtemplate = """
<center>
<table style="width: 100%" background="http://coldconflict.com/static/img/emailbackground.jpg">
    <tr><td><center>
    <table style="width: 600px; border-radius: 5px; background-color: rgba(10, 10, 10, 0.5); padding: 10px; font-family: Droid Sans,Helvetica Neue, Helvetica,Arial,sans-serif">
        <tr>
            <td style="background-color: rgba(23, 21, 20, 0.4); padding: 10px;">
            <center>
                <img src="http://coldconflict.com/static/assets/logo.png">
            </center>
            </td>
        </tr>
        <tr>
            <td>
                <center>
                    <p class="headline">
                        <h1 style="color: rgb(255, 238, 227); padding: 10px;">
                            {{ headline }}
                        </h1>
                    </p>
                </center>
            </td>
        </tr>
        <tr>
            <td>
                <p style="color: rgb(255, 238, 227); padding: 10px;">
                    {{ content }}
                </p>
            </td>
        </tr>
    </table>
</center></td></tr>
</table>"""