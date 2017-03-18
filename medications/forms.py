from django import forms
from django.forms.fields import HiddenInput
from django.core.validators import ValidationError
from ui_objects.widgets import DatePickerWidget

from .models import Medication, MedicationApplication, MedicationDiscard, MedicationEntry, Treatment


class MedicationForm(forms.ModelForm):

    class Meta:
        model = Medication
        fields = ['name', 'recommended_age_start', 'recommended_age_stop', 'dosage_per_kg',
                  'grace_period_days', 'instructions']


class MedicationEntryForm(forms.ModelForm):

    class Meta:
        model = MedicationEntry
        fields = ['date', 'expiration_date', 'quantity', 'medication']
        localized_fields = ('date', 'expiration_date')
        widgets = {'date': DatePickerWidget, 'expiration_date': DatePickerWidget}