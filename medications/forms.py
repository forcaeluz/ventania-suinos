from django import forms
from django.forms.fields import HiddenInput
from django.core.validators import ValidationError
from ui_objects.widgets import DatePickerWidget
from datetime import datetime

from .models import Medication, MedicationApplication, MedicationDiscard, MedicationEntry, Treatment
from flocks.models import Flock


class MedicationForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(forms.ModelForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
            })
    class Meta:
        model = Medication
        fields = ['name', 'recommended_age_start', 'recommended_age_stop', 'dosage_per_kg',
                  'grace_period_days', 'instructions']


class MedicationEntryForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(forms.ModelForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
            })

    class Meta:
        model = MedicationEntry
        fields = ['date', 'expiration_date', 'quantity', 'medication']
        localized_fields = ('date', 'expiration_date')
        widgets = {'date': DatePickerWidget, 'expiration_date': DatePickerWidget}


class TreatmentForm(forms.Form):
    start_date = forms.DateField(widget=DatePickerWidget)
    flock = forms.ModelChoiceField(Flock.objects.all())
    medication = forms.ModelChoiceField(Medication.objects.all())
    comments = forms.CharField(max_length=140)
    dosage = forms.FloatField()

    def __init__(self, *args, **kwargs):
        super(forms.Form, self).__init__(*args, **kwargs)
        current_flocks = [obj.id for obj in Flock.objects.all() if obj.number_of_living_animals > 0]
        self.fields['flock'].queryset = Flock.objects.filter(pk__in=current_flocks)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
            })


    def save(self):
        date = self.cleaned_data.get('start_date')
        flock = self.cleaned_data.get('flock')
        comments = self.cleaned_data.get('comments')
        medication = self.cleaned_data.get('medication')
        dosage = self.cleaned_data.get('dosage')
        treatment = Treatment(start_date=date, flock=flock, comments=comments, medication=medication)
        treatment.save()
        application = MedicationApplication(date=date, dosage=dosage, treatment=treatment)
        application.save()


class ApplicationForm(forms.Form):
    date = forms.DateField(widget=DatePickerWidget)
    dosage = forms.FloatField()
    treatment = forms.IntegerField(widget=HiddenInput)

    def __init__(self, *args, **kwargs):
        treatment_id = kwargs.pop('treatment_id', None)
        super().__init__(*args, **kwargs)
        if treatment_id is not None:
            self.fields['treatment'].initial = treatment_id
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
            })

    def clean(self):
        treatment = Treatment.objects.get(id=self.cleaned_data.get('treatment'))
        date = self.cleaned_data.get('date')
        if treatment.start_date > date:
            raise ValidationError('Application date cannot be before treatment start.')

        if date > datetime.now().date():
            raise ValidationError('Application date cannot be in the future.')

    def save(self):
        treatment_id = self.cleaned_data.get('treatment')
        date = self.cleaned_data.get('date')
        dos = self.cleaned_data.get('dosage')
        appl = MedicationApplication(treatment_id=treatment_id, date=date, dosage=dos)
        appl.save()


class TreatmentEndedForm(forms.Form):
    date = forms.DateField(widget=DatePickerWidget)
    treatment = forms.IntegerField(widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        treatment_id = kwargs.pop('treatment_id', None)
        super().__init__(*args, **kwargs)
        if treatment_id is not None:
            self.fields['treatment'].initial = treatment_id
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
            })

    def clean(self):
        treatment = Treatment.objects.get(id=self.cleaned_data.get('treatment'))
        date = self.cleaned_data.get('date')
        if treatment.start_date > date:
            raise ValidationError('Stop date should be bigger than end date')

    def save(self):
        treatment = Treatment.objects.get(id=self.cleaned_data.get('treatment'))
        date = self.cleaned_data.get('date')
        treatment.stop_date = date
        treatment.save()


class DiscardForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(forms.ModelForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
            })
    class Meta:
        model = MedicationDiscard
        fields = ['date', 'quantity', 'medication', 'reason']
        widgets = {'date': DatePickerWidget}