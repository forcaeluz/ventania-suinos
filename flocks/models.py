from django.db import models
import datetime


class Flock(models.Model):

    entry_date = models.DateField()
    entry_weight = models.DecimalField(decimal_places=3, max_digits=9)
    number_of_animals = models.IntegerField()

    @property
    def flock_name(self):
        return '%d_%d' % (self.entry_date.year, self.id)

    @property
    def expected_exit_date(self):
        date = self.entry_date + datetime.timedelta(days=90)
        return date

    @property
    def number_of_living_animals(self):
        number_of_gone_animals = 0

        for exits in self.animalexits_set.all():
            number_of_gone_animals += exits.number_of_animals

        number_of_gone_animals += self.animaldeath_set.count()
        return self.number_of_animals - number_of_gone_animals

    @property
    def average_entry_weight(self):
        return self.entry_weight / self.number_of_animals

    @property
    def computed_daily_growth(self):
        return 0.0

    def __str__(self):
        return self.flock_name


class AnimalDeath(models.Model):
    date = models.DateField()
    weight = models.IntegerField()
    flock = models.ForeignKey(Flock)


class AnimalExits(models.Model):
    date = models.DateField()
    total_weight = models.DecimalField(decimal_places=3, max_digits=9)
    number_of_animals = models.IntegerField()
    flock = models.ForeignKey(Flock)

    @property
    def grow_rate(self):
        entry_weight = self.flock.get_average_entry_weight()
        exit_weight = self.average_weight
        time_interval = self.date - self.flock.entry_date
        return (exit_weight - entry_weight) / time_interval.days

    @property
    def average_weight(self):
        return self.total_weight / self.number_of_animals
