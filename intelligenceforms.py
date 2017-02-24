import variables as v
from django import forms


class newspyform(forms.Form):
    def __init__(self, *args, **kwargs):
        super(newspyform, self).__init__(*args, **kwargs)
        choices = []
        for specialty in v.specialities:
            choices.append((specialty, specialty))
        choices = tuple(choices)
        self.fields['specialty'] = forms.ChoiceField(choices=choices, widget=forms.Select(attrs={
        'class': 'form-control', 'style': 'color: black'}))
    name = forms.CharField(max_length=10, required=False, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Spy name', 'width': 10, 'style': 'color: black'
        }))
    
class spyselectform(forms.Form):
    def __init__(self, spies, *args, **kwargs):
        super(spyselectform, self).__init__(*args, **kwargs)
        choices = []
        for spy in spies:
            choices.append((spy.pk, "%s - %s" % (spy.name, spy.specialty)))
        choices = tuple(choices)
        self.fields['spy'] = forms.ChoiceField(choices=choices)


class extraditeform(forms.Form):
    name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={
        'class': 'form-control', 'style': 'color: black;', 'placeholder': 'Nation ID/name/username'
        }))


class surveillanceform(forms.Form):
    def __init__(self, nation, *args, **kwargs):
        super(surveillanceform, self).__init__(*args, **kwargs)
        query = nation.spies.all().filter(location=nation, surveilling=None, actioned=False)
        self.fields['spy'] = forms.ModelChoiceField(queryset=query, widget=forms.Select(attrs={
        'class': 'form-control', 'style': 'color: black'}))