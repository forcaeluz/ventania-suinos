from datetime import datetime

# Fields
from django.forms import DateField, IntegerField, FloatField, ModelChoiceField, CharField, ModelMultipleChoiceField
from django.forms import BooleanField
# Others
from django.forms import forms, BaseFormSet, Form, ValidationError

from buildings.models import Room, AnimalRoomEntry, AnimalRoomExit, \
    DeathInRoom, AnimalSeparatedFromRoom, RoomFeedingChange, Silo, SiloFeedEntry

from flocks.models import AnimalDeath, AnimalSeparation, Flock, AnimalFarmExit, AnimalFlockExit
from feeding.models import FeedType, FeedEntry
from medications.models import Medication


from .widgets import RoomSelectionWidget


class EasyFatForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
            })

            if field == 'date':
                self.fields[field].widget.attrs.update({'data-provide': 'datepicker-inline',
                                                        'class': 'form-control datepicker',
                                                        'data-date-end-date': datetime.today().date().isoformat()
                                                        })
                self.fields[field].initial = datetime.today().date()


class DeleteForm(EasyFatForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].disabled = True
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
            })


class AnimalEntryForm(EasyFatForm):
    """ Form class used to get user information about a new flock of animals entering the farm."""

    date = DateField()
    weight = FloatField(min_value=0.1)
    number_of_animals = IntegerField(min_value=1)
    rooms = ModelMultipleChoiceField(queryset=Room.objects.filter(is_separation=False), widget=RoomSelectionWidget)

    def __init__(self, *args, **kwargs):
        """ Form constructor.

        :param args:
        :param kwargs: An value for 'flock' is required in the constructor.
        """
        self.flock = kwargs.pop('flock', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        """ The clean method raises a validation error when the user tries to assign the flock to non-empty rooms."""
        if self.flock is None:
            self.__clean_new_flock_form()
        else:
            self.__clean_edit_flock_form()

    def __clean_new_flock_form(self):
        super().clean()
        rooms = self.cleaned_data.get('rooms')
        date = self.cleaned_data.get('date')
        for room in rooms:
            if room.get_occupancy_at_date(at_date=date) > 0:
                raise ValidationError('You selected rooms which were not empty at the specified date.')

    def __clean_edit_flock_form(self):
        assert self.flock is not None
        super().clean()
        rooms = self.cleaned_data.get('rooms')
        date = self.cleaned_data.get('date')
        for room in rooms:
            room_has_animals_from_flock = room.get_animals_for_flock(flock_id=self.flock.id, at_date=date) > 0
            room_is_empty = room.get_occupancy_at_date(at_date=date) == 0
            if not room_has_animals_from_flock and not room_is_empty:
                raise ValidationError('You selected rooms which were not empty at the specified date.')


class AnimalEntryDeleteForm(EasyFatForm):
    def __init__(self, *args, **kwargs):
        self.flock = kwargs.pop('flock', None)  # Flock
        assert isinstance(self.flock, Flock)
        super().__init__(*args, **kwargs)

    def save(self):
        self.flock.delete()


class AnimalEntryRoomForm(Form):
    room = ModelChoiceField(queryset=Room.objects.all())
    number_of_animals = IntegerField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.warnings = []
        room = kwargs.get('initial').get('room', None)
        if room is not None:
            self.fields['room'].queryset = Room.objects.filter(id=room.id)
            self.fields['room'].widget.attrs['readonly'] = True

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
    number_of_animals = IntegerField(min_value=1)
    rooms = ModelMultipleChoiceField(queryset=Room.objects.filter(is_separation=False), widget=RoomSelectionWidget)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.warnings = []
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
            })
        self.fields['date'].widget.attrs.update(
            {'data-provide': 'datepicker-inline', 'class': 'form-control datepicker',
             'data-date-end-date': datetime.today().date().isoformat()})
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
        assert isinstance(flock, Flock)
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
        animal_exit = AnimalFarmExit(date=date)
        animal_exit.save()

        animal_flock_exit = AnimalFlockExit(number_of_animals=1,
                                            weight=data['weight'],
                                            flock=self.flock,
                                            farm_exit=animal_exit)

        animal_flock_exit.save()

        room_exit = AnimalRoomExit(date=date,
                                   room=room,
                                   flock=flock,
                                   number_of_animals=1,
                                   farm_exit=animal_exit)

        room_exit.save()

        self.animal_exit = animal_flock_exit


class AnimalExitDeleteForm(EasyFatForm):

    def __init__(self, *args, **kwargs):
        self.exit = kwargs.pop('exit', None)  # AnimalFarmExit
        self.instance = self.exit
        super().__init__(*args, **kwargs)
        assert isinstance(self.exit, AnimalFarmExit)

    def save(self):
        room_exits = self.exit.animalroomexit_set.all()
        for room_exit in room_exits:
            room_exit.delete()
        self.exit.delete()


