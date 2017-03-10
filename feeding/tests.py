from django.test import TestCase
from datetime import date, timedelta, datetime
from .models import FeedType, FeedEntry


# Create your tests here.
class FeedingTests(TestCase):

    def test_days_since_delivery(self):
        feed_type = FeedType(name='S2', start_feeding_age=0, stop_feeding_age=1)
        feed_type.save()
        entry_date = datetime.today() - timedelta(days=7)
        feed_type.feedentry_set.create(date=entry_date.date(), weight=10000)
        self.assertEqual(7, feed_type.days_since_last_deliver)

    def test_remaining_weight_single_delivery(self):
            feed_type = FeedType(name='S2', start_feeding_age=0, stop_feeding_age=1)
            feed_type.save()
            entry_date = datetime.today() - timedelta(days=7)
            feed_type.feedentry_set.create(date=entry_date.date(), weight=28)
            self.assertEqual(14, feed_type.remaining_weight)
