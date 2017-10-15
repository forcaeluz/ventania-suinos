from datetime import date
from unittest import mock
from django.test import TestCase
from django.forms import formset_factory
from django.shortcuts import reverse
from django.contrib.auth.models import User
from buildings.models import Building, Room, SiloFeedEntry
from flocks.models import Flock, AnimalSeparation
from feeding.models import FeedType, FeedEntry
from medications.models import Medication, Treatment, MedicationApplication

from .forms import AnimalDeathForm, AnimalSeparationForm, AnimalSeparationDistinctionForm, GroupExitForm
from .forms import AnimalExitRoomFormset, AnimalExitRoomForm, FeedEntryForm, AnimalEntryForm
from .models import AnimalEntry, NewTreatment


class FarmTestClass(TestCase):
    def setUp(self):
        super().setUp()
        User.objects.create_user(username='NormalUser', email='none@noprovider.test', password='Password')
        building = Building(name='b1')
        self.building = building
        self.building.save()
        self.normal_room1 = Room(name='Room1', is_separation=False, capacity=13, group=building)
        self.normal_room1.save()
        self.normal_room2 = Room(name='Room2', is_separation=False, capacity=13, group=building)
        self.normal_room2.save()
        self.separation_room = Room(name='SeparationRoom', is_separation=True, capacity=4, group=building)
        self.separation_room.save()
        self.flock1 = Flock(entry_date='2016-12-01', number_of_animals=13, entry_weight=270)
        self.flock1.save()
        self.flock2 = Flock(entry_date='2017-01-01', number_of_animals=13, entry_weight=270)
        self.flock2.save()
        self.separation1 = AnimalSeparation(date='2016-12-15', flock=self.flock1, reason='Separation1')
        self.separation1.save()
        self.separation2 = AnimalSeparation(date='2016-01-15', flock=self.flock2, reason='Separation2')
        self.separation2.save()
        animal_entry = self.normal_room1.animalroomentry_set.create(date='2016-12-01',
                                                                    number_of_animals=13,
                                                                    flock=self.flock1)
        animal_entry.save()
        animal_entry = self.normal_room2.animalroomentry_set.create(date='2017-01-01',
                                                                    number_of_animals=13,
                                                                    flock=self.flock2)
        animal_entry.save()
        animal_exit = self.normal_room1.animalroomexit_set.create(date='2016-12-15',
                                                                  number_of_animals=1,
                                                                  flock=self.flock1)
        animal_exit.save()
        animal_exit = self.normal_room2.animalroomexit_set.create(date='2017-01-15',
                                                                  number_of_animals=1,
                                                                  flock=self.flock2)
        animal_exit.save()
        animal_entry = self.separation_room.animalroomentry_set.create(date='2016-12-15',
                                                                       number_of_animals=1,
                                                                       flock=self.flock1)
        animal_entry.save()
        animal_entry = self.separation_room.animalroomentry_set.create(date='2017-01-15',
                                                                       number_of_animals=1,
                                                                       flock=self.flock2)
        animal_entry.save()

    def setUpEmptyBuilding(self):
        building = Building(name='EmptyBuilding')
        self.empty_building = building
        self.empty_building.save()
        normal_room1 = Room(name='Room1', is_separation=False, capacity=13, group=building)
        normal_room1.save()
        normal_room2 = Room(name='Room2', is_separation=False, capacity=13, group=building)
        normal_room2.save()
        separation_room = Room(name='SeparationRoom', is_separation=True, capacity=4, group=building)
        separation_room.save()


class CreateAnimalEntryFormTest(FarmTestClass):

    def test_empty_constructor(self):
        form = AnimalEntryForm()

    def test_with_valid_data(self):
        self.setUpEmptyBuilding()
        data = {'date': '2017-01-02',
                'weight': '220',
                'number_of_animals': '10',
                'rooms': [obj.id for obj in self.empty_building.room_set.filter(is_separation=False)]}
        form = AnimalEntryForm(data=data)
        self.assertTrue(form.is_valid())

    def test_with_invalid_data(self):
        self.setUpEmptyBuilding()
        data = {'date': '2017-01-02',
                'weight': '220',
                'number_of_animals': '10',
                'rooms': [obj.id for obj in self.building.room_set.filter(is_separation=False)]}
        form = AnimalEntryForm(data=data)
        self.assertFalse(form.is_valid())
        error_list = form.non_field_errors()
        self.assertTrue('not empty' in error_list[0])

    def test_update_with_valid_data(self):
        flock = self.flock1
        data = {'date': '2016-12-01',
                'weight': '220',
                'number_of_animals': '10',
                'rooms': [self.normal_room1.id]}
        form = AnimalEntryForm(flock=flock, data=data)
        self.assertTrue(form.is_valid())

    def test_update_with_invalid_data(self):
        flock = self.flock2
        data = {'date': '2017-01-01',
                'weight': '220',
                'number_of_animals': '10',
                'rooms': [self.normal_room1.id]}
        form = AnimalEntryForm(flock=flock, data=data)
        self.assertFalse(form.is_valid())
        error_list = form.non_field_errors()
        self.assertTrue('not empty' in error_list[0])

    def test__update_with_valid_data2(self):
        self.setUpEmptyBuilding()
        flock = self.flock1
        data = {'date': '2017-01-02',
                'weight': '220',
                'number_of_animals': '10',
                'rooms': [self.empty_building.room_set.first()]}
        form = AnimalEntryForm(flock=flock, data=data)
        self.assertTrue(form.is_valid())


