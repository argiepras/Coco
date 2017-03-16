from django import forms
import nation.variables as v
from django.contrib.auth.models import User
from nation.models import Nation

class registrationform(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'placeholder': 'Email',
        'class': 'form-control',
        }))
    username = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'placeholder': 'Username'}))

class loginform(forms.Form):
    username = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'placeholder': 'Username or Email', 'class': 'form-control'}))
    password = forms.CharField(max_length=30, widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'class': 'form-control'}))

class newpasswordform(forms.Form):
        password = forms.CharField(max_length=30, widget=forms.PasswordInput(attrs={
            'placeholder': 'New password', 
            'class': 'form-control',
            'style': 'color: black;',
            }))

class emailform(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(
        attrs={
            'placeholder': 'Enter your email',
            'class': 'form-control',}
            ))


class newuserform(forms.Form):
    def __init__(self, *args, **kwargs):
        super(newuserform, self).__init__(*args, **kwargs)
        regions = []
        governments = []
        economy = []
        #this is a hack of sorts, I'm too lazy to type out all dis shit again
        #plus this makes it so changing the structure in variables
        #means you don't have to change this
        for region in v.regions:
            for subregion in v.regions[region]:
                regions.append((subregion, subregion))
        for key in v.government:
            governments.append(((key*20)+10, v.government[key]))
        for markettype in v.economy:
            economy.append(((markettype+1)*25, v.economy[markettype]))

        economy = tuple(economy)
        governments = tuple(governments)
        regions = tuple(regions)
        self.fields['government'] = forms.ChoiceField(
            choices=governments, 
            label="Government Type",
            widget=forms.Select(attrs={'class': 'form-control'}))
        self.fields['subregion'] = forms.ChoiceField(
            choices=regions, 
            label="Region",
            widget=forms.Select(attrs={'class': 'form-control'}))
        self.fields['economy'] = forms.ChoiceField(
            choices=economy, 
            label="Economy Type",
            widget=forms.Select(attrs={'class': 'form-control'}))

    username = forms.CharField(max_length=50, widget=forms.TextInput(attrs={
        'placeholder': 'Leader name', 
        'class': 'form-control',
        })) 
    name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={
        'placeholder': 'Nation name',
        'class': 'form-control',
        }))
    password = forms.CharField(max_length=40, widget=forms.PasswordInput(attrs={
        'placeholder': 'Password',
        'class': 'form-control',
        }))
    password2 = forms.CharField(max_length=40, widget=forms.PasswordInput(attrs={
        'placeholder': 'Confirm password',
        'class': 'form-control',
        }))

    def clean(self):
        cleaned_data = super(newuserform, self).clean()
        if cleaned_data.get("password") != cleaned_data.get("password2"):
            self.add_error('password', 'Passwords must match')

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('Username is taken!')
        return username

    def clean_name(self):
        name = self.cleaned_data['name']
        if Nation.objects.filter(name__iexact=name).exists():
            raise forms.ValidationError('Nation name is taken!')
        return name
