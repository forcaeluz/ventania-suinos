import datetime
from django.utils import timezone
from django.test import TestCase

from .models import Flock


class FlockTests(TestCase):

    def test_flock_exit_date(self):
        """
        flock_predicted_exit_date() Should return the date 90 days after entry
        """
        time = timezone.now() + datetime.timedelta(days=90)
        flock = Flock(entry_date=timezone.now().date(), entry_weight=10.00, number_of_animals=130)
        self.assertEqual(time.date(), flock.expected_exit_date)

    def test_flock_number_of_living_animals(self):
        flock = Flock(entry_date=timezone.now().date(), entry_weight=10.00, number_of_animals=130)
        self.assertEqual(130, flock.number_of_living_animals)

    def test_flock_number_of_living_animals_after_exit(self):
        entry_date = timezone.now().date()
        exit_date = entry_date + datetime.timedelta(days=95)
        flock = Flock(entry_date=timezone.now().date(), entry_weight=10.00, number_of_animals=130)
        flock.save()
        flock.animalexits_set.create(date=exit_date, total_weight=1000.000, number_of_animals=10)
        self.assertEqual(120, flock.number_of_living_animals)

    def test_flock_number_of_living_animals_after_multiple_exits(self):
        entry_date = timezone.now().date()
        exit_date = entry_date + datetime.timedelta(days=95)
        flock = Flock(entry_date=entry_date, entry_weight=10.00, number_of_animals=130)
        flock.save()
        flock.animalexits_set.create(date=exit_date, total_weight=6000.000, number_of_animals=65)
        flock.animalexits_set.create(date=exit_date, total_weight=6000.000, number_of_animals=65)
        self.assertEqual(0, flock.number_of_living_animals)

    def test_flock_number_of_living_animals_after_multiple_deaths(self):
        entry_date = timezone.now().date()
        exit_date = entry_date + datetime.timedelta(days=95)
        flock = Flock(entry_date=entry_date, entry_weight=10.00, number_of_animals=130)
        flock.save()
        flock.animaldeath_set.create(date=exit_date, weight=100.00)
        flock.animaldeath_set.create(date=exit_date, weight=100.00)
        self.assertEqual(128, flock.number_of_living_animals)

    def test_flock_average_grow_single_exit(self):
        entry_date = timezone.now().date()
        exit_date = entry_date + datetime.timedelta(days=100)
        flock = Flock(entry_date=timezone.now().date(), entry_weight=10.00, number_of_animals=1)
        flock.save()
        flock.animalexits_set.create(date=exit_date, total_weight=100.00, number_of_animals=1)
        self.assertAlmostEqual(0.900, flock.computed_daily_growth)

    def test_flock_average_grow_dual_exit(self):
        entry_date = timezone.now().date()
        exit_date = entry_date + datetime.timedelta(days=100)
        flock = Flock(entry_date=entry_date, entry_weight=20.00, number_of_animals=2)
        flock.save()
        flock.animalexits_set.create(date=exit_date, total_weight=100.00, number_of_animals=1)
        flock.animalexits_set.create(date=exit_date, total_weight=150.00, number_of_animals=1)
        self.assertAlmostEqual(1.150, flock.computed_daily_growth)

    def test_flock_average_grow_dual_exit_different_dates(self):
        entry_date = timezone.now().date()
        exit_date1 = entry_date + datetime.timedelta(days=50)
        exit_date2 = entry_date + datetime.timedelta(days=100)
        flock = Flock(entry_date=entry_date, entry_weight=20.00, number_of_animals=2)
        flock.save()
        flock.animalexits_set.create(date=exit_date1, total_weight=110.00, number_of_animals=1)
        flock.animalexits_set.create(date=exit_date2, total_weight=110.00, number_of_animals=1)
        self.assertAlmostEqual(1.50, flock.computed_daily_growth)

    def test_flock_average_grow_unknown(self):
        entry_date = timezone.now().date()
        flock = Flock(entry_date=entry_date, entry_weight=20.00, number_of_animals=2)
        flock.save()
        self.assertEqual(None, flock.computed_daily_growth)