class AnimalEntryTest(FarmTestClass):
    def setUp(self):
        super().setUp()
        self.setUpEmptyBuilding()

    def test_constructor(self):
        entry = AnimalEntry()
        self.assertIsNone(entry.flock)
        self.assertEquals(0, len(entry.room_entries))

    def test_set_flock(self):
        entry = AnimalEntry()
        entry.set_flock(instance=self.flock1)
        self.assertEquals(1, len(entry.room_entries))
        self.assertEquals(self.normal_room1.animalroomentry_set.first(), entry.room_entries[0])

    def test_update_flock(self):
        entry = AnimalEntry()
        entry.set_flock(instance=self.flock1)
        data = {'weight': 300,
                'number_of_animals': 13,
                'date': '2016-12-02'}
        entry.update_flock(data=data)
        self.assertTrue(entry.is_valid())
        entry.save()
        self.assertEquals(300, self.flock1.entry_weight)
        self.assertEquals(13, self.flock1.number_of_animals)
        self.assertEquals(date(2016, 12, 2), self.flock1.entry_date)
        room_entry = self.flock1.animalroomentry_set.filter(room=self.normal_room1).first()
        self.assertEquals(date(2016, 12, 2), room_entry.date)

    def test_remove_and_add_room_entry(self):
        entry = AnimalEntry()
        entry.set_flock(instance=self.flock1)
        data = {'weight': 300,
                'number_of_animals': 13,
                'date': '2016-12-02'}
        entry.update_flock(data=data)
        room_data = [{'room': self.empty_building.room_set.first(),
                      'number_of_animals': 13
                      }]
        entry.update_room_entries(room_data)
        self.assertEquals(1, len(entry.room_entries))
        self.assertEquals(self.empty_building.room_set.first(), entry.room_entries[0].room)
        self.assertTrue(entry.is_valid())
        entry.save()
        self.assertEquals(0, self.normal_room1.animalroomentry_set.count())

    def test_update_room_info(self):
        entry = AnimalEntry()
        entry.set_flock(instance=self.flock1)
        data = {'weight': 300,
                'number_of_animals': 10,
                'date': '2016-12-02'}
        entry.update_flock(data=data)
        room_data = [{'room': self.normal_room1,
                      'number_of_animals': 10
                      }]
        entry.update_room_entries(room_data)
        self.assertEquals(1, len(entry.room_entries))
        self.assertEquals(self.normal_room1, entry.room_entries[0].room)
        self.assertTrue(entry.is_valid())
        entry.save()
        room_entry = self.normal_room1.animalroomentry_set.first()
        self.assertEquals(10, room_entry.number_of_animals)

    def test_create_flock(self):
        entry = AnimalEntry()
        data = {'weight': 300,
                'number_of_animals': 13,
                'date': '2017-03-01'}
        room_data = [{'room': self.empty_building.room_set.first(),
                      'number_of_animals': 13
                      }]

        entry.set_flock(data=data)
        entry.update_room_entries(room_data)
        self.assertTrue(entry.is_valid())
        entry.save()
        self.assertEquals(3, Flock.objects.count())

    def test_delete_flock(self):
        entry = AnimalEntry()
        entry.set_flock(instance=self.flock1)
        entry.delete()
        self.assertEquals(1, Flock.objects.count())
        self.assertEquals(0, self.normal_room1.animalroomentry_set.count())

    def test_invalid_data(self):
        entry = AnimalEntry()
        data = {'weight': 300,
                'number_of_animals': 13,
                'date': '2017-03-01'}
        room_data = [{'room': self.empty_building.room_set.first(),
                      'number_of_animals': 14
                      }]

        entry.set_flock(data=data)
        entry.update_room_entries(room_data)
        self.assertFalse(entry.is_valid())

    def test_set_flock_invalid(self):
        entry = AnimalEntry()
        with self.assertRaises(ValueError):
            entry.set_flock(flock=self.flock1)

    def test_set_room_info_before_flock(self):
        entry = AnimalEntry()
        room_data = [{'room': self.empty_building.room_set.first(),
                      'number_of_animals': 14
                      }]
        with self.assertRaises(AssertionError):
            entry.update_room_entries(room_data)


