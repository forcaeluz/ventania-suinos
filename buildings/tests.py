from django.test import TestCase
from datetime import date

from .models import Flock, Room, RoomGroup, Building, FeedType, SiloFeedEntry, FeedEntry
# Create your tests here.
from .views import BuildingDetailView


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


class BuildingFeedingTestCase(TestCase):
    def setUp(self):
        self.flock = Flock(entry_date='2017-01-01', entry_weight=600, number_of_animals=30)
        self.flock.save()
        self.feed_type1 = FeedType(name='FeedType1', start_feeding_age=0, stop_feeding_age=10)
        self.feed_type1.save()
        self.feed_type2 = FeedType(name='FeedType2', start_feeding_age=11, stop_feeding_age=50)
        self.feed_type2.save()
        self.building = Building(name='TheBigBuilding')
        self.building.save()
        self.room_group = RoomGroup(group=self.building, name='Group1')
        self.room_group.save()
        self.room1 = Room(group=self.building, name='Room 1', capacity=10)
        self.room1.save()
        self.room2 = Room(group=self.building, name='Room 2', capacity=10)
        self.room2.save()
        self.room3 = Room(group=self.room_group, name='Room 3', capacity=10)
        self.room3.save()
        self.room4 = Room(group=self.room_group, name='Room 4', capacity=10)
        self.room4.save()

        self.silo1 = self.building.silo_set.create(capacity=10000, feed_type=self.feed_type1)
        self.silo1.save()
        self.silo2 = self.building.silo_set.create(capacity=20000, feed_type=self.feed_type2)

        self.setUpFeedingInfo()

        self.room1.animalroomentry_set.create(number_of_animals=10, date='2017-01-01', flock=self.flock)
        self.room2.animalroomentry_set.create(number_of_animals=10, date='2017-01-01', flock=self.flock)
        self.room3.animalroomentry_set.create(number_of_animals=10, date='2017-01-01', flock=self.flock)

    def setUpFeedingInfo(self):
        self.feed1_entry1 = FeedEntry(date='2017-01-01', weight=10000, feed_type=self.feed_type1)
        self.feed1_entry1.save()
        self.feed1_entry2 = FeedEntry(date='2017-01-15', weight=10000, feed_type=self.feed_type1)
        self.feed1_entry2.save()
        self.feed2_entry1 = FeedEntry(date='2017-01-01', weight=20000, feed_type=self.feed_type2)
        self.feed2_entry1.save()
        self.silo1_feed_entries = []
        self.silo2_feed_entries = []
        self.silo1_feed_entries.append(SiloFeedEntry(silo=self.silo1, feed_entry=self.feed1_entry1))
        self.silo1_feed_entries.append(SiloFeedEntry(silo=self.silo1, feed_entry=self.feed1_entry2))
        self.silo2_feed_entries.append(SiloFeedEntry(silo=self.silo2, feed_entry=self.feed2_entry1))
        for entry in self.silo1_feed_entries:
            entry.save()

        for entry in self.silo2_feed_entries:
            entry.save()

        self.room1.roomfeedingchange_set.create(feed_type=self.feed_type1, date='2017-01-01')
        self.room2.roomfeedingchange_set.create(feed_type=self.feed_type1, date='2017-01-01')
        self.room3.roomfeedingchange_set.create(feed_type=self.feed_type1, date='2017-01-01')

    def test_feed_capacity(self):
        self.assertEqual(10000, self.building.feed_capacity(self.feed_type1))
        self.assertEqual(20000, self.building.feed_capacity(self.feed_type2))

    def test_get_feed_entries(self):
        self.assertEqual(self.silo1_feed_entries, self.building.get_feed_entries('2017-01-01',
                                                                                 '2017-01-31',
                                                                                 self.feed_type1))
        self.assertEqual(self.silo2_feed_entries, self.building.get_feed_entries('2017-01-01',
                                                                                 '2017-01-31',
                                                                                 self.feed_type2))

    def test_feed_consumption(self):
        self.assertEqual(300, self.building.animal_days_for_feed_type('2017-01-01', '2017-01-11', self.feed_type1))
        self.assertEqual(0, self.building.animal_days_for_feed_type('2017-01-01', '2017-01-11', self.feed_type2))

    def test_feed_consumption_single_day(self):
        self.assertEqual(30, self.building.animal_days_for_feed_type('2017-01-05', '2017-01-06', self.feed_type1))
        self.assertEqual(0, self.building.animal_days_for_feed_type('2017-01-05', '2017-01-06', self.feed_type2))

    def test_last_feed_entries(self):
        actual = self.building.get_last_feed_entries('2017-01-17', self.feed_type1)
        expected = self.silo1_feed_entries[1]
        self.assertEqual(expected, actual)

    def test_feed_estimation(self):
        actual = self.building.get_estimated_remaining_feed('2017-01-21', self.feed_type1)
        expected = 5000
        self.assertEqual(expected, actual)
        actual = self.building.get_estimated_remaining_feed('2017-01-21', self.feed_type2)
        expected = 20000
        self.assertEqual(expected, actual)

    def test_feed_etimation_without_consumption(self):
        actual = self.building.get_estimated_remaining_feed('2017-01-21', self.feed_type2)
        expected = 20000
        self.assertEqual(expected, actual)

    def test_feed_end_date_estimation(self):
        actual = self.building.get_estimated_feed_end_date('2017-01-21', self.feed_type1)
        expected = date(2017, 1, 28)
        self.assertEqual(expected, actual)

    def test_feed_end_date_estimation_without_consumption(self):
        actual = self.building.get_estimated_feed_end_date('2017-01-21', self.feed_type2)
        self.assertIsNone(actual)

    def test_feed_estimation_with_remains(self):
        feed1_entry3 = FeedEntry(date='2017-01-21', weight=5000, feed_type=self.feed_type1)
        feed1_entry3.save()
        silo_entry = SiloFeedEntry(feed_entry=feed1_entry3,
                                   remaining=self.building.get_estimated_remaining_feed('2017-01-20', self.feed_type1),
                                   silo=self.silo1)
        silo_entry.save()
        actual = self.building.get_estimated_remaining_feed('2017-01-21', self.feed_type1)
        self.assertEqual(10000, actual)

    def test_feed_date_estimation_with_remains(self):
        feed1_entry3 = FeedEntry(date='2017-01-21', weight=5000, feed_type=self.feed_type1)
        feed1_entry3.save()
        silo_entry = SiloFeedEntry(feed_entry=feed1_entry3,
                                   remaining=self.building.get_estimated_remaining_feed('2017-01-20', self.feed_type1),
                                   silo=self.silo1)
        silo_entry.save()
        # Here the rules are a bit fuzzy, and an exact expectation does not make a lot of sense
        # either.
        self.assertEqual(date(2017, 2, 4), self.building.get_estimated_feed_end_date('2017-01-22', self.feed_type1))

