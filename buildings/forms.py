from django import forms
from django.utils.translation import ugettext as tr
from django.core.validators import ValidationError
from .models import AnimalRoomEntry
from .models import Room
from flocks.models import Flock


class MigrationFlockEntryFormSet(forms.BaseModelFormSet):
    def clean(self):
        if any(self.errors):
            return
        flocks = {obj.__str__(): obj.number_of_animals for obj in Flock.objects.all() if
                  obj.number_of_living_animals > 0}
        for form in self.forms:
            flocks[form.cleaned_data['flock'].__str__()] -= form.cleaned_data['number_of_animals']
            if flocks[form.cleaned_data['flock'].__str__()] < 0:
                raise forms.ValidationError("More animals in rooms than possible for flock: " +
                                            form.cleaned_data['flock'].__str__())

    def save(self, commit=True):
        for entry in self.forms:
            date = entry.cleaned_data['flock'].entry_date
            room_entry = entry.save(commit=False)
            room_entry.date = date
            room_entry.save()

        return super().save(commit)


class MigrationFlockEntryRoomGroupForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
            })
        self.fields['room'].widget.attrs['readonly'] = True

    def save(self, commit=True):
        return super().save(commit)

    class Meta:
        model = AnimalRoomEntry
        fields = ['flock', 'number_of_animals', 'room']
