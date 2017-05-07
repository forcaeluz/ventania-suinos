from django.db import models
from flocks.models import Flock, AnimalDeath, AnimalSeparation
from datetime import date


class Silo(models.Model):
    capacity = models.FloatField()
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name


class RoomGroup(models.Model):
    name = models.CharField(max_length=20)
    group = models.ForeignKey('self', blank=True, null=True)

    @property
    def number_of_rooms(self):
        count = 0
        for group in self.roomgroup_set.all():
            count += group.number_of_rooms

        count += self.room_set.count()
        return count

    @property
    def animal_capacity(self):
        count = 0
        for group in self.roomgroup_set.all():
            count += group.animal_capacity

        for room in self.room_set.all():
            count += room.capacity

        return count

    @property
    def occupancy(self):
        count = 0
        for group in self.roomgroup_set.all():
            count += group.occupancy

        for room in self.room_set.all():
            count += room.occupancy

        return count

    def __str__(self):
        return self.name


class Building(RoomGroup):
    supplied_by = models.ManyToManyField(Silo)
    location = models.CharField(max_length=150, blank=True)

    @property
    def feed_capacity(self):
        capacity = 0
        for silo in self.supplied_by.all():
            capacity += silo.capacity
        return capacity


class Room(models.Model):
    capacity = models.IntegerField()
    name = models.CharField(max_length=20)
    group = models.ForeignKey(RoomGroup)
    is_separation = models.BooleanField(default=False)

    @property
    def occupancy(self, at_date=date.today()):
        count = 0
        for entry in self.animalroomentry_set.filter(date__lte=at_date):
            count += entry.number_of_animals

        for room_exit in self.animalroomexit_set.filter(date__lte=at_date):
            count -= room_exit.number_of_animals
        return count

    def get_animals_for_flock(self, flock_id, at_date=date.today()):
        count = 0
        for entry in self.animalroomentry_set.filter(flock_id=flock_id, date__lte=at_date):
            count += entry.number_of_animals

        for room_exit in self.animalroomexit_set.filter(flock_id=flock_id, date__lte=at_date):
            count -= room_exit.number_of_animals
        return count

    def get_flocks_present_at(self, at_date=date.today()):
        flocks = {}
        for entry in self.animalroomentry_set.filter(date__lte=at_date):
            count = flocks.get(entry.flock, 0) + entry.number_of_animals
            flocks.update({entry.flock: count})

        for room_exit in self.animalroomexit_set.filter(date__lte=at_date):
            count = flocks.get(room_exit.flock, 0) - room_exit.number_of_animals
            flocks.update({room_exit.flock: count})

        flocks = {key: value for key, value in flocks.items() if value > 0}

        return flocks

    def __str__(self):
        return self.group.name + ' - ' + self.name


class AnimalRoomEntry(models.Model):
    date = models.DateField()
    number_of_animals = models.IntegerField()
    flock = models.ForeignKey(Flock)
    room = models.ForeignKey(Room)


class AnimalRoomExit(models.Model):
    date = models.DateField()
    room = models.ForeignKey(Room)
    number_of_animals = models.IntegerField()
    flock = models.ForeignKey(Flock)


class DeathInRoom(models.Model):
    """
        Model only used for statistics, to couple a death to a certain room.
    """
    room = models.ForeignKey(Room)
    death = models.ForeignKey(AnimalDeath)


class AnimalSeparatedFromRoom(models.Model):
    """
        Model only used for statistics, to couple a separation to a room. Note that this is the room "from" where the
        animal was separated, and not the room to which it went to.
    """
    room = models.ForeignKey(Room, related_name='source_room')
    destination = models.ForeignKey(Room, related_name='destination_room', null=True)
    separation = models.ForeignKey(AnimalSeparation)

