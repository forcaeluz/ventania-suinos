from django import forms
from django.core.validators import ValidationError
from .models import AnimalExits, Flock


class FlockForm(forms.Form):
    entry_date = forms.DateField()
    entry_weight = forms.DecimalField()
    number_of_animals = forms.IntegerField()


class AnimalExitsForm(forms.ModelForm):

    def clean_number_of_animals(self):
        n_of_animals = self.cleaned_data.get('number_of_animals')
        flock = self.fields['flock'].queryset[0]
        if n_of_animals > flock.number_of_living_animals:
            raise ValidationError(("Number of exiting animals is bigger than available."), code='Too much animals')

        return n_of_animals

    class Meta:
        model = AnimalExits
        fields = ['date', 'number_of_animals', 'total_weight', 'flock']