class NewAnimalEntryWizardTest(FarmTestClass):
    def setUp(self):
        super().setUp()
        super().setUpEmptyBuilding()
        response = self.client.login(username='NormalUser', password='Password')
        self.assertTrue(response)

    def test_get_view(self):
        response = self.client.get(reverse('farm:new_animal_entry'))
        self.assertEquals(200, response.status_code)
        self.assertEquals(response.context['wizard']['steps'].current, 'flock_information')

    def test_post_invalid_first_step(self):
        data = {'register_new_animal_entry-current_step': 'flock_information',
                'flock_information-date': '2017-01-01',
                'flock_information-weight': '0',
                'flock_information-number_of_animals': '10',
                'flock_information-rooms': [self.empty_building.room_set.first().id]}

        response = self.client.post(reverse('farm:new_animal_entry'), data)
        self.assertEquals(200, response.status_code)
        self.assertEquals(response.context['wizard']['steps'].current, 'flock_information')

    def test_post_first_step(self):
        data = {'register_new_animal_entry-current_step': 'flock_information',
                'flock_information-date': '2017-01-01',
                'flock_information-weight': '200',
                'flock_information-number_of_animals': '10',
                'flock_information-rooms': [self.empty_building.room_set.first().id]}

        response = self.client.post(reverse('farm:new_animal_entry'), data)
        self.assertEquals(200, response.status_code)
        self.assertEquals(response.context['wizard']['steps'].current, 'building_information')

    def test_post_second_step(self):
        data = {'register_new_animal_entry-current_step': 'flock_information',
                'flock_information-date': '2017-01-01',
                'flock_information-weight': '200',
                'flock_information-number_of_animals': '10',
                'flock_information-rooms': [self.empty_building.room_set.first().id]}
        self.client.post(reverse('farm:new_animal_entry'), data)

        data = {'register_new_animal_entry-current_step': 'building_information',
                'building_information-TOTAL_FORMS': 1,
                'building_information-INITIAL_FORMS': 1,
                'building_information-MIN_NUM_FORMS': 0,
                'building_information-MAX_NUM_FORMS': 1000,
                'building_information-0-room': self.empty_building.room_set.first().id,
                'building_information-0-number_of_animals': '10',
                }
        response = self.client.post(reverse('farm:new_animal_entry'), data)
        self.assertEquals(302, response.status_code)
        # New flock should have been created now.
        self.assertEquals(3, Flock.objects.count())


class EditAnimalEntryWizardTest(FarmTestClass):
    def setUp(self):
        super().setUp()
        super().setUpEmptyBuilding()
        response = self.client.login(username='NormalUser', password='Password')
        self.assertTrue(response)

    def test_get_view(self):
        response = self.client.get(reverse('farm:edit_animal_entry', kwargs={'flock_id': 1}))
        self.assertEquals(200, response.status_code)
        self.assertEquals(response.context['wizard']['steps'].current, 'flock_information')
        form = response.context['wizard']['form']
        self.assertEquals(self.flock1.entry_weight, form.initial['weight'])
        self.assertEquals([self.normal_room1], form.initial['rooms'])
        self.assertEquals(date(2016, 12, 1), form.initial['date'])

    def test_post_step1(self):
        response = self.client.get(reverse('farm:edit_animal_entry', kwargs={'flock_id': 1}))
        form = response.context['wizard']['form']
        data = {'edit_animal_entry-current_step': 'flock_information',
                'flock_information-date': '2016-12-01',
                'flock_information-weight': '250',
                'flock_information-number_of_animals': '10',
                'flock_information-rooms': [self.normal_room1.id]}

        response = self.client.post(reverse('farm:edit_animal_entry', kwargs={'flock_id': 1}), data)
        self.assertEquals(200, response.status_code)
        self.assertEquals(response.context['wizard']['steps'].current, 'building_information')

    def test_post_step2(self):
        response = self.client.get(reverse('farm:edit_animal_entry', kwargs={'flock_id': 1}))
        data = {'edit_animal_entry-current_step': 'flock_information',
                'flock_information-date': '2016-12-01',
                'flock_information-weight': '250',
                'flock_information-number_of_animals': '10',
                'flock_information-rooms': [self.empty_building.room_set.first().id]}

        response = self.client.post(reverse('farm:edit_animal_entry', kwargs={'flock_id': 1}), data)
        data = {'edit_animal_entry-current_step': 'building_information',
                'building_information-TOTAL_FORMS': 1,
                'building_information-INITIAL_FORMS': 1,
                'building_information-MIN_NUM_FORMS': 0,
                'building_information-MAX_NUM_FORMS': 1000,
                'building_information-0-room': self.empty_building.room_set.first().id,
                'building_information-0-number_of_animals': '10',
                }
        response = self.client.post(reverse('farm:edit_animal_entry', kwargs={'flock_id': 1}), data)
        self.assertEquals(302, response.status_code)
        self.assertEquals(0, self.normal_room1.animalroomentry_set.count())


