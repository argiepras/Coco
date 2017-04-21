from models import *
from django import forms
from . import variables as v

class anthemform(forms.Form):
    anthem = forms.CharField(max_length=15, widget=forms.TextInput(attrs={
        'placeholder': 'New anthem', 'class': 'form-control', 'style': 'color: black',}))

class flagform(forms.Form):
    flag = forms.CharField(max_length=100, widget=forms.TextInput(attrs={
        'placeholder': 'New flag URL', 'class': 'form-control', 'style': 'color: black',}))

class declarationform(forms.Form):
    message = forms.CharField(max_length=400, widget=forms.Textarea(attrs={
        'placeholder': 'Enter your message.', 'class': 'form-control', 'style': 'height: 150px; color: black;'}))


class masscommform(forms.Form):
    message = forms.CharField(max_length=500, widget=forms.Textarea(attrs={
        'placeholder': 'Enter your alliance-wide message', 'class': 'form-control', 'style': 'height: 150px; color: black;'}))

class newallianceform(forms.Form):
    name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={
        'placeholder': 'Alliance name', 'class': 'form-control'}))
    member_title = forms.CharField(max_length=30, widget=forms.TextInput(attrs={
        'placeholder': 'Member title', 'class': 'form-control'}))
    founder_title = forms.CharField(max_length=30, widget=forms.TextInput(attrs={
        'placeholder': 'Founder title', 'class': 'form-control'}))
    description  = forms.CharField(max_length=1000, widget=forms.Textarea(attrs={
        'placeholder': 'Enter description', 'class': 'form-control', 'style': 'height: 150px; color: black;'}))


class inviteform(forms.Form):
    name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={
        'placeholder': 'Nation name, ID or player name', 'class': 'form-control', 'style': 'color: black;'}))

class heirform(forms.Form):
    def __init__(self, nation, *args, **kwargs):
        super(heirform, self).__init__(*args, **kwargs)
        query = nation.alliance.members.all().filter(permissions__template__officer=True).exclude(pk=nation.pk)
        self.fields['heir'] = forms.ModelChoiceField(queryset=query, widget=forms.Select(attrs={
            'class': 'form-control', 'style': 'color: black;'}))

class descriptionform(forms.Form):
    content = forms.CharField(max_length=1000, widget=forms.Textarea(attrs={
        'placeholder': 'Enter new description', 'class': 'form-control', 'style': 'height: 150px; color: black;'}))


# Withdrawing and depositing limits are form enforced
# withdrawing limits are whatever is lower between nation withdrawal limit or bank stockpile


#base form for rendering
#using either a deposit or withdraw form could lead to problems with max values
#this has more redundant code but easier verification
class numberform(forms.Form):
    def __init__(self, *args, **kwargs):
        super(numberform, self).__init__(*args, **kwargs)
        for choice in v.depositchoices:
            self.fields[choice] = forms.IntegerField(
                min_value=1, 
                required=False,
                widget=forms.NumberInput(attrs={
                        'class': 'form-control', 
                        'placeholder': 'Amount', 
                        'style': 'color: black;'
                    }))



class depositform(forms.Form):
    def __init__(self, nation, *args, **kwargs):
        super(depositform, self).__init__(*args, **kwargs)
        for choice in v.depositchoices:
            self.fields[choice] = forms.IntegerField(
                min_value=1,
                max_value=nation.__dict__[choice],
                required=False,
                widget=forms.NumberInput(attrs={
                        'class': 'form-control', 
                        'placeholder': 'Deposit amount', 
                        'style': 'color: black;'
                    }))


    empty = forms.BooleanField(required=False)

    def clean(self):
        cleaned_data = super(depositform, self).clean()
        fields = []
        for field in cleaned_data:
            if cleaned_data[field] == None:
                fields.append(field)
        for field in fields:
            cleaned_data.pop(field)
        if len(cleaned_data) == 1:
            cleaned_data['empty'] = True
        return cleaned_data