class AnimalExitRoomForm(Form):
    room = ModelChoiceField(queryset=Room.objects.all())
    number_of_animals = IntegerField(min_value=0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        room = None
        initial = kwargs.get('initial', None)
        if initial is not None:
            room = kwargs.get('initial').get('room', None)
        if room is not None:
            self.fields['room'].queryset = Room.objects.filter(id=room.id)
            self.fields['room'].widget.attrs['readonly'] = True
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


class AnimalDeathBaseForm(EasyFatForm):
    date = DateField()
    room = ModelChoiceField(queryset=Room.objects.all())
    weight = FloatField()
    reason = CharField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.death = None
        self.flock = None

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
        raise NotImplementedError


class AnimalDeathUpdateForm(AnimalDeathBaseForm):
    def __init__(self, *args, **kwargs):
        death_id = kwargs.pop('death_id', 0)
        super().__init__(*args, **kwargs)
        self.death = AnimalDeath.objects.get(id=death_id)
        self.fields['date'].widget.attrs.update(
            {'data-provide': 'datepicker-inline', 'class': 'form-control datepicker'})
        self.fields['date'].initial = self.death.date
        self.fields['weight'].initial = self.death.weight
        self.fields['reason'].initial = self.death.cause
        self.fields['room'].initial = self.death.deathinroom_set.all()[0].room

    def save(self):
        data = self.cleaned_data
        date = data['date']
        room = data['room']
        old_date = self.death.date
        old_flock = self.death.flock

        if not self.flock:
            if len(room.get_flocks_present_at(date)) == 1:
                self.flock = next(iter(room.get_flocks_present_at(date)))
            else:
                raise ValidationError('No flock distinction possible')

        assert self.death is not None
        flock = self.flock
        self.death.date = date
        self.death.flock = flock
        self.death.weight = data['weight']
        self.death.cause = data['reason']

        self.death.save()

        death_in_room = DeathInRoom.objects.get(death=self.death)
        old_room = death_in_room.room
        death_in_room.room = room
        death_in_room.save()

        animal_room_exit = AnimalRoomExit.objects.get(room=old_room, flock=old_flock,
                                                      date=old_date, number_of_animals=1)
        animal_room_exit.date = date
        animal_room_exit.room = room
        animal_room_exit.flock = flock
        animal_room_exit.save()


class AnimalDeathForm(AnimalDeathBaseForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date'].widget.attrs.update(
            {'data-provide': 'datepicker-inline', 'class': 'form-control datepicker'})
        self.fields['date'].initial = datetime.today().date()

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


class AnimalSeparationDistinctionForm(EasyFatForm):
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
        assert isinstance(death, AnimalDeath)
        self.death = death

    def set_exit(self, animal_exit):
        assert isinstance(animal_exit, AnimalFlockExit)
        self.exit = animal_exit

    def save(self):
        separation = self.cleaned_data.get('separation')
        separation.death = self.death
        separation.exit = self.exit
        separation.save()


class AnimalSeparationBaseForm(EasyFatForm):
    date = DateField()
    src_room = ModelChoiceField(Room.objects.filter(is_separation=False), label='From room:')
    dst_room = ModelChoiceField(Room.objects.filter(is_separation=True), label='To room:')
    reason = CharField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date'].widget.attrs.update(
            {'data-provide': 'datepicker-inline', 'class': 'form-control datepicker'})

    def clean(self):
        data = self.cleaned_data
        room = data.get('src_room')
        if len(room.get_flocks_present_at(data['date'])) != 1:
            raise ValidationError('Unable to handle rooms with multiple flocks.')

    def save(self):
        raise NotImplementedError