class AnimalDeathFormTest(FarmTestClass):

    def test_death_from_normal_room(self):
        form_data = {'date': '2016-12-02',
                     'weight': '30',
                     'reason': 'Random',
                     'room': self.normal_room1.id}
        form = AnimalDeathForm(data=form_data)
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(11, self.normal_room1.occupancy)
        self.assertEqual(12, self.normal_room1.get_animals_for_flock(self.flock1, '2016-12-02'))
        self.assertEqual(12, self.flock1.number_of_living_animals)

    def test_death_from_empty_room(self):
        form_data = {'date': '2016-11-02',
                     'weight': '30',
                     'reason': 'Random',
                     'room': self.normal_room1.id}
        form = AnimalDeathForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_death_from_room_with_two_flocks(self):
        form_data = {'date': '2017-01-15',
                     'weight': '30',
                     'reason': 'Random',
                     'room': self.separation_room.id}

        form = AnimalDeathForm(data=form_data)
        form.set_flock(self.flock2)
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(1, self.separation_room.occupancy)
        self.assertEqual(1, self.separation_room.get_animals_for_flock(self.flock1, '2017-01-15'))
        self.assertEqual(12, self.flock2.number_of_living_animals)
        self.assertEqual(13, self.flock1.number_of_living_animals)

    def test_death_from_room_with_two_flocks_without_flock_information(self):
        form_data = {'date': '2017-01-15',
                     'weight': '30',
                     'reason': 'Random',
                     'room': self.separation_room.id}

        form = AnimalDeathForm(data=form_data)
        self.assertFalse(form.is_valid())


class AnimalSeparationFormTest(FarmTestClass):
    def test_separation_form(self):
        form_data = {'date': '2017-01-16',
                     'reason': 'Random',
                     'src_room': self.normal_room1.id,
                     'dst_room': self.separation_room.id}
        form = AnimalSeparationForm(form_data)
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(3, self.separation_room.occupancy)
        self.assertEqual(11, self.normal_room1.occupancy)
        self.assertEqual(2, self.flock1.animalseparation_set.count())


class AnimalSeparationViewTest(FarmTestClass):
    def setUp(self):
        super().setUp()
        super().setUpEmptyBuilding()
        response = self.client.login(username='NormalUser', password='Password')
        self.assertTrue(response)

    def test_get_view(self):
        response = self.client.get(reverse('farm:new_animal_separation'))
        self.assertEquals(200, response.status_code)
        form = response.context['form']
        self.assertTrue(isinstance(form, AnimalSeparationForm))

    def test_post_view_valid(self):
        self.client.get(reverse('farm:new_animal_separation'))
        form_data = {'date': '2017-01-16',
                     'reason': 'Random',
                     'src_room': self.normal_room1.id,
                     'dst_room': self.separation_room.id}
        response = self.client.post(reverse('farm:new_animal_separation'), form_data)
        self.assertEquals(302, response.status_code)
        self.assertEqual(3, self.separation_room.occupancy)
        self.assertEqual(11, self.normal_room1.occupancy)
        self.assertEqual(2, self.flock1.animalseparation_set.count())


class AnimalDistinctionFormTest(FarmTestClass):
    def create_room_exit_formset_data(self):
        data = {'form-TOTAL_FORMS': '3',
                'form-INITIAL_FORMS': '3',
                'form-MAX_NUM_FORMS': '',
                'form-0-room': self.normal_room1.id,
                'form-0-number_of_animals': 0,
                'form-1-room': self.normal_room2.id,
                'form-1-number_of_animals': 0,
                'form-2-room': self.separation_room.id,
                'form-2-number_of_animals': 1,
                }
        return data

    def test_death_distinction(self):
        form_data = {'date': '2017-01-15',
                     'weight': '30',
                     'reason': 'Random',
                     'room': self.separation_room.id}

        form1 = AnimalDeathForm(data=form_data)
        form_data = {'separation': self.separation1.id}
        form2 = AnimalSeparationDistinctionForm(form_data)
        self.assertTrue(form2.is_valid())
        form1.set_flock(form2.cleaned_data.get('separation').flock)
        self.assertTrue(form1.is_valid())
        form1.save()
        form2.set_death(form1.death)
        form2.save()
        self.separation1.refresh_from_db()
        self.assertFalse(self.separation1.active)

    def test_exit_distinction(self):
        form_data = {'date': '2017-01-15',
                     'number_of_animals': '1',
                     'weight': 30,
                     'rooms': [1]
                     }

        form1 = GroupExitForm(data=form_data)
        self.assertTrue(form1.is_valid())
        form_data = self.create_room_exit_formset_data()
        FormSet = formset_factory(formset=AnimalExitRoomFormset, form=AnimalExitRoomForm)
        form2 = FormSet(form_data, number_of_animals=1)
        self.assertTrue(form2.is_valid())
        form_data = {'separation': self.separation1.id}
        form3 = AnimalSeparationDistinctionForm(form_data)
        self.assertTrue(form3.is_valid())
#         TODO: Implement further checks.


class GroupExitFormTest(FarmTestClass):

    def test_form(self):
        form_data = {'date': '2017-03-15',
                     'number_of_animals': '13',
                     'weight': 1330,
                     'rooms': [1]
                     }

        form1 = GroupExitForm(data=form_data)
        self.assertTrue(form1.is_valid())


