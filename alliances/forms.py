from nation.models import *
from django import forms
import nation.variables as v

class membertitleform(forms.Form):
    title = forms.CharField(max_length=30, min_length=2, widget=forms.TextInput(attrs={
            'class': 'form-control', 'style': 'color: black' 
            }))

class generals_form(forms.Form):
    anthem = forms.CharField(max_length=15, widget=forms.TextInput(attrs={
        'placeholder': 'New anthem', 'class': 'form-control', 'style': 'color: black',}))
    flag = forms.CharField(max_length=100, widget=forms.TextInput(attrs={
        'placeholder': 'New flag URL', 'class': 'form-control', 'style': 'color: black',}))
    description = forms.CharField(max_length=1000, required=False, widget=forms.Textarea(attrs={
        'placeholder': 'Enter new description', 'class': 'form-control', 'style': 'height: 150px; color: black;'}))


class declarationform(forms.Form):
    message = forms.CharField(min_length=5, max_length=400, widget=forms.Textarea(attrs={
        'placeholder': 'Enter your message.', 'class': 'form-control', 'style': 'height: 150px; color: black;'}))


class masscommform(forms.Form):
    message = forms.CharField(min_length=5, max_length=500, widget=forms.Textarea(attrs={
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
    name = forms.CharField(max_length=200, widget=forms.TextInput(attrs={
        'placeholder': 'Invite players by name, ID or username', 'class': 'form-control', 'style': 'color: black;'}))

class heirform(forms.Form):
    def __init__(self, nation, *args, **kwargs):
        super(heirform, self).__init__(*args, **kwargs)
        query = nation.alliance.members.all().filter(permissions__template__rank__lt=5).exclude(pk=nation.pk)
        self.fields['heir'] = forms.ModelChoiceField(queryset=query, required=False, widget=forms.Select(attrs={
            'class': 'form-control', 'style': 'color: black;'}))

# Withdrawing and depositing limits are form enforced
# withdrawing limits are whatever is lower between nation withdrawal limit or bank stockpile


#base form for rendering
#using either a deposit or withdraw form could lead to problems with max values
#this has more redundant code but easier verification
class numberform(forms.Form):
    def __init__(self, *args, **kwargs):
        super(numberform, self).__init__(*args, **kwargs)
        self.fields['amount'] = forms.IntegerField(
            min_value=1,
            widget=forms.NumberInput(attrs={
                    'class': 'form-control', 
                    'placeholder': 'Amount', 
                    'style': 'color: black;'
                }))



class depositform(forms.Form):
    def __init__(self, nation, *args, **kwargs):
        super(depositform, self).__init__(*args, **kwargs)
        self.fields['amount'] = forms.IntegerField(
            min_value=1,
            max_value=nation.budget,
            widget=forms.NumberInput(attrs={
                    'class': 'form-control', 
                    'placeholder': 'Deposit amount', 
                    'style': 'color: black;'
                }))


class withdrawform(forms.Form):
    def __init__(self, nation, *args, **kwargs):
        super(withdrawform, self).__init__(*args, **kwargs)
        stockpile = nation.budget
        bankstock = nation.alliance.bank.budget
        if nation.alliance.bank.limit and not nation.permissions.template.rank == 0:
            limit = nation.alliance.bank.budget_limit - nation.memberstats.budget
            maxwithdraw = (limit if limit < bankstock else bankstock)
        else:
            maxwithdraw = bankstock
        self.fields['amount'] = forms.IntegerField(
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


#selecting permission templates for promote/alter/deletion
class permissionselectform(forms.Form):
    def __init__(self, nation, *args, **kwargs):
        super(permissionselectform, self).__init__(*args, **kwargs)
        if nation.permissions.template.rank == 0:
            perms = nation.alliance.templates.all().exclude(rank=5)
        else:
            perms = nation.alliance.templates.all().filter(rank__lte=nation.permissions.rank).exclude(member_template=True)
        self.fields['template'] = forms.ModelChoiceField(queryset=perms, widget=forms.Select(attrs={
            'class': 'form-control', 'style': 'color: black',
            }))

class newtemplateform(forms.Form):
    def __init__(self, permissions, *args, **kwargs):
        super(newtemplateform, self).__init__(*args, **kwargs)
        for field in Basetemplate._meta.fields: #list of regular permissions
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
        
        if permissions.template.rank == 0:
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
        if nation.permissions.template.rank == 0:
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
        if not nation.permissions.template.rank == 0:
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
        if not nation.permissions.template.rank == 0:
            query = query.filter(permissions__template__rank__gte=nation.permissions.template.rank)
        self.fields['officer'] = forms.ModelChoiceField(queryset=query, widget=forms.Select(attrs={
            'class': 'form-control', 'style': 'color: black' 
            }))


class templatesform(forms.Form):
    def __init__(self, nation, *args, **kwargs):
        super(templatesform, self).__init__(*args, **kwargs)
        templates = nation.alliance.templates.all().exclude(rank=5).exclude(rank=0)
        if not nation.permissions.template.rank == 0:
            templates = templates.filter(rank__gte=nation.permissions.template.rank)
        self.fields['template'] = forms.ModelChoiceField(queryset=templates, widget=forms.Select(
            attrs={'class': 'form-control', 'style': 'color: black'}))


######
## banking forms
######

class taxrateform(forms.Form):
    wealthy_tax = forms.IntegerField(label="Wealthy nations tax rate",
     widget=forms.NumberInput(attrs={'class': 'form-control', 'style': 'color: black'}))
    
    uppermiddle_tax = forms.IntegerField(label="Upper middle nations tax rate",
     widget=forms.NumberInput(attrs={'class': 'form-control', 'style': 'color: black'}))
    
    lowermiddle_tax = forms.IntegerField(label="Lower middle nations tax rate",
     widget=forms.NumberInput(attrs={'class': 'form-control', 'style': 'color: black'}))
    
    poor_tax = forms.IntegerField(label="Poor nations tax rate",
     widget=forms.NumberInput(attrs={'class': 'form-control', 'style': 'color: black'}))

    def clean(self):
        cleaned_data = super(taxrateform, self).clean()
        for field in cleaned_data:
            if field == "budget_limit":
                continue
            if cleaned_data[field] < 0:
                cleaned_data[field] = 0
            elif cleaned_data[field] > 100:
                cleaned_data[field] = 100
        return cleaned_data

class bankingform(taxrateform):
    #inherit from taxrate form to make form validation at the view level easier
    budget_limit = forms.IntegerField(min_value=0, widget=forms.NumberInput(attrs={
        'class': 'form-control', 'style': 'color: black',
        }))