class AnimalSeparationForm(AnimalSeparationBaseForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date'].initial = datetime.today().date()

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


class AnimalSeparationUpdateForm(AnimalSeparationBaseForm):

    def __init__(self, *args, **kwargs):
        separation_id = kwargs.pop('separation_id', 0)
        super().__init__(*args, **kwargs)
        self.separation = AnimalSeparation.objects.get(id=separation_id)
        self.sep_from_room = AnimalSeparatedFromRoom.objects.get(separation=self.separation)
        self.fields['date'].initial = self.separation.date
        self.fields['reason'].initial = self.separation.reason
        self.fields['src_room'].initial = self.sep_from_room.room
        self.fields['dst_room'].initial = self.sep_from_room.destination

    def save(self):
        data = self.cleaned_data
        date = data['date']
        src_room = data['src_room']
        dst_room = data['dst_room']

        old_flock = self.separation.flock
        old_room = self.sep_from_room.room
        old_date = self.separation.date
        old_destination = self.sep_from_room.destination

        if len(src_room.get_flocks_present_at(date)) == 1:
            flock = next(iter(src_room.get_flocks_present_at(date)))

            self.separation.flock = flock
            self.separation.date = date
            self.separation.reason = data['reason']

            self.separation.save()

            self.sep_from_room.separation = self.separation
            self.sep_from_room.room = src_room
            self.sep_from_room.destination = dst_room
            self.sep_from_room.save()

            room_exit = AnimalRoomExit.objects.get(date=old_date, flock=old_flock, room=old_room, number_of_animals=1)
            room_exit.date = date
            room_exit.flock = flock
            room_exit.room = src_room
            room_exit.save()

            room_entry = AnimalRoomEntry.objects.get(date=old_date, flock=old_flock,
                                                     room=old_destination, number_of_animals=1)
            room_entry.date = date
            room_entry.flock = flock
            room_entry.room = dst_room
            room_entry.save()


class AnimalDeathDeleteForm(EasyFatForm):
    def __init__(self, *args, **kwargs):
        self.death = kwargs.pop('death', None)  # AnimalDeath
        self.instance = self.death
        super().__init__(*args, **kwargs)

    def save(self):
        date = self.death.date
        flock = self.death.flock
        room_exit = AnimalRoomExit.objects.get(date=date, flock=flock, number_of_animals=1)
        self.death.delete()
        room_exit.delete()


class AnimalSeparationDeleteForm(DeleteForm):

    def __init__(self, *args, **kwargs):
        self.separation = kwargs.pop('separation', None)  # AnimalSeparation
        self.instance = self.separation
        self.sep_from_room = AnimalSeparatedFromRoom.objects.get(separation=self.separation)
        super().__init__(*args, **kwargs)
        assert isinstance(self.separation, AnimalSeparation)

    def save(self):
        date = self.separation.date
        flock = self.separation.flock
        room_exit = AnimalRoomExit.objects.get(date=date, flock=flock, number_of_animals=1)
        room_entry = AnimalRoomEntry.objects.get(date=date, flock=flock, number_of_animals=1, room__is_separation=True)
        self.separation.delete()
        room_exit.delete()
        room_entry.delete()


class FeedTransitionForm(EasyFatForm):
    date = DateField()
    feed_type = ModelChoiceField(queryset=FeedType.objects.all())
    rooms = ModelMultipleChoiceField(queryset=Room.objects.filter(is_separation=False), widget=RoomSelectionWidget)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date'].widget.attrs.update(
            {'data-provide': 'datepicker-inline', 'class': 'form-control datepicker',
             'data-date-end-date': datetime.today().date().isoformat()})
        self.fields['date'].initial = datetime.today().date()

    def save(self):
        date = self.cleaned_data.get('date')
        feed_type = self.cleaned_data.get('feed_type')
        selected_rooms = self.cleaned_data.get('rooms')
        for room in selected_rooms:
            room_feed_change = RoomFeedingChange(date=date, feed_type=feed_type, room=room)
            room_feed_change.save()


class FeedEntryForm(EasyFatForm):
    date = DateField()
    feed_type = ModelChoiceField(queryset=FeedType.objects.all())
    weight = FloatField()
    silo = ModelChoiceField(queryset=Silo.objects.all())
    remaining = FloatField()

    def clean(self):
        super().clean()
        data = self.cleaned_data
        feed_type = data['feed_type']
        silo = data['silo']
        total = data['weight'] + data['remaining']
        if feed_type != silo.feed_type:
            raise ValidationError('Feedtype not for this silo.')

        if total > silo.capacity:
            raise ValidationError('Total weight is more than silo capacity.')

    def save(self):
        data = self.cleaned_data
        date = data['date']
        feed_type = data['feed_type']
        silo = data['silo']
        weight = data['weight']
        remaining = data['remaining']
        feed_entry = FeedEntry(date=date, weight=weight, feed_type=feed_type)
        feed_entry.save()
        silo_feed_entry = SiloFeedEntry(feed_entry=feed_entry, silo=silo, remaining=remaining)
        silo_feed_entry.save()


class TreatmentRoomAndSymptomsForm(EasyFatForm):

    """First form in the New Treatment Wizard."""

    date = DateField()
    room = ModelChoiceField(queryset=Room.objects.all())
    symptoms = CharField()


class MedicationChoiceForm(EasyFatForm):

    """Second step in the New Treatment Wizard."""

    medication = ModelChoiceField(queryset=Medication.objects.all(), required=False)
    override = ModelChoiceField(queryset=Medication.objects.all(), required=False)

    def __init__(self, *args, **kwargs):
        suggested_list = kwargs.pop('suggested', [])
        super().__init__(*args, **kwargs)
        self.fields['medication'].queryset = Medication.objects.filter(pk__in=suggested_list)
        self.fields['override'].queryset = Medication.objects.exclude(pk__in=suggested_list)


    def clean(self):
        medication = self.cleaned_data['medication']
        override = self.cleaned_data['override']
        if (medication is not None) and (override is not None):
            raise ValidationError('Choose only one medication from one of the lists.')


class DosageConfirmationForm(EasyFatForm):

    """Third step in the New Treatment Wizard."""

    dosage = FloatField(min_value=0.01)
    confirm_application = BooleanField(required=False)
    separate = BooleanField(required=False)
    destination_room = ModelChoiceField(queryset=Room.objects.filter(is_separation=True), required=False)
