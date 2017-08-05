from django.core.validators import ValidationError

from flocks.models import Flock, AnimalFarmExit, AnimalFlockExit
from buildings.models import Room, AnimalRoomExit, AnimalRoomEntry


class AnimalExit:
    """
    Class that combines Farm, Flock and Room exit information.
    """
    def __init__(self, animal_farm_exit=None):
        self.animal_farm_exit = animal_farm_exit  # AnimalFarmExit
        self.flock_exits = []
        self.room_exits = []
        self.total_weight = []
        self.average_exit_weight = []

        if animal_farm_exit is not None:
            self.flock_exits = self.animal_farm_exit.animalflockexit_set.all()
            self.room_exits = self.animal_farm_exit.animalroomexit_set.all()

    def set_animal_farm_exit(self, **kwargs):
        instance = kwargs.get('separation', None)
        data = kwargs.get('cleaned_data', None)
        if instance:
            self.animal_farm_exit = instance
            self.flock_exits = self.animal_farm_exit.animalflockexit_set.all()
            self.room_exits = self.animal_farm_exit.animalroomexit_set.all()
        elif data:
            self.animal_farm_exit = AnimalFarmExit(date=data['date'])
            self.total_weight = data['weight']
            self.average_exit_weight = self.total_weight / data['number_of_animals']
        else:
            raise ValueError('Not possible to assign flock information')
        pass

    def set_room_exit_information(self, room_exits_information):
        assert (self.animal_farm_exit is not None)
        date = self.animal_farm_exit.date

        for room_exit_info in room_exits_information:
            room = room_exit_info['room']  # Room
            if len(room.get_flocks_present_at(date)) == 1:
                flock = next(iter(room.get_flocks_present_at(date)))
                room_exit = AnimalRoomExit(number_of_animals=room_exit_info['number_of_animals'],
                                           flock=flock,
                                           date=self.animal_farm_exit.date,
                                           room=room,
                                           farm_exit=self.animal_farm_exit)
                self.room_exits.append(room_exit)
            else:
                print(room.get_flocks_present_at(date))
                raise ValueError('Unable to handle rooms with more than one flock.')

        self.__generate_flock_exits()

    def __generate_flock_exits(self):
        flock_info = {}
        date = self.animal_farm_exit.date
        for room_exit in self.room_exits:
            if len(room_exit.room.get_flocks_present_at(date)) == 1:
                flock = next(iter(room_exit.room.get_flocks_present_at(date)))
                flock_info.update({flock: flock_info.get(flock, 0) + room_exit.number_of_animals})
            else:
                raise ValueError('Unable to handle rooms with multiple flocks present.')

        for flock, number_of_animals in flock_info.items():
            flock_exit = AnimalFlockExit(flock=flock,
                                         farm_exit=self.animal_farm_exit,
                                         number_of_animals=number_of_animals,
                                         weight=self.average_exit_weight * number_of_animals)

            self.flock_exits.append(flock_exit)

    def clean(self):
        self.animal_farm_exit.clean()

    def save(self):
        self.animal_farm_exit.save()

        for flock_exit in self.flock_exits:
            flock_exit.farm_exit = self.animal_farm_exit
            flock_exit.save()

        for room_exit in self.room_exits:
            room_exit.farm_exit = self.animal_farm_exit
            room_exit.save()


class AnimalEntry:
    """Class that combines RoomEntry and Flock Information.

    This class is used to create, edit or delete information about animal entries in the farm. That means it
    combines the information about a new Flock, together with room entry information for this flock.
    """

    def __init__(self):
        """Constructor, only to initialize variables."""
        self.flock = None
        self.room_entries = []

    def set_flock(self, **kwargs):
        """Set the Flock information for the AnimalEntry model.

        :param kwargs: There are two options to set the Flock. Either by instance, or by data.
        :return:
        """
        instance = kwargs.get('instance', None)
        data = kwargs.get('data', None)
        if instance:
            self.flock = instance
            self.room_entries = list(self.flock.animalroomentry_set.filter(date=self.flock.entry_date).all())
        elif data:
            self.flock = Flock(number_of_animals=data['number_of_animals'],
                               entry_date=data['date'],
                               entry_weight=data['weight'])
        else:
            raise ValueError('Not possible to assign flock information')

    def update_flock(self, data):
        """Update the flock information.

        :param data: The flock information, given as a dictionary.
        """
        assert(self.flock is not None)
        self.flock.number_of_animals = data['number_of_animals']
        self.flock.entry_date = data['date']
        self.flock.entry_weight = data['weight']
        for room_entry in self.room_entries:
            room_entry.date = self.flock.entry_date

    def set_room_entries(self, room_entries_info):
        """Set the room entries information.

        :param room_entries_info: The room entries information, given as a dictionary.
        """
        assert(self.flock is not None)
        self.update_room_entries(room_entries_info)

    def update_room_entries(self, room_entries_info):
        """Update the room entries information.

        :param room_entries_info: New data, as a dictionary.
        """
        assert(self.flock is not None)
        existing_room_list = [obj.room for obj in self.room_entries]
        # The final list
        final_room_list = [obj['room'] for obj in room_entries_info]
        # Room entries to be deleted
        delete_list = [obj for obj in self.room_entries if obj.room not in final_room_list]
        # Room entries to be added
        add_list = [obj for obj in room_entries_info if obj['room'] not in existing_room_list]
        # Room entries to be updated
        update_list = [obj for obj in room_entries_info if obj not in add_list]
        self.room_entries = [obj for obj in self.room_entries if obj.room in final_room_list]

        # Delete entries
        for room_entry in delete_list:
            room_entry.delete()

        for room_entry in update_list:
            self.__update_room_entry_information(room_entry)

        for new_room_info in add_list:
            room_entry = AnimalRoomEntry(number_of_animals=new_room_info['number_of_animals'],
                                         flock=self.flock,
                                         date=self.flock.entry_date,
                                         room=new_room_info['room'])
            self.room_entries.append(room_entry)

    def __update_room_entry_information(self, new_info):
        for old_entry in self.room_entries:
            if old_entry.room == new_info['room']:
                old_entry.number_of_animals = new_info['number_of_animals']
                old_entry.date = self.flock.entry_date

    def clean(self):
        """Perform the computation to check the validity of the data.

        :raises: Validation error, if the number of animals placed in rooms is not equal to the number of animals in the
        flock.
        """
        count = 0
        self.flock.full_clean()
        for room_entry in self.room_entries:
            count += room_entry.number_of_animals

        if count != self.flock.number_of_animals:
            raise ValidationError('Number of animals in flock is different than in rooms.')

    def is_valid(self):
        """Check the validity of the data.

        :return: True if valid, false otherwise.
        """
        try:
            self.clean()
        except ValidationError:
            return False
        except AssertionError:
            return False

        return True

    def save(self):
        """Save the data. """
        self.flock.save()
        for room_entry in self.room_entries:
            room_entry.flock = self.flock
            room_entry.save()

    def delete(self):
        """Delete the flock and room entries information."""
        self.flock.delete()
