import datetime
from django.utils import timezone
from django.test import TestCase

from .models import Flock, AnimalFarmExit


class FlockTests(TestCase):

    def setUp(self):
        flock_entry_date = datetime.date(2017, 1, 1)
        self.flock1 = Flock(entry_date=flock_entry_date, entry_weight=2600.00, number_of_animals=130)
        self.flock1.save()

    def test_flock_exit_date(self):
        """
        flock_predicted_exit_date() Should return the date 90 days after entry
        """
        expected_exit_date = datetime.date(2017, 4, 23)
        self.assertEqual(expected_exit_date, self.flock1.expected_exit_date)

    def test_flock_name(self):
        """
        Tests the automatic name assignment to flocks.
        """
        self.assertEqual('2017_1', self.flock1.flock_name)

    def test_flock_number_of_living_animals(self):
        self.assertEqual(130, self.flock1.number_of_living_animals)

    def test_flock_number_of_living_animals_after_exit(self):
        exit_date = datetime.date(2017, 1, 10)
        farm_animal_exit = AnimalFarmExit(date=exit_date)
        farm_animal_exit.save()
        flock_exit = self.flock1.animalflockexit_set.create(farm_exit=farm_animal_exit,
                                                            number_of_animals=10,
                                                            weight=700)
        flock_exit.save()
        self.assertEqual(120, self.flock1.number_of_living_animals)

    def test_flock_number_of_living_animals_after_multiple_exits(self):
        exit_date = datetime.date(2017, 4, 23)
        farm_animal_exit = AnimalFarmExit(date=exit_date)
        farm_animal_exit.save()
        flock_exit1 = self.flock1.animalflockexit_set.create(farm_exit=farm_animal_exit,
                                                             number_of_animals=65,
                                                             weight=7500)
        flock_exit1.save()
        flock_exit2 = self.flock1.animalflockexit_set.create(farm_exit=farm_animal_exit,
                                                             number_of_animals=65,
                                                             weight=7500)
        flock_exit2.save()

        self.assertEqual(0, self.flock1.number_of_living_animals)

    def test_flock_number_of_living_animals_after_multiple_deaths(self):
        exit_date = datetime.date(2017, 1, 10)
        self.flock1.animaldeath_set.create(date=exit_date, weight=26.00)
        self.flock1.animaldeath_set.create(date=exit_date, weight=26.00)
        self.assertEqual(128, self.flock1.number_of_living_animals)

    def test_flock_average_grow_single_exit(self):
        exit_date = self.flock1.entry_date + datetime.timedelta(days=100)
        farm_animal_exit = AnimalFarmExit(date=exit_date)
        farm_animal_exit.save()
        flock_exit = self.flock1.animalflockexit_set.create(farm_exit=farm_animal_exit,
                                                            number_of_animals=1,
                                                            weight=110)
        flock_exit.save()
        self.assertAlmostEqual(0.900, self.flock1.computed_daily_growth)

    def test_flock_average_grow_dual_exit(self):
        exit_date = self.flock1.entry_date + datetime.timedelta(days=100)
        farm_animal_exit = AnimalFarmExit(date=exit_date)
        farm_animal_exit.save()

        flock_exit = self.flock1.animalflockexit_set.create(farm_exit=farm_animal_exit,
                                                            number_of_animals=1,
                                                            weight=110)
        flock_exit.save()
        flock_exit = self.flock1.animalflockexit_set.create(farm_exit=farm_animal_exit,
                                                            number_of_animals=1,
                                                            weight=160)
        flock_exit.save()
        self.assertAlmostEqual(1.150, self.flock1.computed_daily_growth)

    def test_flock_average_grow_dual_exit_different_dates(self):
        exit_date1 = self.flock1.entry_date + datetime.timedelta(days=50)
        exit_date2 = self.flock1.entry_date + datetime.timedelta(days=100)
        farm_animal_exit1 = AnimalFarmExit(date=exit_date1)
        farm_animal_exit1.save()
        farm_animal_exit2 = AnimalFarmExit(date=exit_date2)
        farm_animal_exit2.save()

        flock_exit = self.flock1.animalflockexit_set.create(farm_exit=farm_animal_exit1,
                                                            number_of_animals=1,
                                                            weight=120)
        flock_exit.save()
        flock_exit = self.flock1.animalflockexit_set.create(farm_exit=farm_animal_exit2,
                                                            number_of_animals=1,
                                                            weight=120)
        flock_exit.save()
        self.assertAlmostEqual(1.50, self.flock1.computed_daily_growth)

    def test_flock_average_grow_unknown(self):
        entry_date = timezone.now().date()
        flock = Flock(entry_date=entry_date, entry_weight=20.00, number_of_animals=2)
        flock.save()
        self.assertEqual(None, flock.computed_daily_growth)


class SeparationTests(TestCase):

    def setUp(self):
        flock_entry_date = datetime.date(2017, 1, 1)
        self.flock1 = Flock(entry_date=flock_entry_date, entry_weight=2600.00, number_of_animals=130)
        self.flock1.save()

        self.separation = self.flock1.animalseparation_set.create(date=datetime.date(2017, 1, 2), reason='Sick.')

    def test_create_separation(self):
        self.assertTrue(self.separation.active)

    def test_death_after_separation(self):
        death = self.flock1.animaldeath_set.create(date=datetime.date(2017, 1, 5), weight=22)
        self.separation.death = death
        self.assertFalse(self.separation.active)

    def test_exit_after_death(self):
        exit_date = self.flock1.entry_date + datetime.timedelta(days=20)
        farm_animal_exit = AnimalFarmExit(date=exit_date)
        farm_animal_exit.save()

        flock_exit = self.flock1.animalflockexit_set.create(farm_exit=farm_animal_exit,
                                                            number_of_animals=1,
                                                            weight=30)

        self.separation.exit = flock_exit
        self.assertFalse(self.separation.active)