class withdrawform(forms.Form):
    def __init__(self, nation, *args, **kwargs):
        super(withdrawform, self).__init__(*args, **kwargs)
        for choice in v.depositchoices:
            stockpile = nation.__dict__[choice]
            bankstock = nation.alliance.bank.__dict__[choice]
            if nation.alliance.bank.limit and not nation.permissions.template.founder:
                limit = nation.alliance.bank.__dict__['%s_limit' % choice] - nation.memberstats.__dict__[choice]
                maxwithdraw = (limit if limit < bankstock else bankstock)
            else:
                maxwithdraw = bankstock
            self.fields[choice] = forms.IntegerField(
                min_value=1, 
                max_value=maxwithdraw, 
                required=False,
                widget=forms.NumberInput(attrs={
                        'class': 'form-control', 
                        'placeholder': 'Deposit amount', 
                        'style': 'color: black;'
                    }))


    empty = forms.BooleanField(required=False)

    def clean(self):
        cleaned_data = super(withdrawform, self).clean()
        fields = []
        for field in cleaned_data:
            if cleaned_data[field] == None:
                fields.append(field)
        for field in fields:
            cleaned_data.pop(field)
        if len(cleaned_data) == 1:
            cleaned_data['empty'] = True
        return cleaned_data


class bankingform(forms.Form):
    choices = (
        ('per_nation', 'Total is per nation'),
        ('total', 'Total is alliance wide'),
        )
    per_nation = forms.ChoiceField(choices=choices, widget=forms.RadioSelect())
    budget_limit = forms.IntegerField(widget=forms.NumberInput(attrs={
        'class': 'form-control', 'style': 'color: black',
        }))
    mg_limit = forms.IntegerField(widget=forms.NumberInput(attrs={
        'class': 'form-control', 'style': 'color: black',
        }))
    rm_limit = forms.IntegerField(widget=forms.NumberInput(attrs={
        'class': 'form-control', 'style': 'color: black',
        }))
    food_limit = forms.IntegerField(widget=forms.NumberInput(attrs={
        'class': 'form-control', 'style': 'color: black',
        }))
    oil_limit = forms.IntegerField(widget=forms.NumberInput(attrs={
        'class': 'form-control', 'style': 'color: black',
        }))


#selecting permission templates for promote/alter/deletion
class permissionselectform(forms.Form):
    def __init__(self, nation, *args, **kwargs):
        super(permissionselectform, self).__init__(*args, **kwargs)
        if nation.permissions.template.founder:
            perms = nation.alliance.templates.all().exclude(rank=5)
        else:
            perms = nation.alliance.templates.all().filter(rank__lte=nation.permissions.rank).exclude(member_template=True)
        self.fields['template'] = forms.ModelChoiceField(queryset=perms, widget=forms.Select(attrs={
            'class': 'form-control', 'style': 'color: black',
            }))

