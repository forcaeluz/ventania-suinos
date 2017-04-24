from django.shortcuts import render
from django.forms import modelformset_factory
from .models import Building, AnimalRoomEntry, Room
from .forms import MigrationFlockEntryRoomGroupForm, MigrationFlockEntryFormSet

def index(request):
    buildings = Building.objects.all()

    return render(request, 'buildings/index.html', {'buildings': buildings})


def migrate(request):
    rooms = Room.objects.all().filter(is_separation=False)
    MigrationRoomEntryFormsetFactory = modelformset_factory(AnimalRoomEntry,
                                                            form=MigrationFlockEntryRoomGroupForm,
                                                            # formset=MigrationFlockEntryFormSet,
                                                            extra=rooms.count())

    initial = []
    for room in rooms:
        initial.append({'number_of_animals': room.capacity, 'room': room})

    formset = MigrationRoomEntryFormsetFactory(initial=initial)
    return render(request, 'buildings/migration.html', {'formset': formset})


def save_migrate(request):
    MigrationRoomEntryFormsetFactory = modelformset_factory(AnimalRoomEntry,
                                                            form=MigrationFlockEntryRoomGroupForm,
                                                            formset=MigrationFlockEntryFormSet,
                                                            extra=40)
    formset = MigrationRoomEntryFormsetFactory(request.POST)

    if formset.is_valid():
        formset.save()

    return render(request, 'buildings/migration.html', {'formset': formset})
