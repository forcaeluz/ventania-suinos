from django.test import TestCase
from datetime import date

from .models import Flock, Room, Building, FeedType
# Create your tests here.


class RoomTestCase(TestCase):

    def setUp(self):
        self.flock = Flock(entry_date='2017-01-01', entry_weight=220, number_of_animals=10)
        self.flock.save()
        self.building = Building(name='TheBigBuilding')
        self.building.save()
        self.room = Room(name='Room1', capacity=10, group=self.building)
        self.room.save()
        self.feed_type = FeedType(name='S3', start_feeding_age=0, stop_feeding_age=15)
        self.feed_type.save()
        self.feed_type2 = FeedType(name='S2', start_feeding_age=0, stop_feeding_age=15)
        self.feed_type2.save()

    def test_get_name(self):
        self.assertEqual('Room1', self.room.name)

    def test_occupancy_after_entry(self):
        self.room.animalroomentry_set.create(number_of_animals=10, flock=self.flock, date='2017-01-01')
        self.assertEqual(10, self.room.get_occupancy_at_date('2017-01-02'))

    def test_occupancy_after_exit(self):
        self.room.animalroomentry_set.create(number_of_animals=10, flock=self.flock, date='2017-01-01')
        self.room.animalroomexit_set.create(number_of_animals=1, flock=self.flock, date='2017-01-03')
        self.assertEqual(10, self.room.get_occupancy_at_date('2017-01-02'))
        self.assertEqual(9, self.room.get_occupancy_at_date('2017-01-04'))

    def test_occupancy_after_multiple_exits(self):
        self.room.animalroomentry_set.create(number_of_animals=10, flock=self.flock, date='2017-01-01')
        self.room.animalroomexit_set.create(number_of_animals=1, flock=self.flock, date='2017-01-03')
        self.room.animalroomexit_set.create(number_of_animals=1, flock=self.flock, date='2017-01-05')
        self.assertEqual(10, self.room.get_occupancy_at_date('2017-01-02'))
        self.assertEqual(9, self.room.get_occupancy_at_date('2017-01-04'))
        self.assertEqual(8, self.room.get_occupancy_at_date('2017-01-05'))

    def test_occupancy_changes_1(self):
        expected_output = {date(2017, 1, 1): 10,
                           date(2017, 1, 3): 9,
                           date(2017, 1, 5): 8,
                           date(2017, 1, 6): 8}
        self.room.animalroomentry_set.create(number_of_animals=10, flock=self.flock, date='2017-01-01')
        self.room.animalroomexit_set.create(number_of_animals=1, flock=self.flock, date='2017-01-03')
        self.room.animalroomexit_set.create(number_of_animals=1, flock=self.flock, date='2017-01-05')
        changes = self.room.get_occupancy_transitions(date(2017, 1, 1), '2017-01-06')
        self.assertEqual(4, len(changes))
        self.assertEqual(expected_output, changes)

    def test_occupancy_changes_2(self):
        expected_output = {date(2016, 12, 1): 0,
                           date(2017, 1, 1): 10,
                           date(2017, 1, 3): 9,
                           date(2017, 1, 5): 8,
                           date(2017, 1, 6): 8}
        self.room.animalroomentry_set.create(number_of_animals=10, flock=self.flock, date='2017-01-01')
        self.room.animalroomexit_set.create(number_of_animals=1, flock=self.flock, date='2017-01-03')
        self.room.animalroomexit_set.create(number_of_animals=1, flock=self.flock, date='2017-01-05')
        changes = self.room.get_occupancy_transitions(date(2016, 12, 1), '2017-01-06')
        self.assertEqual(5, len(changes))
        self.assertEqual(expected_output, changes)

    def test_animal_days_count(self):
        self.room.animalroomentry_set.create(number_of_animals=10, flock=self.flock, date='2017-01-01')
        animal_days = self.room.get_animal_days_for_period(date(2016, 12, 1), date(2017, 1, 3))
        self.assertEqual(20, animal_days)
        self.room.animalroomexit_set.create(number_of_animals=1, flock=self.flock, date='2017-01-03')
        animal_days = self.room.get_animal_days_for_period(date(2017, 1, 3), date(2017, 1, 5))
        self.assertEqual(18, animal_days)
        self.room.animalroomexit_set.create(number_of_animals=1, flock=self.flock, date='2017-01-05')
        animal_days = self.room.get_animal_days_for_period(date(2017, 1, 5), date(2017, 1, 7))
        self.assertEqual(16, animal_days)
        animal_days = self.room.get_animal_days_for_period(date(2016, 12, 1), date(2017, 1, 7))
        self.assertEqual(54, animal_days)

    def test_feed_type_on_change(self):
        self.room.roomfeedingchange_set.create(feed_type=self.feed_type, date='2017-01-01')
        self.assertEqual(self.feed_type, self.room.get_feeding_type_at('2017-01-01'))

    def test_feed_type_before_change(self):
        self.room.roomfeedingchange_set.create(feed_type=self.feed_type, date='2017-01-01')
        self.assertIsNone(self.room.get_feeding_type_at('2016-12-31'))

    def test_feed_type_after_change(self):
        self.room.roomfeedingchange_set.create(feed_type=self.feed_type, date='2017-01-01')
        self.assertEqual(self.feed_type, self.room.get_feeding_type_at('2017-01-02'))

    def test_feed_type_two_types(self):
        self.room.roomfeedingchange_set.create(feed_type=self.feed_type, date='2017-01-01')
        self.room.roomfeedingchange_set.create(feed_type=self.feed_type2, date='2017-01-31')
        self.assertEqual(self.feed_type, self.room.get_feeding_type_at('2017-01-02'))
        self.assertEqual(self.feed_type2, self.room.get_feeding_type_at('2017-02-01'))

    def test_get_feeding_periods(self):
        expected_periods1 = [[date(2017, 1, 1), date(2017, 2, 1)],
                             [date(2017, 3, 1), date(2017, 4, 1)]]

        expected_periods2 = [[date(2017, 2, 1), date(2017, 3, 1)],
                             [date(2017, 4, 1), date(2017, 4, 30)]]

        self.room.roomfeedingchange_set.create(feed_type=self.feed_type, date='2017-01-01')
        self.room.roomfeedingchange_set.create(feed_type=self.feed_type2, date='2017-02-01')
        self.room.roomfeedingchange_set.create(feed_type=self.feed_type, date='2017-03-01')
        self.room.roomfeedingchange_set.create(feed_type=self.feed_type2, date='2017-04-01')

        self.assertEqual(expected_periods1, self.room.get_feeding_periods('2017-01-01', '2017-04-30', self.feed_type))
        self.assertEqual(expected_periods2, self.room.get_feeding_periods('2017-01-01', '2017-04-30', self.feed_type2))

    def test_animal_days_for_feeding_period(self):
        self.room.animalroomentry_set.create(number_of_animals=10, flock=self.flock, date='2017-01-01')
        self.room.roomfeedingchange_set.create(feed_type=self.feed_type, date='2017-01-01')
        self.assertEqual(90, self.room.get_animal_days_for_feeding_period('2017-01-01', '2017-01-10', self.feed_type))
