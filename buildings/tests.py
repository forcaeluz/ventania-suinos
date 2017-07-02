from django.test import TestCase
from datetime import date

from .models import Flock, Room, Building
# Create your tests here.


class RoomTestCase(TestCase):

    def setUp(self):
        self.flock = Flock(entry_date='2017-01-01', entry_weight=220, number_of_animals=10)
        self.flock.save()
        self.building = Building(name='TheBigBuilding')
        self.building.save()
        self.room = Room(name='Room1', capacity=10, group=self.building)
        self.room.save()

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

