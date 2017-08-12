from django.db import models
from django.db.models import Sum
from django.core.validators import ValidationError
from datetime import timedelta

from flocks.models import Flock


class Medication(models.Model):
    name = models.CharField(max_length=140, unique=True, null=False)
    recommended_age_start = models.IntegerField()
    recommended_age_stop = models.IntegerField()
    dosage_per_kg = models.FloatField()
    grace_period_days = models.IntegerField()
    instructions = models.TextField()
    quantity_unit = models.CharField(max_length=4, default='ml')

    def clean(self):
        if self.recommended_age_start >= self.recommended_age_stop:
            raise ValidationError('Start age should be smaller than stop age.', code='Start age bigger than stop age')

    @property
    def availability(self):
        """
            Property that tells how much of this medicine is available at the farm.
        :return: A float value, indicating how much. The units depend on the units used for this medicine.
        :rtype: float
        """
        entry_quantity = self.medicationentry_set.all().aggregate(Sum('quantity'))['quantity__sum']
        used_quantity = self.__get_used_medication()
        discarded_quantity = self.medicationdiscard_set.all().aggregate(Sum('quantity'))['quantity__sum']

        if discarded_quantity is None:
            discarded_quantity = 0

        if entry_quantity is None:
            entry_quantity = 0

        return entry_quantity - (used_quantity + discarded_quantity)

    def is_recommended_for_flock(self, flock):
        """
            This property tells if this medicine is recommended to give to a certain flock.
        :rtype: bool
        :param flock: The flock for which the condition is being checked.
        :return: True if it is recommended, false otherwise.
        """
        assert isinstance(flock, Flock)
        # Include logic to determine is medicine should be
        # suggested to this flock or not.
        return True

    def __str__(self):
        return self.name

    def __get_used_medication(self):
        """

        :return:
        """
        treatments = self.treatment_set.all()
        total_used = 0
        for treatment in treatments:
            total_used += treatment.total_amount_used

        return total_used


class Treatment(models.Model):
    start_date = models.DateField()
    stop_date = models.DateField(null=True)
    medication = models.ForeignKey(Medication)
    flock = models.ForeignKey(Flock)
    comments = models.TextField()

    @property
    def is_active(self):
        return self.stop_date is None

    @property
    def end_date_grace_period(self):
        grace_period = self.medication.grace_period_days
        last_application = self.medicationapplication_set.order_by('date').last()
        if last_application is None:
            return self.start_date

        return last_application.date + timedelta(days=grace_period)

    @property
    def total_amount_used(self):
        used = self.medicationapplication_set.all().aggregate(Sum('dosage'))['dosage__sum']
        if used is None:
            used = 0

        return used

    @property
    def number_of_application(self):
        return self.medicationapplication_set.all().count()


class MedicationApplication(models.Model):
    date = models.DateField()
    dosage = models.FloatField()
    treatment = models.ForeignKey(Treatment)


class MedicationEntry(models.Model):
    date = models.DateField()
    medication = models.ForeignKey(Medication)
    quantity = models.FloatField()
    expiration_date = models.DateField()


class MedicationDiscard(models.Model):
    date = models.DateField()
    medication = models.ForeignKey(Medication)
    quantity = models.FloatField()
    reason = models.CharField(max_length=100)


class Surgery(models.Model):

    """Surgery Model

    This model describes a surgery event. It could be coupled to a medical treatment, but that is not
    necessarily the case.
    """

    date = models.DateField()
    description = models.TextField()
    recovery_time = models.IntegerField()
    treatment = models.ForeignKey(Treatment, null=True)
    flock = models.ForeignKey(Flock)
