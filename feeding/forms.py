from django import forms
from django.core.validators import ValidationError

from .models import FeedType, FeedEntry


class FeedTypeForm(forms.ModelForm):

    class Meta:
        model = FeedType
        fields = ['name', 'start_feeding_age', 'stop_feeding_age']
