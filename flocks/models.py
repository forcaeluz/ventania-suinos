from django.db import models
from math import ceil
import datetime


class Flock(models.Model):

    entry_date = models.DateField()
    entry_weight = models.FloatField()
    number_of_animals = models.IntegerField()

    @property
    def flock_name(self):
        return '%d_%d' % (self.entry_date.year, self.id)

    @property
    def expected_exit_date(self):
        date_year_before = self.entry_date - datetime.timedelta(days=365)
        exits = AnimalFlockExit.objects.filter(farm_exit__date__gte=date_year_before)
        grow_rate = self.__compute_grow_rate_for_exits_set(exits)
        if grow_rate is None:
            grow_rate = 0.850

        growing_days = ceil((115 - self.average_entry_weight) / grow_rate)
        date = self.entry_date + datetime.timedelta(days=growing_days)
        return date

    @property
    def number_of_living_animals(self):
        number_of_gone_animals = 0

        for exits in self.animalflockexit_set.all():
            number_of_gone_animals += exits.number_of_animals

        number_of_gone_animals += self.animaldeath_set.count()
        return self.number_of_animals - number_of_gone_animals

    @property
    def average_entry_weight(self):
        return self.entry_weight / self.number_of_animals

    @property
    def computed_daily_growth(self):
        exits_set = self.animalflockexit_set.all()
        return self.__compute_grow_rate_for_exits_set(exits_set)

    @property
    def average_exit_weight(self):
        exits_set = self.animalflockexit_set.all()
        weight = sum([obj.weight for obj in exits_set])
        animals = sum([obj.number_of_animals for obj in exits_set])
        if animals > 0:
            return weight/animals
        else:
            return 0

    @property
    def separated_animals(self):
        separation_set = self.animalseparation_set.all()
        active_separations = len([obj for obj in separation_set if obj.active])
        return active_separations

    @staticmethod
    def __compute_grow_rate_for_exits_set(exits_set):
        total_number_of_animals = 0
        average_grow = 0
        for animal_exit in exits_set:
            total_number_of_animals += animal_exit.number_of_animals
            average_grow += animal_exit.grow_rate * animal_exit.number_of_animals

        if total_number_of_animals == 0:
            return None

        return average_grow / total_number_of_animals

    @property
    def death_percentage(self):
        return (self.animaldeath_set.count() / self.number_of_animals) * 100

    def __str__(self):
        return self.flock_name


class AnimalDeath(models.Model):
    date = models.DateField()
    weight = models.FloatField()
    cause = models.TextField()
    flock = models.ForeignKey(Flock)


class AnimalFarmExit(models.Model):
    date = models.DateField()
    weight = models.FloatField()
    number_of_animals = models.IntegerField()
    destination = models.CharField(max_length=140, default='Unknown')

    @property
    def average_weight(self):
        return self.weight / self.number_of_animals


class AnimalFlockExit(models.Model):
    weight = models.FloatField()
    number_of_animals = models.IntegerField()
    flock = models.ForeignKey(Flock)
    farm_exit = models.ForeignKey(AnimalFarmExit)

    @property
    def grow_rate(self):
        entry_weight = self.flock.average_entry_weight
        exit_weight = self.average_weight
        time_interval = self.farm_exit.date - self.flock.entry_date
        return (exit_weight - entry_weight) / time_interval.days

    @property
    def average_weight(self):
        return self.weight / self.number_of_animals

    @property
    def date(self):
        return self.farm_exit.date


class AnimalSeparation(models.Model):
    date = models.DateField()
    reason = models.CharField(max_length=250)
    flock = models.ForeignKey(Flock)
    death = models.ForeignKey(AnimalDeath, null=True, blank=True, on_delete=models.SET_NULL)
    exit = models.ForeignKey(AnimalFlockExit, null=True, blank=True, on_delete=models.SET_NULL)

    @property
    def active(self):
        return (self.death is None) and (self.exit is None)

    def __str__(self):
        return '@' + str(self.date) + ' reas:' + self.reason
