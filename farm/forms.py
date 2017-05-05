from datetime import datetime

from django.forms import forms, DateField, IntegerField, FloatField, ModelChoiceField
from django.forms import BaseFormSet, BaseForm, Form, ValidationError

from buildings.models import Room, AnimalRoomExit
from flocks.models import Flock, AnimalExits


class EasyFatForm(forms.Form):
    pass


class AnimalEntryForm(Form):
    date = DateField()
    weight = FloatField(min_value=0.0)
    number_of_animals = IntegerField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
            })
        self.fields['date'].widget.attrs.update(
            {'data-provide': 'datepicker-inline', 'class': 'form-control datepicker'})
        self.fields['date'].initial = datetime.today().date()


class AnimalEntryRoomForm(Form):
    room = ModelChoiceField(queryset=Room.objects.all())
    number_of_animals = IntegerField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.warnings = []
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
            })

        if not self.is_bound:
            if self.initial['number_of_animals'] > self.initial['room'].capacity:
                self.warnings.append('Number of animals higher than room capacity.')


class AnimalEntryRoomFormset(BaseFormSet):
    def __init__(self, *args, **kwargs):
        self.__n_of_animals = int(kwargs.pop('number_of_animals', 0))
        super().__init__(*args, **kwargs)

    def clean(self):
        if any(self.errors):
            return
        count = 0
        for form in self.forms:
            nof_animals = form.cleaned_data['number_of_animals']
            count += nof_animals

        if count != self.__n_of_animals:
            raise ValidationError('Number of animals out in form is different than in the exit.')


class AnimalExitForm(Form):
    date = DateField()
    weight = FloatField(min_value=0.0)
    number_of_animals = IntegerField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.warnings = []
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
            })
        self.fields['date'].widget.attrs.update(
            {'data-provide': 'datepicker-inline', 'class': 'form-control datepicker'})
        self.fields['date'].initial = datetime.today().date()


class AnimalExitRoomForm(Form):
    room = ModelChoiceField(queryset=Room.objects.all())
    number_of_animals = IntegerField(min_value=0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.warnings = []
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
            })

    def clean(self):
        no_of_animals = self.cleaned_data['number_of_animals']
        room = self.cleaned_data['room']
        if no_of_animals > room.occupancy:
            raise ValidationError('Number of animals for room %s '
                                  'must be less than the occupancy of %d.' % (room.__str__(), room.occupancy))


class AnimalExitRoomFormset(BaseFormSet):

    def __init__(self, *args, **kwargs):
        self.__n_of_animals = int(kwargs.pop('number_of_animals', 0))
        super().__init__(*args, **kwargs)

    def clean(self):
        if any(self.errors):
            return
        count = 0
        for form in self.forms:
            nof_animals = form.cleaned_data['number_of_animals']
            count += nof_animals

        if count != self.__n_of_animals:
            raise ValidationError('Number of animals out in form is different than in the exit.')

    def get_exited_rooms(self):
        """
            This function returns only rooms where animals actually went out.
        :return: List of AnimalRoomExitForms from which animals left.
        """
        exited_rooms = []
        for form in self.forms:
            nof_animals = form.cleaned_data['number_of_animals']
            if nof_animals != 0:
                exited_rooms.append(form)

        return exited_rooms