class newtemplateform(forms.Form):
    def __init__(self, permissions, *args, **kwargs):
        super(newtemplateform, self).__init__(*args, **kwargs)
        for field in Permissiontemplate._meta.fields[6:]: #list of regular permissions
            self.fields[field.name] = forms.BooleanField(required=False)
        rank_choices = (
            (1, 1), 
            (2, 2), 
            (3, 3), 
            (4, 4), #rank 5 is regular member
            ) #rank is to establish hierarchy, also lower ranks can't delete higher ranks
        #to add more rank choices, just extend the tuple
        if permissions.template.rank == 0:
            self.fields['rank'] = forms.ChoiceField(choices=rank_choices)
        else:
            self.fields['rank'] = forms.ChoiceField(choices=rank_choices[permissions.template.rank-1:len(rank_choices)])
        if permissions.template.founder:
            type_choices = (
            ('officer', 'Officer'),
            ('founder', 'Founder'),
            )
            self.fields['permset'] = forms.ChoiceField(choices=type_choices, widget=forms.Select(attrs={
                'class': 'form-control', 'style': 'color: black',
                }))
    title = forms.CharField(max_length=30, label='', widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Title', 'style': 'color: black',}))


class changeform(forms.Form):
    def __init__(self, nation, *args, **kwargs):
        super(changeform, self).__init__(*args, **kwargs)
        templatequery = nation.alliance.templates.all().exclude(rank=5).exclude(rank=0)
        if nation.permissions.template.founder:
            query = nation.alliance.members.all().exclude(pk=nation.pk).exclude(permissions__template__rank=5).exclude(permissions__template__rank=0)
        else:
            query = nation.alliance.members.all().exclude(
                permissions__template__rank__gte=nation.permissions.template.rank).exclude(permissions__template__rank=5)
            templatequery = templatequery.filter(rank__lte=nation.permissions.template.rank)
        self.fields['officer'] = forms.ModelChoiceField(queryset=query, widget=forms.Select(attrs={
            'class': 'form-control', 'style': 'color: black',
            }))
        self.fields['template'] = forms.ModelChoiceField(queryset=templatequery, widget=forms.Select(attrs={
            'class': 'form-control', 'style': 'color: black',
            }))

#promote members to stuff
class promoteform(forms.Form):
    def __init__(self, nation, *args, **kwargs):
        super(promoteform, self).__init__(*args, **kwargs)
        query = nation.alliance.members.all().filter(permissions__template__rank=5).exclude(pk=nation.pk)
        templatequery = nation.alliance.templates.all().exclude(rank=5).exclude(rank=0)
        if not nation.permissions.template.founder:
            templatequery = templatequery.filter(rank__lte=nation.permissions.template.rank)
        self.fields['member'] = forms.ModelChoiceField(queryset=query, widget=forms.Select(attrs={
            'class': 'form-control', 'style': 'color: black',
            }))
        self.fields['template'] = forms.ModelChoiceField(queryset=templatequery, widget=forms.Select(attrs={
            'class': 'form-control', 'style': 'color: black',
            }))

class demoteform(forms.Form):
    def __init__(self, nation, *args, **kwargs):
        super(demoteform, self).__init__(*args, **kwargs)
        query = nation.alliance.members.all().exclude(permissions__template__rank=5).exclude(pk=nation.pk)
        if not nation.permissions.template.founder:
            query = query.filter(permissions__template__rank__gte=nation.permissions.template.rank)
        self.fields['officer'] = forms.ModelChoiceField(queryset=query, widget=forms.Select(attrs={
            'class': 'form-control', 'style': 'color: black' 
            }))

class membertitleform(forms.Form):
    title = forms.CharField(max_length=30, min_length=2, widget=forms.TextInput(attrs={
            'class': 'form-control', 'style': 'color: black' 
            }))

class applicantsetform(forms.Form):
    choices = (
        ('on', 'Allow nations to apply for membership'),
        ('off', 'Do not allow nations to apply for membership'),
        )
    choice = forms.ChoiceField(choices=choices, widget=forms.RadioSelect())


class applicantcommform(forms.Form):
    choices = (
        ('on', 'Notify relevant officers when a nation applies for membership'),
        ('off', 'Do not notify relevant officers when a nation applies for membership'),
        )
    choice = forms.ChoiceField(choices=choices, widget=forms.RadioSelect())

class taxrateform(forms.Form):
    wealthy_tax = forms.IntegerField(min_value=0, max_value=100, label="Wealthy nations tax rate",
     widget=forms.NumberInput(attrs={'class': 'form-control', 'style': 'color: black'}))
    
    uppermiddle_tax = forms.IntegerField(min_value=0, max_value=100, label="Upper middle nations tax rate",
     widget=forms.NumberInput(attrs={'class': 'form-control', 'style': 'color: black'}))
    
    lowermiddle_tax = forms.IntegerField(min_value=0, max_value=100, label="Lower middle nations tax rate",
     widget=forms.NumberInput(attrs={'class': 'form-control', 'style': 'color: black'}))
    
    poor_tax = forms.IntegerField(min_value=0, max_value=100, label="Poor nations tax rate",
     widget=forms.NumberInput(attrs={'class': 'form-control', 'style': 'color: black'}))


class templatesform(forms.Form):
    def __init__(self, nation, *args, **kwargs):
        super(templatesform, self).__init__(*args, **kwargs)
        templates = nation.alliance.templates.all().exclude(rank=5).exclude(rank=0)
        if not nation.permissions.template.founder:
            templates = templates.filter(rank__gte=nation.permissions.template.rank)
        self.fields['template'] = forms.ModelChoiceField(queryset=templates, widget=forms.Select(
            attrs={'class': 'form-control', 'style': 'color: black'}))

