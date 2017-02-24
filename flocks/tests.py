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
        flock = Flock(entry_date=timezone.now().date(), entry_weight=10.00, number_of_animals=130)
        flock.save()
        flock.animalexits_set.create(date=exit_date, total_weight=6000.000, number_of_animals=65)
        flock.animalexits_set.create(date=exit_date, total_weight=6000.000, number_of_animals=65)
        self.assertEqual(0, flock.number_of_living_animals)

    def test_flock_number_of_living_animals_after_multiple_deaths(self):
        entry_date = timezone.now().date()
        exit_date = entry_date + datetime.timedelta(days=95)
        flock = Flock(entry_date=timezone.now().date(), entry_weight=10.00, number_of_animals=130)
        flock.save()
        flock.animaldeath_set.create(date=exit_date, weight=100.00)
        flock.animaldeath_set.create(date=exit_date, weight=100.00)
        self.assertEqual(128, flock.number_of_living_animals)
