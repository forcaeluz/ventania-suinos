from django.db import models


class FeedType(models.Model):
    name = models.TextField(max_length=20)
    start_feeding_at = models.IntegerField()
    stop_feeding_at = models.IntegerField()


class FeedEntry(models.Model):
    date = models.DateField()
    weight = models.DecimalField(decimal_places=3, max_digits=9)
    feed_type = models.ForeignKey(to=FeedType)