class AnimalExitRoomFormsetTest(FarmTestClass):

    def test_constructor(self):
        FormSet = formset_factory(formset=AnimalExitRoomFormset, form=AnimalExitRoomForm)
        data = {'form-TOTAL_FORMS': '3',
                'form-INITIAL_FORMS': '3',
                'form-MAX_NUM_FORMS': '',
                'form-0-room': self.normal_room1.id,
                'form-0-number_of_animals': 12,
                'form-1-room': self.normal_room2.id,
                'form-1-number_of_animals': 0,
                'form-2-room': self.separation_room.id,
                'form-2-number_of_animals': 0,
                }

        formset = FormSet(data, number_of_animals=12)
        self.assertTrue(formset.is_valid())

    def test_get_exited_rooms(self):
        FormSet = formset_factory(formset=AnimalExitRoomFormset, form=AnimalExitRoomForm)
        data = {'form-TOTAL_FORMS': '3',
                'form-INITIAL_FORMS': '3',
                'form-MAX_NUM_FORMS': '',
                'form-0-room': self.normal_room1.id,
                'form-0-number_of_animals': 9,
                'form-1-room': self.normal_room2.id,
                'form-1-number_of_animals': 3,
                'form-2-room': self.separation_room.id,
                'form-2-number_of_animals': 0,
                }

        formset = FormSet(data, number_of_animals=12)
        self.assertTrue(formset.is_valid())
        rooms = formset.get_exited_rooms()
        self.assertTrue(rooms[0], self.normal_room1)
        self.assertTrue(rooms[1], self.normal_room2)

    def test_invalid_sub_form(self):
        FormSet = formset_factory(formset=AnimalExitRoomFormset, form=AnimalExitRoomForm)
        data = {'form-TOTAL_FORMS': '3',
                'form-INITIAL_FORMS': '3',
                'form-MAX_NUM_FORMS': '',
                'form-0-room': self.normal_room1.id,
                'form-0-number_of_animals': 13,
                'form-1-room': self.normal_room2.id,
                'form-1-number_of_animals': 0,
                'form-2-room': self.separation_room.id,
                'form-2-number_of_animals': 0,
                }

        formset = FormSet(data, number_of_animals=12)
        self.assertFalse(formset.is_valid())
        self.assertEqual(0, len(formset.non_form_errors()))
        self.assertEqual(1, len(formset.forms[0].errors))
        self.assertEqual(0, len(formset.forms[1].errors))
        self.assertEqual(0, len(formset.forms[2].errors))

    def test_not_matching_animal_count(self):
        FormSet = formset_factory(formset=AnimalExitRoomFormset, form=AnimalExitRoomForm)
        data = {'form-TOTAL_FORMS': '3',
                'form-INITIAL_FORMS': '3',
                'form-MAX_NUM_FORMS': '',
                'form-0-room': self.normal_room1.id,
                'form-0-number_of_animals': 12,
                'form-1-room': self.normal_room2.id,
                'form-1-number_of_animals': 0,
                'form-2-room': self.separation_room.id,
                'form-2-number_of_animals': 0,
                }

        formset = FormSet(data, number_of_animals=13)
        self.assertFalse(formset.is_valid())
        self.assertEqual(1, len(formset.non_form_errors()))
        self.assertEqual(0, len(formset.forms[0].errors))
        self.assertEqual(0, len(formset.forms[1].errors))
        self.assertEqual(0, len(formset.forms[2].errors))


class TestFeedEntryForm(FarmTestClass):

    def setUp(self):
        super().setUp()
        self.feed_type1 = FeedType(name='Type1', start_feeding_age=0, stop_feeding_age=10)
        self.feed_type1.save()
        self.feed_type2 = FeedType(name='Type2', start_feeding_age=0, stop_feeding_age=10)
        self.feed_type2.save()

        self.silo1 = self.building.silo_set.create(name='Silo1', feed_type=self.feed_type1, capacity=10000)
        self.silo2 = self.building.silo_set.create(name='Silo2', feed_type=self.feed_type2, capacity=10000)

    def test_feed_entry_form(self):
        form_data = {'date': '2017-01-15',
                     'weight': '10000',
                     'remaining': '0',
                     'silo': self.silo1.id,
                     'feed_type': self.feed_type1.id
                     }

        form = FeedEntryForm(data=form_data)
        self.assertTrue(form.is_valid())
        form.save()
        feed_entries = FeedEntry.objects.all()
        self.assertEqual(1, feed_entries.count())
        entry = feed_entries.first()
        self.assertEqual(date(2017, 1, 15), entry.date)
        self.assertEqual(10000, entry.weight)
        silo_entries = SiloFeedEntry.objects.all()
        self.assertEqual(1, silo_entries.count())

    def test_feed_entry_invalid_type(self):
        form_data = {'date': '2017-01-15',
                     'weight': '10000',
                     'remaining': '0',
                     'silo': self.silo1.id,
                     'feed_type': self.feed_type2.id
                     }
        form = FeedEntryForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_feed_entry_over_capacity(self):
        form_data = {'date': '2017-01-15',
                     'weight': '9000',
                     'remaining': '2000',
                     'silo': self.silo1.id,
                     'feed_type': self.feed_type1.id
                     }
        form = FeedEntryForm(data=form_data)
        self.assertFalse(form.is_valid())


