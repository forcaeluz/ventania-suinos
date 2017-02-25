from django.db import models
from flocks.models import Flock


class FeedType(models.Model):
    name = models.CharField(max_length=20, unique=True, null=False)
    start_feeding_age = models.IntegerField()
    stop_feeding_age = models.IntegerField()


class FeedEntry(models.Model):
    date = models.DateField()
    weight = models.DecimalField(decimal_places=3, max_digits=9)
    feed_type = models.ForeignKey(to=FeedType)


class FlockFeedMutation(models.Model):
    """
    Class that links the types of feed being fed to the flocks.
    """
    date = models.DateField()
    flock = models.ForeignKey(to=Flock)
    feed_type = models.ForeignKey(to=FeedType, null=True)