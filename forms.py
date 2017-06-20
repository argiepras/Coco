from .models import *
from django import forms
from . import variables as v


class aidform(forms.Form):
    def __init__(self, nation, *args, **kwargs):
        super(aidform, self).__init__(*args, **kwargs)
        for resource in v.resources:
            if nation.__dict__[resource] > 0:
                self.fields[resource] = forms.IntegerField(min_value=1, max_value=nation.__dict__[resource], required=False, 
                    widget=forms.NumberInput(attrs={'size': '4', 'placeholder': '0'}))


class ajaxaidform(forms.Form):
    def __init__(self, nation, *args, **kwargs):
        super(ajaxaidform, self).__init__(*args, **kwargs)
        self.nation = nation #so the clean method can use it
        x = []
        for resource in v.resources:
            x.append((resource, resource))
        self.fields['resource'] = forms.ChoiceField(choices=x)
    amount = forms.IntegerField(min_value=0)

    def clean(self):
        cleaned_data = super(ajaxaidform, self).clean()
        if not cleaned_data:
            return  cleaned_data
        if cleaned_data.get("amount") > getattr(self.nation, cleaned_data.get("resource")):
            self.add_error('amount', 'You cannot send off more than you have!')
        return cleaned_data


class searchform(forms.Form):
    nation = forms.CharField(max_length=50, min_length=1, widget=forms.TextInput(attrs={
        'placeholder': 'Search for nation...', 'class': 'form-control'
        }))

class commform(forms.Form):
    message = forms.CharField(max_length=1000, widget=forms.Textarea(attrs={'placeholder': 'Enter your message...', 'class': 'id_message'}))


class declarationform(forms.Form):
    message = forms.CharField(max_length=500, min_length=1, widget=forms.Textarea(
        attrs={
        'style': 'height: 150px', 
        'placeholder': 'Enter your declaration', 
        'class': 'form-control',
    }))

class filterform(forms.Form):
    def __init__(self, *args, **kwargs):
        super(filterform, self). __init__(*args, **kwargs)
        choices = []
        for resource in v.depositchoices:
            choices.append((resource, v.depositchoices[resource]))
        choices.append(('army', 'Troops'))
        self.fields['offer'] = forms.ChoiceField(choices=choices, widget=forms.Select(
            attrs={
                'class': 'form-control',
            }))

class offerform(forms.Form):
    def __init__(self, *args, **kwargs):
        super(offerform, self).__init__(*args, **kwargs)
        choices = []
        for resource in v.depositchoices:
            choices.append((resource, v.depositchoices[resource]))
        choices.append(('army', 'Troops'))
        self.fields['offer'] = forms.ChoiceField(choices=choices, widget=forms.Select(
            attrs={
                'class': 'form-control',
            }))
        self.fields['request'] = forms.ChoiceField(choices=choices, widget=forms.Select(
                attrs={
                    'class': 'form-control',
                }))
    allow_tariff = forms.BooleanField(required=False)
    offer_amount = forms.IntegerField(min_value=1, widget=forms.NumberInput(
        attrs={
            'class': 'form-control',
            'placeholder': 'Offer amount',
        }))
    request_amount = forms.IntegerField(min_value=1, widget=forms.NumberInput(
        attrs={
            'class': 'form-control',
            'placeholder': 'Offer amount',
        }))

    def clean(self):
        cleaned_data = super(offerform, self).clean()

        if cleaned_data.get("offer") == cleaned_data.get("request"):
            self.add_error('offer', 'You cannot trade %(offer)s for %(offer)s!' % {'offer': cleaned_data.get("offer")})
        if cleaned_data.get("offer") == 'army':
            cleaned_data['offer_amount'] = 10
        elif cleaned_data.get("request") == 'army':
            cleaned_data['request_amount'] = 10
        return cleaned_data


class descriptionform(forms.Form):
    description = forms.CharField(max_length=500, min_length=1, widget=forms.Textarea(
        attrs={'style': 'height: 150px', 'placeholder': 'Enter new description', 'class': 'form-control'}))


class flagform(forms.Form):
    choices = (
        ('angola.png', 'Angola'),
        ('vi.png', 'Vi'),
        ('saudi.png', 'Saudi'),
        ('lf.png', 'Lf'),
        ('burundi.png', 'Burundi'),
        ('grenada.png', 'Grenada'),
        ('libya.png', 'Libya'),
        ('ethiopia.png', 'Ethiopia'),
        ('venezuela.png', 'Venezuela'),
        ('barbados.png', 'Barbados'),
        ('burya.png', 'Burya'),
        ('roc.png', 'Roc'),
        ('myanmar.png', 'Myanmar'),
        ('sicily.png', 'Sicily'),
        ('tropico.png', 'Tropico'),
        ('kenya.png', 'Kenya'),
        ('iraq.png', 'Iraq'),
        ('taliban.png', 'Taliban'),
        ('charlesb.png', 'Charlesb'),
        ('ghana.png', 'Ghana'),
        ('snip.png', 'Snip'),
        ('centralamerica.png', 'Central america'),
        ('jordan.png', 'Jordan'),
        ('zaire.png', 'Zaire'),
        ('arstotzka.png', 'Arstotzka'),
        ('ottoman.png', 'Ottoman'),
        ('albania.png', 'Albania'),
        ('tuva.png', 'Tuva'),
        ('tajik.png', 'Tajik'),
        ('goonflag.png', 'Goonflag'),
        ('newengland.png', 'Newengland'),
        ('israel.png', 'Israel'),
        ('prc.png', 'Prc'),
        ('mozambique.png', 'Mozambique'),
        ('whiskey.png', 'Whiskey'),
        ('haiti.png', 'Haiti'),
        ('finland.png', 'Finland'),
        ('ingsoc.png', 'Ingsoc'),
        ('korea.png', 'Korea'),
        ('nkorea.png', 'Nkorea'),
    )
    flag = forms.ChoiceField(choices=choices)

