from django.shortcuts import Http404
from django.core.validators import ValidationError

from flocks.models import Flock, AnimalExits
from buildings.models import Room, AnimalRoomExit, AnimalRoomEntry


class AnimalExitWizardSaver:

    def __init__(self, group_form, rooms_form):
        self.group_form = group_form
        self.room_form = rooms_form

    def get_animal_exits(self):
        animal_exits = []
        rooms = self.room_form.get_exited_rooms()
        exit_date = self.group_form.cleaned_data.get('date')
        flock_exits = {}
        flocks_present = [obj for obj in Flock.objects.all() if obj.number_of_living_animals > 0]
        for room_form in rooms:
            room = room_form.cleaned_data.get('room')
            for flock in flocks_present:
                if room.get_animals_for_flock(flock.id, exit_date):
                    count = flock_exits.get(flock, 0)
                    count += room_form.cleaned_data.get('number_of_animals')
                    flock_exits.update({flock: count})

        date = self.group_form.cleaned_data.get('date')
        weight = self.group_form.cleaned_data.get('weight')
        total_nof_animals = self.group_form.cleaned_data.get('number_of_animals')
        avg_weight = weight / total_nof_animals
        for an_exit in flock_exits.keys():
            flock_number_of_animals = flock_exits.get(an_exit)
            total_weight = flock_number_of_animals*avg_weight
            animal_exit = AnimalExits(date=date,
                                      total_weight=total_weight,
                                      flock=an_exit,
                                      number_of_animals=flock_number_of_animals)
            animal_exits.append(animal_exit)

        return animal_exits

    def get_room_exits(self):
        room_exits = []
        rooms = self.room_form.get_exited_rooms()
        exit_date = self.group_form.cleaned_data.get('date')
        flocks_present = [obj for obj in Flock.objects.all() if obj.number_of_living_animals > 0]
        for room_form in rooms:
            room = room_form.cleaned_data.get('room')
            for flock in flocks_present:
                if room.get_animals_for_flock(flock.id, exit_date):
                    animals = room_form.cleaned_data.get('number_of_animals')
                    room_exit = AnimalRoomExit(room=room,
                                               date=exit_date,
                                               number_of_animals=animals,
                                               flock=flock)
                    room_exits.append(room_exit)

        return room_exits

    def save(self):
        room_exits = self.get_room_exits()
        animal_exits = self.get_animal_exits()
        for obj in room_exits:
            obj.full_clean()

        for obj in animal_exits:
            obj.full_clean()

        for obj in room_exits:
            obj.save()

        for obj in animal_exits:
            obj.save()


class AnimalEntry:
    """
    Class that combines RoomEntry and Flock Information.
    
    This class is used to create or edit RoomEntry and Flock Information.
    """
    def __init__(self, flock=None):
        self.flock = flock
        if self.flock is not None:
            self.room_entries = flock.animalroomentry_set()
        else:
            self.room_entries = []

    def set_flock(self, **kwargs):
        instance = kwargs.get('instance', None)
        data = kwargs.get('cleaned_data', None)
        if instance:
            self.flock = instance
        elif data:
            self.flock = Flock(number_of_animals=data['number_of_animals'],
                               entry_date=data['date'],
                               entry_weight=data['weight'])
        else:
            raise ValueError('Not possible to assign flock information')

    def set_room_entries(self, room_info):
        assert(self.flock is not None)
        room_info = [room for room in room_info if room['number_of_animals'] > 0]
        for room in room_info:
            room_entry = AnimalRoomEntry(number_of_animals=room['number_of_animals'],
                                         flock=self.flock,
                                         date=self.flock.entry_date,
                                         room=room['room'])
            self.room_entries.append(room_entry)

    def clean(self):
        count = 0
        self.flock.full_clean()
        for room_entry in self.room_entries:
            room_entry.full_clean()
            count += room_entry.number_of_animals

    def save(self):
        self.flock.save()
        for room_entry in self.room_entries:
            room_entry.save()
