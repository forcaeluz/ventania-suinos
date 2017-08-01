from django.db import models
from django.utils.dateparse import parse_date

from flocks.models import Flock, AnimalDeath, AnimalSeparation, AnimalFarmExit
from feeding.models import FeedType

from datetime import date
from itertools import chain


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

    def get_occupancy_at_date(self, at_date=date.today()):
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

    def get_occupancy_transitions(self, start_date, end_date):
        if isinstance(start_date, str):
            start_date = parse_date(start_date)
        if isinstance(end_date, str):
            end_date = parse_date(end_date)

        entries = self.animalroomentry_set.filter(date__gt=start_date, date__lte=end_date)
        exits = self.animalroomexit_set.filter(date__gt=start_date, date__lte=end_date)
        changes = chain(entries, exits)
        changes = sorted(changes, key=lambda instance: instance.date)
        start = self.get_occupancy_at_date(start_date)
        results = {start_date: start}
        for change in changes:
            results.update({change.date: self.get_occupancy_at_date(change.date)})

        results.update({end_date: self.get_occupancy_at_date(end_date)})
        return results

    def get_animal_days_for_period(self, start_date, end_date):
        changes = self.get_occupancy_transitions(start_date, end_date)
        dates = sorted(changes.keys())
        previous_count = changes[dates[0]]
        previous_date = dates[0]
        animals_days = 0
        for transition_date in dates[1:]:
            days = (transition_date - previous_date).days
            animals_days += previous_count * days
            previous_date = transition_date
            previous_count = changes[transition_date]

        return animals_days

    def __str__(self):
        return self.group.name + ' - ' + self.name

    def get_feeding_type_at(self, at_date=date.today()):
        feed_change = self.roomfeedingchange_set.filter(date__lte=at_date).order_by('-date').first()
        if feed_change is None:
            return None
        else:
            return feed_change.feed_type


class AnimalRoomEntry(models.Model):
    date = models.DateField()
    number_of_animals = models.IntegerField()
    flock = models.ForeignKey(Flock)
    room = models.ForeignKey(Room)

    def __str__(self):
        return self.room.__str__() + ' - ' + str(self.number_of_animals)


class AnimalRoomExit(models.Model):
    date = models.DateField()
    room = models.ForeignKey(Room)
    number_of_animals = models.IntegerField()
    flock = models.ForeignKey(Flock)
    farm_exit = models.ForeignKey(AnimalFarmExit, null=True)


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


class RoomFeedingChange(models.Model):
    date = models.DateField()
    feed_type = models.ForeignKey(to=FeedType)
    room = models.ForeignKey(to=Room)
