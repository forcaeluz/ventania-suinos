from django import forms
from django.utils.translation import ugettext as tr
from django.core.validators import ValidationError
from .models import AnimalRoomEntry, AnimalRoomExit
from .models import Room, DeathInRoom, AnimalSeparatedFromRoom
from flocks.models import Flock, AnimalExits, AnimalDeath, AnimalSeparation


class FlockEntryRoomFormSet(forms.BaseModelFormSet):
    def clean(self):
        if any(self.errors):
            return
        flocks = {obj.__str__(): obj.number_of_animals for obj in Flock.objects.all() if
                  obj.number_of_living_animals > 0}
        for form in self.forms:
            flocks[form.cleaned_data['flock'].__str__()] -= form.cleaned_data['number_of_animals']
            if flocks[form.cleaned_data['flock'].__str__()] < 0:
                raise forms.ValidationError("More animals in rooms than possible for flock: " +
                                            form.cleaned_data['flock'].__str__())

    def save(self, commit=True):
        for entry in self.forms:
            date = entry.cleaned_data['flock'].entry_date
            room_entry = entry.save(commit=False)
            room_entry.date = date
            room_entry.save()

        return super().save(commit)


class FlockEntryRoomForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['room'].queryset = Room.objects.filter(id=kwargs['initial']['room'].id)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
            })
            if self.fields[field].error_messages:
                self.fields[field].widget.attrs.update({'class': 'form-control'})
        self.fields['room'].widget.attrs['readonly'] = True

        flocks = [obj.id for obj in Flock.objects.all() if obj.number_of_living_animals > 0]
        self.fields['flock'].queryset = Flock.objects.filter(pk__in=flocks)

    def save(self, commit=True):
        return super().save(commit)

    class Meta:
        model = AnimalRoomEntry
        fields = ['flock', 'number_of_animals', 'room']


class AnimalExitRoomForm(forms.ModelForm):
    animal_exit = forms.IntegerField(widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
            })
            if self.fields[field].error_messages:
                self.fields[field].widget.attrs.update({'class': 'form-control'})
        self.fields['room'].widget.attrs['readonly'] = True


    class Meta:
        model = AnimalRoomExit
        fields = ['room', 'number_of_animals']

    def clean_number_of_animals(self):
        number_of_animals = self.cleaned_data['number_of_animals']
        if number_of_animals < 0:
            raise ValidationError(tr('The number of exiting animals should be greater than 0'))
        return number_of_animals

    def clean(self):
        cleaned_data = super().clean()
        number_of_animals = cleaned_data.get('number_of_animals')
        room = cleaned_data.get('room')
        if number_of_animals and room and number_of_animals > room.occupancy:
            raise ValidationError(tr('The number of exiting animals should be smaller than the occupancy of the room'))


class AnimalExitRoomFormSet(forms.BaseModelFormSet):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queryset = AnimalRoomExit.objects.none()

    def clean(self):
        if any(self.errors):
            return
        animal_exit = AnimalExits.objects.get(id=self.forms[0].cleaned_data['animal_exit'])
        count = 0
        for form in self.forms:
            count += form.cleaned_data['number_of_animals']
            if animal_exit.id != form.cleaned_data['animal_exit']:
                raise ValidationError('Should not happen.')

        if count != animal_exit.number_of_animals:
            raise ValidationError('Number of animals out in form is different than in the exit.')

    def save(self, commit=True):
        for form in self.forms:
            animal_exit = AnimalExits.objects.get(id=form.cleaned_data['animal_exit'])
            date = animal_exit.date
            flock = animal_exit.flock
            room_exit = form.save(commit=False)
            room_exit.date = date
            room_exit.flock = flock
            room_exit.save()
        return super().save(commit)


class AnimalDeathRoomForm(forms.Form):
    death_id = forms.IntegerField(widget=forms.HiddenInput)
    room = forms.ModelChoiceField(queryset=Room.objects.all())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.is_bound:
            death_id = self.data[self.prefix + '-death_id']
        else:
            death_id = self.initial['death_id']

        if death_id != 0:
            self.death = AnimalDeath.objects.get(id=death_id)
            rooms = [obj.id for obj in Room.objects.filter(is_separation=False) if obj.get_animals_for_flock(self.death.flock) > 0]
            self.fields['room'].queryset = Room.objects.filter(pk__in=rooms)
        else:
            self.death = None
            self.fields['room'].queryset = Room.objects.none()

    def save(self):
        data = self.cleaned_data
        assert (isinstance(self.death, AnimalDeath))
        assert (self.death.deathinroom_set.count() == 0)
        room_exit = AnimalRoomExit(room=data['room'],
                                   date=self.death.date,
                                   number_of_animals=1,
                                   flock=self.death.flock)
        room_death = DeathInRoom(room=data['room'],
                                 death=self.death)

        room_exit.save()
        room_death.save()


class AnimalSeparationRoomForm(forms.Form):
    separation_id = forms.IntegerField(widget=forms.HiddenInput)
    exit_room = forms.ModelChoiceField(queryset=Room.objects.filter(is_separation=False))
    dest_room = forms.ModelChoiceField(queryset=Room.objects.filter(is_separation=True))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.is_bound:
            separation_id = self.data[self.prefix + '-separation_id']
        else:
            separation_id = self.initial['separation_id']

        if separation_id != 0:
            self.separation = AnimalSeparation.objects.get(pk=separation_id)
            rooms = [obj.id for obj in Room.objects.all() if obj.get_animals_for_flock(self.separation.flock) > 0]
            self.fields['exit_room'].queryset = Room.objects.filter(pk__in=rooms)
        else:
            # Invalid state, raise an exception
            self.separation = None
            self.fields['exit_room'].queryset = Room.objects.none()

    def save(self):
        data = self.cleaned_data
        assert(isinstance(self.separation, AnimalSeparation))
        room_exit = AnimalRoomExit(room=data['exit_room'],
                                   date=self.separation.date,
                                   number_of_animals=1,
                                   flock=self.separation.flock)
        room_exit.save()
        room_entry = AnimalRoomEntry(room=data['dest_room'],
                                     date=self.separation.date,
                                     number_of_animals=1,
                                     flock=self.separation.flock)
        room_entry.save()
        animal_separation_from_room = AnimalSeparatedFromRoom(room=data['exit_room'],
                                                              separation=self.separation)
        animal_separation_from_room.save()

        if self.separation.death_id:
            self._save_separation_death()
        elif self.separation.exit_id:
            self._save_separation_exit()

    def _save_separation_death(self):
        death = AnimalDeath.objects.get(pk=self.separation.death_id)
        sep_room_exit = AnimalRoomExit(room=self.cleaned_data['dest_room'],
                                       date=death.date,
                                       number_of_animals=1,
                                       flock=death.flock)
        sep_room_exit.save()
        room_death = DeathInRoom(room=self.cleaned_data['dest_room'],
                                 death=death)
        room_death.save()

    def _save_separation_exit(self):
        animal_exit = AnimalExits.objects.get(pk=self.separation.exit_id)
        sep_room_exit = AnimalRoomExit(room=self.cleaned_data['dest_room'],
                                       date=animal_exit.date,
                                       number_of_animals=1,
                                       flock=animal_exit.flock)
        sep_room_exit.save()