class TestNewTreatmentModel(FarmTestClass):

    def setUp(self):
        super().setUp()
        self.medication1 = Medication(name='Medication1', recommended_age_start=1, recommended_age_stop=100,
                                     dosage_per_kg=1, grace_period_days=10, instructions='DoSomething',
                                     quantity_unit='ml')
        self.medication2 = Medication(name='Medication2', recommended_age_start=1, recommended_age_stop=100,
                                     dosage_per_kg=0.1, grace_period_days=10, instructions='DoSomething',
                                     quantity_unit='ml')
        self.medication1.save()
        self.medication2.save()

    def test_object_creation(self):
        new_treatment = NewTreatment()

    def test_symptoms_step(self):
        data = {'date': '2017-02-01',
                'room': self.normal_room1,
                'symptoms': 'Sickness'}
        new_treatment = NewTreatment()
        new_treatment.process_symptom_form(data)

    def test_medication_suggestion(self):
        data = {'date': '2017-02-01',
                'room': self.normal_room1,
                'symptoms': 'Sickness'}
        new_treatment = NewTreatment()
        new_treatment.process_symptom_form(data)
        suggestions = new_treatment.suggest_medications()
        self.assertEquals(2, len(suggestions))
        self.assertTrue(self.medication1.id in suggestions)
        self.assertTrue(self.medication2.id in suggestions)

    def test_medication_step(self):
        data = {'date': '2017-02-01',
                'room': self.normal_room1,
                'symptoms': 'Sickness'}
        new_treatment = NewTreatment()
        new_treatment.process_symptom_form(data)
        data = {'medication': self.medication1,
                'override': None}
        new_treatment.process_medication_form(data)

    def test_medication_step_with_override(self):
        data = {'date': '2017-02-01',
                'room': self.normal_room1,
                'symptoms': 'Sickness'}
        new_treatment = NewTreatment()
        new_treatment.process_symptom_form(data)
        data = {'medication': None,
                'override': self.medication2}
        new_treatment.process_medication_form(data)

    def test_suggest_dosage_med2(self):
        data = {'date': '2017-02-01',
                'room': self.normal_room2,
                'symptoms': 'Sickness'}
        new_treatment = NewTreatment()
        new_treatment.process_symptom_form(data)
        data = {'medication': None,
                'override': self.medication2}
        new_treatment.process_medication_form(data)
        suggested_dosaged = new_treatment.suggest_dosage()
        self.assertAlmostEquals(4.712, suggested_dosaged, places=2)

    def test_suggest_dosage_med1(self):
        data = {'date': '2017-02-01',
                'room': self.normal_room2,
                'symptoms': 'Sickness'}
        new_treatment = NewTreatment()
        new_treatment.process_symptom_form(data)
        data = {'medication': self.medication1,
                'override': None}
        new_treatment.process_medication_form(data)
        suggested_dosaged = new_treatment.suggest_dosage()
        self.assertAlmostEquals(47.12, suggested_dosaged, places=2)

    def test_application_form(self):
        data = {'date': '2017-02-01',
                'room': self.normal_room2,
                'symptoms': 'Sickness'}
        new_treatment = NewTreatment()
        new_treatment.process_symptom_form(data)
        data = {'medication': self.medication1,
                'override': None}
        new_treatment.process_medication_form(data)

        data = {'dosage': 45.0,
                'confirm_application': True,
                'separate': False,
                'destination_room': None}
        new_treatment.process_dosage_and_separation_form(data)

    def test_save_with_application(self):
        data = {'date': '2017-02-01',
                'room': self.normal_room2,
                'symptoms': 'Sickness'}
        new_treatment = NewTreatment()
        new_treatment.process_symptom_form(data)
        data = {'medication': self.medication1,
                'override': None}
        new_treatment.process_medication_form(data)

        data = {'dosage': 45.0,
                'confirm_application': True,
                'separate': False,
                'destination_room': None}
        new_treatment.process_dosage_and_separation_form(data)
        new_treatment.save()
        self.assertEquals(1, Treatment.objects.count())
        self.assertEquals(1, MedicationApplication.objects.count())

    def test_save_without_application(self):
        data = {'date': '2017-02-01',
                'room': self.normal_room2,
                'symptoms': 'Sickness'}
        new_treatment = NewTreatment()
        new_treatment.process_symptom_form(data)
        data = {'medication': self.medication1,
                'override': None}
        new_treatment.process_medication_form(data)

        data = {'dosage': 45.0,
                'confirm_application': False,
                'separate': False,
                'destination_room': None}
        new_treatment.process_dosage_and_separation_form(data)
        new_treatment.save()
        self.assertEquals(1, Treatment.objects.count())
        self.assertEquals(0, MedicationApplication.objects.count())

    def test_save_without_application_with_separation(self):
        data = {'date': '2017-02-01',
                'room': self.normal_room2,
                'symptoms': 'Sickness'}
        new_treatment = NewTreatment()
        new_treatment.process_symptom_form(data)
        data = {'medication': self.medication1,
                'override': None}
        new_treatment.process_medication_form(data)

        data = {'dosage': 45.0,
                'confirm_application': False,
                'separate': True,
                'destination_room': self.separation_room}
        new_treatment.process_dosage_and_separation_form(data)
        new_treatment.save()
        self.assertEquals(1, Treatment.objects.count())
        self.assertEquals(1, AnimalSeparation.objects.filter(date='2017-02-01', reason='Treatment').count())
        self.assertEquals(3, self.separation_room.get_occupancy_at_date('2017-02-02'))


