from django.test import TestCase
from django.core.validators import ValidationError
from datetime import date
from .models import Medication, Treatment, MedicationApplication, MedicationEntry, MedicationDiscard
from flocks.models import Flock


class MedicineModelTest(TestCase):

    def setUp(self):
        super().setUp()
        self.flock1 = Flock(entry_date='2017-01-01', entry_weight=2200, number_of_animals=100)
        self.flock1.save()

    def test_creation(self):
        med = Medication(name='Medicine1', recommended_age_start=20, recommended_age_stop=50, dosage_per_kg=3,
                         grace_period_days=10, instructions='Hello World')
        med.full_clean()
        med.save()
        self.assertEqual(med.name, 'Medicine1')
        self.assertEqual(20, med.recommended_age_start)

    def test_invalid_start_stop_ages(self):
        med = Medication(name='Medicine1', recommended_age_start=30, recommended_age_stop=20, dosage_per_kg=3,
                         grace_period_days=10, instructions='Apply')
        with self.assertRaises(ValidationError):
            med.full_clean()

    def test_stock_quantity(self):
        med = Medication(name='Medicine1', recommended_age_start=30, recommended_age_stop=20, dosage_per_kg=3,
                         grace_period_days=10)
        med.save()
        med.medicationentry_set.create(date='2017-01-01', expiration_date='2017-10-01',
                                     quantity=100)

        self.assertEqual(100, med.availability)

    def test_stock_quantity_after_application(self):
        med = Medication(name='Medicine1', recommended_age_start=30, recommended_age_stop=20, dosage_per_kg=3,
                         grace_period_days=10)
        med.save()
        med.medicationentry_set.create(date='2017-01-01', expiration_date='2017-10-01',
                                     quantity=100)

        treatment = med.treatment_set.create(flock=self.flock1, start_date='2017-01-10')
        treatment.save()

        application = treatment.medicationapplication_set.create(date='2017-01-10', dosage=10)
        application.save()
        self.assertEqual(90, med.availability)

    def test_stock_quantity_after_discard(self):
        med = Medication(name='Medicine1', recommended_age_start=30, recommended_age_stop=20, dosage_per_kg=3,
                         grace_period_days=10)
        med.save()
        med.medicationentry_set.create(date='2017-01-01', expiration_date='2017-10-01',
                                     quantity=100)

        med.medicationdiscard_set.create(date='2017-02-02', quantity=30, reason='Bad storage')
        self.assertEqual(70, med.availability)


class TreatmentModelTest(TestCase):
    def setUp(self):
        super().setUp()
        self.medication1 = Medication(name='Medicine1', recommended_age_start=20, recommended_age_stop=50, dosage_per_kg=3,
                                    grace_period_days=10)
        self.medication1.save()
        self.flock1 = Flock(entry_date='2017-01-01', entry_weight=2200, number_of_animals=100)
        self.flock1.save()

    def test_creation(self):
        treatment = Treatment(flock=self.flock1, start_date='2017-01-10', medication=self.medication1)
        treatment.save()

    def test_is_active_true(self):
        treatment = Treatment(flock=self.flock1, start_date='2017-01-10', medication=self.medication1)
        treatment.save()
        self.assertTrue(treatment.is_active)

    def test_set_stop_date(self):
        treatment = Treatment(flock=self.flock1, start_date='2017-01-10', medication=self.medication1)
        treatment.save()
        treatment.stop_date = '2017-01-15'
        treatment.save()
        self.assertEqual(treatment.stop_date, '2017-01-15')

    def test_is_active_after_stop(self):
        treatment = Treatment(flock=self.flock1, start_date='2017-01-10', medication=self.medication1)
        treatment.save()
        treatment.stop_date = '2017-01-15'
        treatment.save()
        self.assertFalse(treatment.is_active)

    def test_grace_period_without_application(self):
        """
            Tests the computation of the grace period, date of end grace period.
            Note that as long as there are no actual applications, the grace period is zero.
        """
        treatment = Treatment(flock=self.flock1, start_date='2017-01-10', medication=self.medication1)
        treatment.save()
        self.assertEqual('2017-01-10', treatment.end_date_grace_period)

    def test_grace_period_after_application(self):
        treatment = Treatment(flock=self.flock1, start_date='2017-01-10', medication=self.medication1)
        treatment.save()
        treatment.medicationapplication_set.create(date='2017-01-10', dosage=10)
        self.assertEqual(date(year=2017, month=1, day=20), treatment.end_date_grace_period)

    def test_grace_period_after_multiple_applications(self):
        treatment = Treatment(flock=self.flock1, start_date='2017-01-10', medication=self.medication1)
        treatment.save()
        treatment.medicationapplication_set.create(date='2017-01-10', dosage=10)
        treatment.medicationapplication_set.create(date='2017-01-11', dosage=10)
        self.assertEqual(date(year=2017, month=1, day=21), treatment.end_date_grace_period)


class TestMedicineApplication(TestCase):

    def setUp(self):
        super().setUp()
        self.medication1 = Medication(name='Medicine1', recommended_age_start=20, recommended_age_stop=50,
                                    dosage_per_kg=3,
                                    grace_period_days=10)
        self.medication1.save()
        self.flock1 = Flock(entry_date='2017-01-01', entry_weight=2200, number_of_animals=100)
        self.flock1.save()
        self.treatment = Treatment(flock=self.flock1, start_date='2017-01-10', medication=self.medication1)
        self.treatment.save()

    def test_creation(self):
        med_application = MedicationApplication(date='2017-01-10', dosage=10, treatment=self.treatment)
        med_application.save()


class TestMedicineEntry(TestCase):
    def setUp(self):
        super().setUp()
        self.medication1 = Medication(name='Medicine1', recommended_age_start=20, recommended_age_stop=50,
                                    dosage_per_kg=3,
                                    grace_period_days=10)
        self.medication1.save()

    def test_creation(self):
        entry = MedicationEntry(medication=self.medication1, date='2017-01-01', expiration_date='2017-10-01',
                                quantity=100)
        entry.save()


# class TestMedicineDiscard(TestCase):