class portraitform(forms.Form):
    choices = (
        ('allende.gif', 'allende'),
        ('obama.gif', 'obama'),
        ('presidente.gif', 'presidente'),
        ('deng.gif', 'deng'),
        ('ayatollah.gif', 'ayatollah'),
        ('marcos.gif', 'marcos'),
        ('saddam.gif', 'saddam'),
        ('mao.jpg', 'mao'),
        ('saud.gif', 'saud'),
        ('salazar.gif', 'salazar'),
        ('bokassa.gif', 'bokassa'),
        ('Golda.gif', 'Golda'),
        ('ataturk.gif', 'ataturk'),
        ('chaing.gif', 'chaing'),
        ('charlesb.gif', 'charlesb'),
        ('evita.gif', 'evita'),
        ('shah.gif', 'shah'),
        ('fidel.gif', 'fidel'),
        ('papa.gif', 'papa'),
        ('indhira.gif', 'indhira'),
        ('stalin1.gif', 'stalin1'),
        ('kimil.gif', 'kimil'),
        ('benazir.gif', 'benazir'),
        ('jorji.gif', 'jorji'),
        ('noriega.gif', 'noriega'),
        ('rpaul.gif', 'rpaul'),
        ('peron.gif', 'peron'),
        ('moshe.gif', 'moshe'),
        ('kuanda.gif', 'kuanda'),
        ('batista.gif', 'batista'),
        ('idi.gif', 'idi amin'),
        ('qaddafi.gif', 'qaddafi'),
        ('bf.gif', 'bf'),
        ('lumumba.gif', 'lumumba'),
        ('ho.gif', 'ho'),
        ('tatcher.gif', 'tatcher'),
        ('chavez.gif', 'chavez'),
        ('stroessner.gif', 'stroessner'),
        ('mobutu.jpg', 'mobutu'),
        ('leila.gif', 'leila'),
        ('hoxha.gif', 'hoxha'),
        ('franco.gif', 'franco'),
        ('pinochet.gif', 'pinochet'),
        ('ortega.gif', 'ortega'),
        ('tito.gif', 'tito'),
        ('snip.gif', 'snip'),
    )
    portrait = forms.ChoiceField(choices=choices)


class anthemform(forms.Form):
    anthem = forms.CharField(max_length=20, min_length=1, widget=forms.TextInput(attrs={ 
       }))

#for both custom flag and custom avatar
class customavatarform(forms.Form):
    url = forms.CharField(max_length=200, min_length=5, widget=forms.TextInput(attrs={
        'placeholder': 'Enter url', 'class': 'form-control', 'style': 'color: black;',
        }))

class donorurlform(forms.Form):
    url = forms.SlugField(max_length=30, min_length=0, widget=forms.TextInput(attrs={
        'placeholder': 'Enter url', 'class': 'form-control', 'style': 'color: black;',
        }))

class passwordform(forms.Form):
    p1 = forms.CharField(max_length=30, min_length=4, widget=forms.PasswordInput(attrs={
        'placeholder': 'Enter Password', 'class': 'form-control', 'style': 'color: black;',
        }))
    p2 = forms.CharField(max_length=30, min_length=4, widget=forms.PasswordInput(attrs={
        'placeholder': 'Enter Password Again', 'class': 'form-control', 'style': 'color: black;',
        }))


class titleform(forms.Form):
    desc = forms.CharField(max_length=100, min_length=0, widget=forms.TextInput(attrs={
        'placeholder': 'Enter custom title', 'class': 'form-control', 'style': 'color: black;',
        }))

class descriptorform(forms.Form):
    desc = forms.CharField(max_length=100, min_length=0, widget=forms.TextInput(attrs={
        'placeholder': 'Enter custom title', 'class': 'form-control', 'style': 'color: black;',
        }))


class spyselectform(forms.Form):
    def __init__(self, nation, *args, **kwargs):
        super(spyselectform, self).__init__(*args, **kwargs)
        spies = nation.spies.all().filter(location=nation, actioned=False)
        self.fields['spy'] = forms.ModelChoiceField(queryset=spies, widget=forms.Select(attrs={'class': 'form-control', 'style': 'color: black;'}))



class newnationform(forms.Form):
    def __init__(self, *args, **kwargs):
        super(newnationform, self).__init__(*args, **kwargs)
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

        if ID.objects.get().freeIDs > 0:
            self.fields['id'] = forms.IntegerField(
                min_value=-2147483648, 
                max_value=2147483647,
                required=False,
                widget=forms.NumberInput(attrs={
                        'class': 'form-control',
                    }))

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


    name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={
        'placeholder': 'Nation name',
        'class': 'form-control',
        }))


    def clean_name(self):
        name = self.cleaned_data['name']
        if Nation.objects.filter(name__iexact=name).exists():
            raise forms.ValidationError('Nation name is taken!')
        return name

    def clean_id(self):
        index = self.cleaned_data['id']
        if Nation.objects.filter(index=index).exists():
            raise forms.ValidationError('ID is taken!')
        return index


class autoplayform(forms.Form):
    choices = (('off', 'no'), ('on', 'yes'))
    autoplay = forms.ChoiceField(choices=choices, widget=forms.RadioSelect())