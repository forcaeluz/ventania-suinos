from django.test import TestCase
from django.forms import formset_factory
from buildings.models import Building, Room
from flocks.models import Flock, AnimalSeparation

from .forms import AnimalDeathForm, AnimalSeparationForm, AnimalSeparationDistinctionForm, GroupExitForm
from .forms import AnimalExitRoomFormset, AnimalExitRoomForm


class FarmTestClass(TestCase):
    def setUp(self):
        super().setUp()
        building = Building(name='b1')
        building.save()
        self.normal_room1 = Room(name='Room1', is_separation=False, capacity=13, group=building)
        self.normal_room1.save()
        self.normal_room2 = Room(name='Room1', is_separation=False, capacity=13, group=building)
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