class BuildingLayoutInformation(TestCase):

    def setUp(self):
        self.flock = Flock(entry_date='2017-01-01', entry_weight=600, number_of_animals=30)
        self.flock.save()
        self.feed_type1 = FeedType(name='FeedType1', start_feeding_age=0, stop_feeding_age=10)
        self.feed_type1.save()
        self.feed_type2 = FeedType(name='FeedType2', start_feeding_age=11, stop_feeding_age=50)
        self.feed_type2.save()
        self.building = Building(name='TheBigBuilding')
        self.building.save()
        self.room_group = RoomGroup(group=self.building, name='Group1')
        self.room_group.save()
        self.room1 = Room(group=self.building, name='Room 1', capacity=10)
        self.room1.save()
        self.room2 = Room(group=self.building, name='Room 2', capacity=10)
        self.room2.save()
        self.room3 = Room(group=self.room_group, name='Room 3', capacity=10)
        self.room3.save()
        self.silo1 = self.building.silo_set.create(capacity=10000, feed_type=self.feed_type1)
        self.silo1.save()
        self.silo2 = self.building.silo_set.create(capacity=20000, feed_type=self.feed_type2)
        self.room1.animalroomentry_set.create(number_of_animals=10, date='2017-01-01', flock=self.flock)

    def test_room_count(self):
        self.assertEqual(3, self.building.number_of_rooms)

    def test_capacity(self):
        self.assertEqual(30, self.building.animal_capacity)

    def test_name(self):
        self.assertEqual('TheBigBuilding', self.building.name)

    def test_occupancy(self):
        self.assertEqual(10, self.building.occupancy)


