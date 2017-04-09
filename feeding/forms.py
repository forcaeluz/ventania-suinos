from django import forms
from django.utils.translation import ugettext as tr
from django.core.validators import ValidationError
from ui_objects.widgets import DatePickerWidget
from .models import FeedType, FeedEntry
from datetime import datetime


class FeedTypeForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
            })

    def clean_stop_feeding_age(self):
        stop_age = self.cleaned_data.get('stop_feeding_age')
        start_age = self.cleaned_data.get('start_feeding_age')
        if start_age >= stop_age:
            raise ValidationError(tr("Stop feeding age should be bigger than start feeding age."), code='Stop too soon')

        return stop_age

    class Meta:
        model = FeedType
        fields = ['name', 'start_feeding_age', 'stop_feeding_age']


class FeedEntryForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
            })

        self.fields['date'].initial = datetime.today().date()

    class Meta:
        model = FeedEntry
        fields = ['date', 'feed_type', 'weight']
        widgets = {'date': DatePickerWidget()}