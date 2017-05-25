from datetime import datetime

# Fields
from django.forms import DateField, IntegerField, FloatField, ModelChoiceField, CharField, ModelMultipleChoiceField
# Others
from django.forms import forms, BaseFormSet, Form, ValidationError, CheckboxSelectMultiple

from buildings.models import Room, AnimalRoomEntry, AnimalRoomExit, DeathInRoom, AnimalSeparatedFromRoom, RoomGroup
from flocks.models import Flock, AnimalExits, AnimalDeath, AnimalSeparation


class EasyFatForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
            })


class AnimalEntryForm(EasyFatForm):
    date = DateField()
    weight = FloatField(min_value=0.0)
    number_of_animals = IntegerField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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


class GroupExitForm(Form):
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


class SingleAnimalExitForm(EasyFatForm):
    date = DateField()
    room = ModelChoiceField(queryset=Room.objects.all())
    weight = FloatField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.animal_exit = None
        self.flock = None
        non_empty_rooms = [room.id for room in Room.objects.all() if room.occupancy > 0]
        self.fields['date'].widget.attrs.update(
            {'data-provide': 'datepicker-inline', 'class': 'form-control datepicker'})
        self.fields['date'].initial = datetime.today().date()
        self.fields['room'].queryset = Room.objects.filter(pk__in=non_empty_rooms)

    def set_flock(self, flock):
        self.flock = flock

    def clean(self):
        data = self.cleaned_data
        date = data['date']
        room = data['room']  # Room
        if not self.flock:
            if len(room.get_flocks_present_at(date)) == 1:
                self.flock = next(iter(room.get_flocks_present_at(date)))
            elif len(room.get_flocks_present_at(date)) > 1:
                raise ValidationError('No flock distinction possible')
            else:
                raise ValidationError('Room was empty at death date')

        if room.get_animals_for_flock(self.flock, date) <= 0:
            raise ValidationError('No animals from flock in room at death date')

    def save(self):
        data = self.cleaned_data
        date = data['date']
        room = data['room']
        if not self.flock:
            if len(room.get_flocks_present_at(date)) == 1:
                self.flock = next(iter(room.get_flocks_present_at(date)))
            else:
                raise ValidationError('No flock distinction possible')

        flock = self.flock
        animal_exit = AnimalExits(date=date,
                                  flock=flock,
                                  number_of_animals=1,
                                  total_weight=data['weight'])
        animal_exit.save()

        room_exit = AnimalRoomExit(date=date,
                                   room=room,
                                   flock=flock,
                                   number_of_animals=1)
        room_exit.save()
        self.animal_exit = animal_exit


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


class AnimalDeathForm(EasyFatForm):
    date = DateField()
    room = ModelChoiceField(queryset=Room.objects.all())
    weight = FloatField()
    reason = CharField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.death = None
        self.flock = None
        non_empty_rooms = [room.id for room in Room.objects.all() if room.occupancy > 0]
        self.fields['date'].widget.attrs.update(
            {'data-provide': 'datepicker-inline', 'class': 'form-control datepicker'})
        self.fields['date'].initial = datetime.today().date()
        self.fields['room'].queryset = Room.objects.filter(pk__in=non_empty_rooms)

    def set_flock(self, flock):
        self.flock = flock

    def clean(self):
        data = self.cleaned_data
        date = data['date']
        room = data['room'] # Room
        if not self.flock:
            if len(room.get_flocks_present_at(date)) == 1:
                self.flock = next(iter(room.get_flocks_present_at(date)))
            elif len(room.get_flocks_present_at(date)) > 1:
                raise ValidationError('No flock distinction possible')
            else:
                raise ValidationError('Room was empty at death date')

        if room.get_animals_for_flock(self.flock, date) <= 0:
            raise ValidationError('No animals from flock in room at death date')

    def save(self):
        data = self.cleaned_data
        date = data['date']
        room = data['room']
        if not self.flock:
            if len(room.get_flocks_present_at(date)) == 1:
                self.flock = next(iter(room.get_flocks_present_at(date)))
            else:
                raise ValidationError('No flock distinction possible')

        flock = self.flock
        death = AnimalDeath(date=date,
                            flock=flock,
                            weight=data['weight'],
                            cause=data['reason'])
        death.save()
        death_in_room = DeathInRoom(death=death,
                                    room=room)
        death_in_room.save()
        room_exit = AnimalRoomExit(date=date,
                                   room=room,
                                   flock=flock,
                                   number_of_animals=1)
        room_exit.save()
        self.death = death


class AnimalDeathDistinctionForm(EasyFatForm):
    separation = ModelChoiceField(queryset=AnimalSeparation.objects.all())

    def __init__(self, *args, **kwargs):
        self.room = kwargs.pop('room', None)
        self.death = None
        self.exit = None

        super().__init__(*args, **kwargs)
        if not self.is_bound:
            separations = AnimalSeparation.objects.filter(animalseparatedfromroom__destination=self.room)
            separations = [sep.id for sep in separations if sep.active]
            self.fields['separation'].queryset = AnimalSeparation.objects.filter(pk__in=separations)

    def set_death(self, death):
        assert(isinstance(death, AnimalDeath))
        self.death = death

    def save(self):
        separation = self.cleaned_data.get('separation')
        separation.death = self.death
        separation.save()


class AnimalSeparationForm(EasyFatForm):
    date = DateField()
    src_room = ModelChoiceField(Room.objects.filter(is_separation=False))
    dst_room = ModelChoiceField(Room.objects.filter(is_separation=True))
    reason = CharField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        non_empty_rooms = [room.id for room in Room.objects.all() if room.occupancy > 0]
        self.fields['date'].widget.attrs.update(
            {'data-provide': 'datepicker-inline', 'class': 'form-control datepicker'})
        self.fields['date'].initial = datetime.today().date()
        if not self.is_bound:
            self.fields['src_room'].queryset = Room.objects.filter(pk__in=non_empty_rooms)

    def clean(self):
        data = self.cleaned_data
        room = data.get('src_room')
        if len(room.get_flocks_present_at(data['date'])) != 1:
            raise ValidationError('Unable to handle rooms with multiple flocks.')

    def save(self):
        data = self.cleaned_data
        date = data['date']
        src_room = data['src_room']
        dst_room = data['dst_room']

        if len(src_room.get_flocks_present_at(date)) == 1:
            flock = next(iter(src_room.get_flocks_present_at(date)))
            separation = AnimalSeparation(flock=flock,
                                          date=date,
                                          reason=data['reason'])
            separation.save()
            separation_form_room = AnimalSeparatedFromRoom(separation=separation,
                                                           room=src_room,
                                                           destination=dst_room)

            separation_form_room.save()
            room_exit = AnimalRoomExit(date=date,
                                       room=src_room,
                                       flock=flock,
                                       number_of_animals=1)
            room_exit.save()
            room_entry = AnimalRoomEntry(date=date,
                                         room=dst_room,
                                         flock=flock,
                                         number_of_animals=1)
            room_entry.save()