from flocks.models import Flock, AnimalExits
from buildings.models import Room, AnimalRoomExit


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
