from django import forms
from django.forms.fields import HiddenInput
from django.core.validators import ValidationError
from ui_objects.widgets import DatePickerWidget
from .models import Flock, AnimalDeath, AnimalSeparation

from datetime import datetime


class FlockForm(forms.Form):
    entry_date = forms.DateField(widget=DatePickerWidget())
    entry_weight = forms.DecimalField()
    number_of_animals = forms.IntegerField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
            })

        self.fields['entry_date'].widget.attrs.update({'data-provide': 'datepicker-inline', 'data-date-format': "yyyy-mm-dd"})
        self.fields['entry_date'].initial = datetime.today().date()

    def clean_entry_weight(self):
        weight = self.cleaned_data.get('entry_weight')
        if weight <= 0:
            raise ValidationError('Entry weight should be bigger than 0')

        return weight


# class AnimalExitsForm(forms.ModelForm):
#
#     def __init__(self, *args, **kwargs):
#         super(AnimalExitsForm, self).__init__(*args, **kwargs)
#         current_flocks = [obj.id for obj in Flock.objects.all() if obj.number_of_living_animals > 0]
#         self.fields['flock'].queryset = Flock.objects.filter(pk__in=current_flocks)
#         for field in iter(self.fields):
#             self.fields[field].widget.attrs.update({
#                 'class': 'form-control',
#             })
#         self.fields['date'].widget.attrs.update({'data-provide': 'datepicker-inline', 'data-date-format': "yyyy-mm-dd"})
#         self.fields['date'].initial = datetime.today().date()
#
#     def clean_number_of_animals(self):
#         n_of_animals = self.cleaned_data.get('number_of_animals')
#         flock = self.fields['flock'].queryset[0]
#         if n_of_animals > flock.number_of_living_animals:
#             raise ValidationError("Number of exiting animals is bigger than available.", code='Too much animals')
#
#         return n_of_animals
#
#     class Meta:
#         model = AnimalExits
#         fields = ['date', 'number_of_animals', 'total_weight', 'flock']
#         widgets = {'date': DatePickerWidget()}


class AnimalDeathForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(AnimalDeathForm, self).__init__(*args, **kwargs)
        current_flocks = [obj.id for obj in Flock.objects.all() if obj.number_of_living_animals > 0]
        self.fields['flock'].queryset = Flock.objects.filter(pk__in=current_flocks)

        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
            })

        self.fields['date'].widget.attrs.update({'data-provide': 'datepicker-inline', 'data-date-format': "yyyy-mm-dd"})
        self.fields['date'].initial = datetime.today().date()

    class Meta:
        model = AnimalDeath
        fields = ['date', 'weight', 'cause', 'flock']


class AnimalSeparationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(AnimalSeparationForm, self).__init__(*args, **kwargs)
        current_flocks = [obj.id for obj in Flock.objects.all() if obj.number_of_living_animals > 0]
        self.fields['flock'].queryset = Flock.objects.filter(pk__in=current_flocks)
        if 'initial' in kwargs.keys():
            initial_variables = kwargs['initial']
            if initial_variables['flock'] is not None:
                self.fields['flock'].initial = initial_variables['flock']

        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
            })
            self.fields['date'].widget.attrs.update(
                {'data-provide': 'datepicker-inline', 'data-date-format': "yyyy-mm-dd"})
            self.fields['date'].initial = datetime.today().date()

    class Meta:
        model = AnimalSeparation
        fields = ['date', 'reason', 'flock']


class SeparationDeathForm(AnimalDeathForm):
    separation_id = forms.IntegerField(widget=HiddenInput)

    def __init__(self, *args, **kwargs):
        sep_id = kwargs.pop('separation_id', None)
        super(SeparationDeathForm, self).__init__(*args, **kwargs)
        if sep_id is not None:
            self.fields['separation_id'].initial = int(sep_id)
            separation = AnimalSeparation.objects.get(id=sep_id)
            self.fields['flock'].initial = Flock.objects.get(id=separation.flock_id)
            self.fields['flock'].widget = HiddenInput()

    def clean(self):
        sep_id = self.cleaned_data.get('separation_id')
        separation = AnimalSeparation.objects.get(id=sep_id)
        death_date = self.cleaned_data.get('date')
        if separation.date > death_date:
            raise ValidationError('Death happened before separation.', code='Death date before separation')

    def save(self, commit=True):
        death = super(AnimalDeathForm, self).save(commit)
        separation = AnimalSeparation.objects.get(id=self.cleaned_data.get('separation_id'))
        separation.death = death
        separation.save()


# class SeparationExitForm(AnimalExitsForm):
#     separation_id = forms.IntegerField(widget=HiddenInput)
#
#     def __init__(self, *args, **kwargs):
#         sep_id = kwargs.pop('separation_id', None)
#         super().__init__(*args, **kwargs)
#         if sep_id is not None:
#             self.fields['separation_id'].initial = int(sep_id)
#             separation = AnimalSeparation.objects.get(id=sep_id)
#             self.fields['flock'].initial = Flock.objects.get(id=separation.flock_id)
#             self.fields['flock'].widget = HiddenInput()
#             self.fields['number_of_animals'].initial = 1
#             self.fields['number_of_animals'].widget = HiddenInput()
#
#     def clean(self):
#         sep_id = self.cleaned_data.get('separation_id')
#         separation = AnimalSeparation.objects.get(id=sep_id)
#         exit_date = self.cleaned_data.get('date')
#         if separation.date > exit_date:
#             raise ValidationError('Exit happened before separation.', code='Death date before separation')
#
#     def save(self, commit=True):
#         animal_exit = super(AnimalExitsForm, self).save(commit)
#         separation = AnimalSeparation.objects.get(id=self.cleaned_data.get('separation_id'))
#         separation.exit = animal_exit
#         separation.save()