class TestNewTreatmentWizard(FarmTestClass):
    def setUp(self):
        super().setUp()
        self.medication1 = Medication(name='Medication1', recommended_age_start=1, recommended_age_stop=100,
                                     dosage_per_kg=1, grace_period_days=10, instructions='DoSomething',
                                     quantity_unit='ml')
        self.medication2 = Medication(name='Medication2', recommended_age_start=1, recommended_age_stop=100,
                                     dosage_per_kg=0.1, grace_period_days=10, instructions='DoSomething',
                                     quantity_unit='ml')
        self.medication1.save()
        self.medication2.save()

        self.mocked_model = mock.create_autospec(NewTreatment)
        self.mocked_model.suggest_medications.return_value = [self.medication1.id]
        patcher = mock.patch('farm.wizards.NewTreatment', autospec=True)
        class_mocker = patcher.start()
        class_mocker.return_value = self.mocked_model
        self.addCleanup(patcher.stop)
        response = self.client.login(username='NormalUser', password='Password')
        self.assertTrue(response)

    def test_get(self):
        response = self.client.get(reverse('farm:new_treatment'))
        self.assertEquals(200, response.status_code)
        self.assertTrue(self.mocked_model.reset.called)

    def test_post_first_form(self):
        data = {'start_new_treatment-current_step': 'room_symptoms_information',
                'room_symptoms_information-date': '2017-01-01',
                'room_symptoms_information-room': self.normal_room1.id,
                'room_symptoms_information-symptoms': 'Symptom'}

        response = self.client.post(reverse('farm:new_treatment'), data)
        self.assertEquals(200, response.status_code)
        self.assertTrue(self.mocked_model.process_symptom_form.called)
        self.assertTrue(self.mocked_model.suggest_medications.called)

    def test_post_second_form(self):
        data = {'start_new_treatment-current_step': 'room_symptoms_information',
                'room_symptoms_information-date': '2017-01-01',
                'room_symptoms_information-room': self.normal_room1.id,
                'room_symptoms_information-symptoms': 'Symptom'}

        self.client.post(reverse('farm:new_treatment'), data)
        data = {'start_new_treatment-current_step': 'medication_choice_information',
                'medication_choice_information-medication': '1',
                'medication_choice_information-override': ''}
        response = self.client.post(reverse('farm:new_treatment'), data)
        self.assertEquals(200, response.status_code)
        self.assertEquals('dosage_information', response.context_data['wizard']['steps'].current)
        self.assertEquals(2, self.mocked_model.process_symptom_form.call_count)
        self.assertEquals(2, self.mocked_model.suggest_medications.call_count)
        self.assertEquals(1, self.mocked_model.process_medication_form.call_count)
        self.assertEquals(1, self.mocked_model.suggest_dosage.call_count)

    def test_post_third_form(self):
        data = {'start_new_treatment-current_step': 'room_symptoms_information',
                'room_symptoms_information-date': '2017-01-01',
                'room_symptoms_information-room': self.normal_room1.id,
                'room_symptoms_information-symptoms': 'Symptom'}

        self.client.post(reverse('farm:new_treatment'), data)
        data = {'start_new_treatment-current_step': 'medication_choice_information',
                'medication_choice_information-medication': '1',
                'medication_choice_information-override': ''}
        self.client.post(reverse('farm:new_treatment'), data)
        data = {'start_new_treatment-current_step': 'dosage_information',
                'dosage_information-dosage': '10.0',
                'dosage_information-confirm_application': 'True',
                'dosage_information-separate': 'False',
                'dosage_information-separation_room': ''}
        response = self.client.post(reverse('farm:new_treatment'), data)
        self.assertEquals(200, response.status_code)
        self.assertEquals('overview', response.context_data['wizard']['steps'].current)
        self.assertEquals(3, self.mocked_model.process_symptom_form.call_count)
        self.assertEquals(3, self.mocked_model.suggest_medications.call_count)
        self.assertEquals(2, self.mocked_model.process_medication_form.call_count)
        self.assertEquals(2, self.mocked_model.suggest_dosage.call_count)
        self.assertEquals(1, self.mocked_model.process_dosage_and_separation_form.call_count)

    def test_post_submit_wizard(self):
        data = {'start_new_treatment-current_step': 'room_symptoms_information',
                'room_symptoms_information-date': '2017-01-01',
                'room_symptoms_information-room': self.normal_room1.id,
                'room_symptoms_information-symptoms': 'Symptom'}

        self.client.post(reverse('farm:new_treatment'), data)
        data = {'start_new_treatment-current_step': 'medication_choice_information',
                'medication_choice_information-medication': '1',
                'medication_choice_information-override': ''}
        self.client.post(reverse('farm:new_treatment'), data)
        data = {'start_new_treatment-current_step': 'dosage_information',
                'dosage_information-dosage': '10.0',
                'dosage_information-confirm_application': 'True',
                'dosage_information-separate': 'False',
                'dosage_information-separation_room': ''}
        self.client.post(reverse('farm:new_treatment'), data)
        data = {'start_new_treatment-current_step': 'overview'}

        self.mocked_model.reset_mock()
        response = self.client.post(reverse('farm:new_treatment'), data)
        self.assertEquals(302, response.status_code)
        self.assertEquals(1, self.mocked_model.process_symptom_form.call_count)
        self.assertEquals(1, self.mocked_model.process_medication_form.call_count)
        self.assertEquals(1, self.mocked_model.process_dosage_and_separation_form.call_count)
        self.assertEquals(1, self.mocked_model.save.call_count)


