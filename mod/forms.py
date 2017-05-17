from django import forms


class globalcommform(forms.Form):
    content = forms.CharField(min_length=1, max_length=1000, widget=forms.Textarea(attrs={
        'class': 'form-control', 'style': 'color: black; height: 200px;', 'placeholder': 'Enter global comm',
        }))

class reasonform(forms.Form):
    reason = forms.CharField(min_length=1, max_length=500, widget=forms.Textarea(attrs={
        'class': 'form-control', 'style': 'color: black; height: 150px;', 'placeholder': 'Enter reason for action',
        }))

class quickactionform(forms.Form):
    player = forms.CharField(max_length=50, widget=forms.TextInput(attrs={
        'class': 'form-control', 'style': 'color: black;', 'placeholder': 'Nation ID/name/username'
        }))
    actions = (
            ('ban', 'Ban player'),
            ('delete', 'Delete nation'),
            ('enter_vacation', 'Put in vacation'),
            ('exit_vacation', 'Remove from vacation'),
            ('give_donor', 'Give donor'),
            ('revoke_donor', 'Revoke donor'),
            ('report_ban', 'Ban from reporting'),
            ('report_unban', 'Unban from reporting'),
        )
    action = forms.ChoiceField(choices=actions, widget=forms.Select(attrs={
        'class': 'form-control', 'style': 'color: black',
        }))
    reason = forms.CharField(max_length=500, min_length=5, widget=forms.Textarea(attrs={
        'class': 'form-control', 'style': 'color: black; height: 100px;', 'placeholder': 'Reason for action',
        }))


class viewplayerform(forms.Form):
    player = forms.CharField(max_length=50, widget=forms.TextInput(attrs={
        'class': 'form-control', 'style': 'color: black;', 'placeholder': 'Nation ID/name/username'
        }))


class newidform(forms.Form):
    old = forms.CharField(max_length=50, widget=forms.TextInput(attrs={
        'class': 'form-control', 'style': 'color: black;', 'placeholder': 'Enter current ID/nation name/user name'
        }))
    new = forms.IntegerField(min_value=-2147483648, max_value=2147483647, widget=forms.TextInput(attrs={
        'class': 'form-control', 'style': 'color: black;', 'placeholder': 'New ID'
        }))


class closereportform(forms.Form):
    conclusion = forms.CharField(max_length=500, min_length=5, widget=forms.Textarea(attrs={
        'class': 'form-control', 'style': 'color: black; height: 100px;', 'placeholder': 'Report conclusion',
        }))
    guilty = forms.BooleanField(required=False)


class delbanreportform(forms.Form):
    ban = forms.BooleanField(required=False)
    delete = forms.BooleanField(required=False)

    def clean(self):
        cleaned_data = super(delbanreportform, self).clean()

        if not cleaned_data.get('ban') and not cleaned_data.get('delete'):
            self.add_error('ban', 'You need to select at least one')
        return cleaned_data