from django.db import models
from django.utils.dateparse import parse_date

from flocks.models import Flock, AnimalDeath, AnimalSeparation, AnimalFarmExit
from feeding.models import FeedType, FeedEntry

from datetime import date, timedelta
from itertools import chain


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

    def animal_days_for_feed_type(self, start_date, end_date, feed_type):
        total = 0
        for group in self.roomgroup_set.all():
            total += group.animal_days_for_feed_type(start_date, end_date, feed_type)

        for room in self.room_set.all():
            total += room.get_animal_days_for_feeding_period(start_date, end_date, feed_type)

        return total

    def __str__(self):
        return self.name


class Building(RoomGroup):
    location = models.CharField(max_length=150, blank=True)

    def feed_capacity(self, feed_type):
        capacity = 0
        for silo in self.silo_set.all():
            if silo.feed_type == feed_type:
                capacity += silo.capacity

        return capacity

    def get_feed_entries(self, start_date, end_date, feed_type):
        if isinstance(start_date, str):
            start_date = parse_date(start_date)
        if isinstance(end_date, str):
            end_date = parse_date(end_date)

        silos = self.silo_set.filter(feed_type=feed_type)
        entries = []
        for silo in silos:
            s_entries = silo.silofeedentry_set.filter(feed_entry__date__gte=start_date, feed_entry__date__lte=end_date)
            s_entries.order_by('feed_entry__date')
            entries.extend(list(s_entries))

        entries = sorted(entries, key=lambda instance: instance.feed_entry.date)
        return entries

    def get_last_feed_entries(self, at_date, feed_type):
        if isinstance(at_date, str):
            at_date = parse_date(at_date)

        silos = self.silo_set.filter(feed_type=feed_type)
        entries = []
        for silo in silos:
            s_entries = silo.silofeedentry_set.filter(feed_entry__date__lte=at_date).order_by('-feed_entry__date').first()
            if s_entries is not None:
                entries.append(s_entries)

        entries = sorted(entries, key=lambda instance: instance.date)
        if len(entries) >= 1:
            return entries[-1]
        else:
            return None

    def get_estimated_remaining_feed(self, at_date, feed_type):
        if isinstance(at_date, str):
            at_date = parse_date(at_date)

        end_date = at_date + timedelta(days=1)
        last_feed_entry = self.get_last_feed_entries(at_date, feed_type)
        if last_feed_entry is not None:
            consumption_animal_days = self.animal_days_for_feed_type(last_feed_entry.date, end_date, feed_type)
            consumption_kg = consumption_animal_days * self.get_average_feed_consumption(at_date, feed_type)
            return last_feed_entry.weight + last_feed_entry.remaining - consumption_kg
        else:
            return 0

    def get_average_feed_consumption(self, at_date, feed_type):
        if isinstance(at_date, str):
            at_date = parse_date(at_date)

        start_date = at_date - timedelta(365)
        entries = self.get_feed_entries(start_date, at_date, feed_type)
        intervals = zip(entries, entries[1:])
        interval_count = len(entries) - 1
        average = 0
        for entry, next_entry in intervals:
            weight_begin = entry.weight + entry.remaining
            weight_end = next_entry.remaining
            avg_for_entry = (weight_begin - weight_end) / self.animal_days_for_feed_type(entry.date,
                                                                                         next_entry.date, feed_type)

            average += avg_for_entry / interval_count
        return average

    def get_estimated_feed_end_date(self, at_date, feed_type):
        if isinstance(at_date, str):
            at_date = parse_date(at_date)

        remaining_feed = self.get_estimated_remaining_feed(at_date, feed_type)
        average_daily_consumption = self.get_average_feed_consumption(at_date, feed_type)
        current_consumption = self.animal_days_for_feed_type(at_date, at_date + timedelta(days=1), feed_type)
        daily_consumption = average_daily_consumption * current_consumption
        if daily_consumption > 0:
            remaining_days = remaining_feed / daily_consumption
            return at_date + timedelta(days=remaining_days)
        else:
            return None


class Silo(models.Model):
    capacity = models.FloatField()
    feed_type = models.ForeignKey(to=FeedType)
    name = models.CharField(max_length=20)
    building = models.ForeignKey(to=Building)

    def __str__(self):
        return self.name


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

    def get_animal_days_for_feeding_period(self, start_date, end_date, feed_type):
        feeding_periods = self.get_feeding_periods(start_date, end_date, feed_type)
        count = 0
        for period in feeding_periods:
            count += self.get_animal_days_for_period(period[0], period[1])

        return count

    def get_feeding_type_at(self, at_date=date.today()):
        feed_change = self.roomfeedingchange_set.filter(date__lte=at_date).order_by('-date').first()
        if feed_change is None:
            return None
        else:
            return feed_change.feed_type

    def __str__(self):
        return self.group.name + ' - ' + self.name

    def get_feeding_periods(self, start_date, end_date, feed_type):
        feeding_periods = []
        if isinstance(start_date, str):
            start_date = parse_date(start_date)
        if isinstance(end_date, str):
            end_date = parse_date(end_date)

        feed_change_before_period = self.roomfeedingchange_set.filter(date__lte=start_date).order_by('-date').first()
        if feed_change_before_period is None:
            return feeding_periods

        feeding_date = feed_change_before_period.date
        feeding_change_set = self.roomfeedingchange_set
        feeding_transitions = feeding_change_set.filter(date__gte=feeding_date, date__lte=end_date).order_by('date')

        start_of_feeding_period = None
        for transition in feeding_transitions:
            # We are looking for a start period, and we found one
            if start_of_feeding_period is None and transition.feed_type == feed_type:
                start_of_feeding_period = transition.date
            # We have a start period, looking for an end period
            elif start_of_feeding_period is not None and transition.feed_type != feed_type:
                feeding_periods.append([start_of_feeding_period, transition.date])
                start_of_feeding_period = None

        if start_of_feeding_period is not None:
            feeding_periods.append([start_of_feeding_period, end_date])

        if len(feeding_periods) > 0:
            if feeding_periods[0][0] < start_date:
                feeding_periods[0][0] = start_date
        return feeding_periods


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


class SiloFeedEntry(models.Model):
    """
    Creates the link between the Silo where the feed is placed in, and the feed entry itself.
    """
    feed_entry = models.ForeignKey(to=FeedEntry)
    silo = models.ForeignKey(to=Silo)
    remaining = models.FloatField(default=0)

    @property
    def weight(self):
        return self.feed_entry.weight

    @property
    def date(self):
        return self.feed_entry.date