class BuildingDetailViewTest(TestCase):
    def setUp(self):
        self.flock = Flock(entry_date='2017-01-01', entry_weight=600, number_of_animals=30)
        self.flock.save()
        self.feed_type1 = FeedType(name='FeedType1', start_feeding_age=0, stop_feeding_age=10)
        self.feed_type1.save()
        self.feed_type2 = FeedType(name='FeedType2', start_feeding_age=11, stop_feeding_age=50)
        self.feed_type2.save()
        self.building = Building(name='TheBigBuilding')
        self.building.save()
        self.room_group = RoomGroup(group=self.building, name='Group1')
        self.room_group.save()
        self.room1 = Room(group=self.building, name='Room 1', capacity=10)
        self.room1.save()
        self.room2 = Room(group=self.building, name='Room 2', capacity=10)
        self.room2.save()
        self.room3 = Room(group=self.room_group, name='Room 3', capacity=10)
        self.room3.save()
        self.silo1 = self.building.silo_set.create(capacity=10000, feed_type=self.feed_type1)
        self.silo1.save()
        self.silo2 = self.building.silo_set.create(capacity=20000, feed_type=self.feed_type2)
        self.setUpFeedingInfo()
        self.room1.animalroomentry_set.create(number_of_animals=10, date='2017-01-01', flock=self.flock)
        self.room2.animalroomentry_set.create(number_of_animals=10, date='2017-01-01', flock=self.flock)
        self.room3.animalroomentry_set.create(number_of_animals=10, date='2017-01-01', flock=self.flock)

    def setUpFeedingInfo(self):
        self.feed1_entry1 = FeedEntry(date='2017-01-01', weight=10000, feed_type=self.feed_type1)
        self.feed1_entry1.save()
        self.feed1_entry2 = FeedEntry(date='2017-01-15', weight=10000, feed_type=self.feed_type1)
        self.feed1_entry2.save()
        self.feed2_entry1 = FeedEntry(date='2017-01-01', weight=20000, feed_type=self.feed_type2)
        self.feed2_entry1.save()
        self.silo1_feed_entries = []
        self.silo2_feed_entries = []
        self.silo1_feed_entries.append(SiloFeedEntry(silo=self.silo1, feed_entry=self.feed1_entry1))
        self.silo1_feed_entries.append(SiloFeedEntry(silo=self.silo1, feed_entry=self.feed1_entry2))
        self.silo2_feed_entries.append(SiloFeedEntry(silo=self.silo2, feed_entry=self.feed2_entry1))
        for entry in self.silo1_feed_entries:
            entry.save()

        for entry in self.silo2_feed_entries:
            entry.save()

        self.room1.roomfeedingchange_set.create(feed_type=self.feed_type1, date='2017-01-01')
        self.room2.roomfeedingchange_set.create(feed_type=self.feed_type1, date='2017-01-01')
        self.room3.roomfeedingchange_set.create(feed_type=self.feed_type1, date='2017-01-01')

    def test_get_context_data(self):
        view = BuildingDetailView(kwargs={'building_id': 1})
        context_data = view.get_context_data()
        self.assertEqual(context_data['building'], self.building)