class TestFarmIndexView(FarmTestClass):

    def setUp(self):
        super().setUp()
        response = self.client.login(username='NormalUser', password='Password')
        self.assertTrue(response)

    def test_get(self):
        response = self.client.get(reverse('farm:index'))
        self.assertEquals(200, response.status_code)


class TestSingleExitWizard(FarmTestClass):
    def setUp(self):
        super().setUp()
        response = self.client.login(username='NormalUser', password='Password')
        self.assertTrue(response)

    def test_get(self):
        response = self.client.get(reverse('farm:single_animal_exit'))
        self.assertEquals(200, response.status_code)
        print(response)

    def test_post_valid_first_step(self):
        data = {'register_single_animal_exit-current_step': 'exit_information',
                'exit_information-date': '2017-01-16',
                'exit_information-weight': '75',
                'exit_information-room': self.normal_room1.id}

        response = self.client.post(reverse('farm:single_animal_exit'), data)
        self.assertEquals(200, response.status_code)
        self.assertEquals(response.context['wizard']['steps'].current, 'overview')

    def test_post_valid_first_step_separation_room(self):
        data = {'register_single_animal_exit-current_step': 'exit_information',
                'exit_information-date': '2017-01-16',
                'exit_information-weight': '75',
                'exit_information-room': self.separation_room.id}

        response = self.client.post(reverse('farm:single_animal_exit'), data)
        self.assertEquals(200, response.status_code)
        self.assertEquals(response.context['wizard']['steps'].current, 'animal_distinction')

    def test_post_valid_animal_distinction(self):
        data = {'register_single_animal_exit-current_step': 'exit_information',
                'exit_information-date': '2017-01-16',
                'exit_information-weight': '75',
                'exit_information-room': self.separation_room.id}

        response = self.client.post(reverse('farm:single_animal_exit'), data)
        self.assertEquals(200, response.status_code)
        self.assertEquals(response.context['wizard']['steps'].current, 'animal_distinction')

        data = {'register_single_animal_exit-current_step': 'animal_distinction',
                'animal_distinction-separation': self.separation1.id,
                }

        response = self.client.post(reverse('farm:single_animal_exit'), data)
        self.assertEquals(200, response.status_code)
        self.assertEquals(response.context['wizard']['steps'].current, 'overview')

        data = {'register_single_animal_exit-current_step': 'overview'}

        response = self.client.post(reverse('farm:single_animal_exit'), data)
        self.assertEquals(302, response.status_code)
        self.separation1.refresh_from_db()
        self.assertFalse(self.separation1.active)


class TestTransferWizard(FarmTestClass):
    def setUp(self):
        super().setUp()
        response = self.client.login(username='NormalUser', password='Password')
        self.assertTrue(response)

    def test_get(self):
        response = self.client.get(reverse('farm:new_transfer'))
        self.assertEquals(200, response.status_code)

    def test_post_valid_first_step(self):
        data = {'register_animal_transfer_wizard-current_step': 'generic',
                'generic-date': '2017-01-16',
                'generic-number_of_animals': 5,
                'generic-rooms': [self.normal_room1.id]}

        response = self.client.post(reverse('farm:new_transfer'), data)
        self.assertEquals(200, response.status_code)
        self.assertEquals(response.context['wizard']['steps'].current, 'detailed')

    def test_post_valid_detailed(self):
        data = {'register_animal_transfer_wizard-current_step': 'generic',
                'generic-date': '2017-01-16',
                'generic-number_of_animals': 5,
                'generic-rooms': [self.normal_room1.id]}

        response = self.client.post(reverse('farm:new_transfer'), data)
        self.assertEquals(200, response.status_code)
        self.assertEquals(response.context['wizard']['steps'].current, 'detailed')

        data = {'register_animal_transfer_wizard-current_step': 'detailed',
                'detailed-TOTAL_FORMS': 1,
                'detailed-INITIAL_FORMS': 1,
                'detailed-MIN_NUM_FORMS': 0,
                'detailed-MAX_NUM_FORMS': 1000,
                'detailed-0-room': self.normal_room1.id,
                'detailed-0-number_of_animals': '5',
                }

        response = self.client.post(reverse('farm:new_transfer'), data)
        self.assertEquals(200, response.status_code)
        self.assertEquals(response.context['wizard']['steps'].current, 'overview')

        data = {'register_single_animal_exit-current_step': 'overview'}

        response = self.client.post(reverse('farm:single_animal_exit'), data)
        self.assertEquals(302, response.status_code)
        self.separation1.refresh_from_db()
        self.assertFalse(self.separation1.active)