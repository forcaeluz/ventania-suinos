from django.db import models
from datetime import datetime, timedelta


class FeedType(models.Model):
    name = models.CharField(max_length=20, unique=True, null=False)
    start_feeding_age = models.IntegerField()
    stop_feeding_age = models.IntegerField()

    def __str__(self):
        return self.name

    @property
    def remaining_weight(self):
        last_entries = self.feedentry_set.order_by('date')
        if last_entries.count() == 0:
            return 0
        else:
            return self.__get_remaining_weight()

    @property
    def days_since_last_deliver(self):
        entry = self.feedentry_set.order_by('date').last()
        if entry is not None:
            entry_date = entry.date
            today = datetime.today().date()
            delta = today - entry_date
            return delta.days

        return None

    @property
    def feed_end_date(self):
        entry = self.feedentry_set.order_by('date').last()
        if entry is not None:
            return entry.date + timedelta(days=self.__get_average_entry_interval())
        return None

    def __get_average_entry_interval(self):
        initial_date = datetime.now() - timedelta(days=365)     # look into past year.
        found_entries = self.feedentry_set.filter(date__gt=initial_date).order_by('date')
        interval_sum = 0

        if found_entries.count() < 2:
            return 14

        for entry, next_entry in zip(found_entries, found_entries[1:]):
            delta = next_entry.date - entry.date
            interval_sum += delta.days

        return interval_sum / (found_entries.count()-1)

    def __get_remaining_weight(self):
        average_entry_interval = self.__get_average_entry_interval()
        last_entry = self.feedentry_set.order_by('date').last()
        remaining_time = average_entry_interval - self.days_since_last_deliver
        return max(0.0, last_entry.weight * remaining_time / average_entry_interval)


class FeedEntry(models.Model):
    date = models.DateField()
    weight = models.FloatField()
    feed_type = models.ForeignKey(to=FeedType)


