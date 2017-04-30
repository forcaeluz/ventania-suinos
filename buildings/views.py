from django.shortcuts import render, HttpResponseRedirect
from django.forms import modelformset_factory, formset_factory
from django.views.generic import View, TemplateView
from django.urls import reverse

from .models import Building, AnimalRoomEntry, Room, AnimalRoomExit, AnimalSeparatedFromRoom, DeathInRoom
from .forms import FlockEntryRoomForm, FlockEntryRoomFormSet, AnimalExitRoomForm, AnimalExitRoomFormSet
from .forms import AnimalDeathRoomForm, AnimalSeparationRoomForm

from flocks.models import Flock, AnimalExits, AnimalDeath, AnimalSeparation


def index(request):
    buildings = Building.objects.all()

    return render(request, 'buildings/index.html', {'buildings': buildings})


class MigrationWizard(TemplateView):
    """
        This class is for the view of the migration steps, in order to synchronize flock data with building/room data.
    """
    template_name = 'buildings/index.html'

    def get(self, request, *args, **kwargs):
        if self._need_to_fix_entries():
            return HttpResponseRedirect(reverse('buildings:flock_entries_to_rooms'))
        elif self._need_to_fix_separations():
            return HttpResponseRedirect(reverse('buildings:animal_separation_to_room'))
        elif self._need_to_fix_deaths():
            return HttpResponseRedirect(reverse('buildings:animal_death_to_room'))
        else:
            return self._need_to_fix_exits()

    def _need_to_fix_entries(self):
        flocks_on_farm = [obj for obj in Flock.objects.all() if obj.number_of_living_animals > 0]

        flock_entries = sum([obj.number_of_animals for obj in flocks_on_farm])
        room_entries = sum([obj.number_of_animals for obj in AnimalRoomEntry.objects.all() if not obj.room.is_separation])
        return flock_entries != room_entries

    def _need_to_fix_separations(self):
        separation_count = AnimalSeparation.objects.count()
        room_separation_count = AnimalSeparatedFromRoom.objects.count()
        return separation_count != room_separation_count

    def _need_to_fix_deaths(self):
        death_count = AnimalDeath.objects.count()
        death_in_room_count = DeathInRoom.objects.count()
        return death_count != death_in_room_count

    def _need_to_fix_exits(self):
        exits = [obj for obj in AnimalExits.objects.all() if obj.animalseparation_set.count() == 0]

        for animal_exit in exits:
            room_exits = AnimalRoomExit.objects.filter(flock=animal_exit.flock, date=animal_exit.date)
            room_exit_count = 0
            for room_exit in room_exits:
                if not room_exit.room.is_separation:
                    room_exit_count += room_exit.number_of_animals

            separations = AnimalSeparatedFromRoom.objects.filter(separation__date=animal_exit.date)
            room_exit_count -= separations.count()
            if room_exit_count != animal_exit.number_of_animals:
                return HttpResponseRedirect(reverse('buildings:animal_exit_to_rooms') + '?exit_id=%d' % animal_exit.id)

        return HttpResponseRedirect(reverse('buildings:index'))


class AddRoomsToGroupsView(View):
    """
        This class provides the view to add multiple rooms to multiple groups, following a certain pattern.
    """
    pass


class LinkFlockEntriesToRoomsView(TemplateView):
    """
        This provides the view to link the flock entries to the available rooms.
        Should only be used once, to link existing flock data to the new buildings application.
    """
    form_class = FlockEntryRoomForm
    form_set = FlockEntryRoomFormSet
    template_name = 'buildings/migration.html'

    def get(self, request, *args, **kwargs):
        rooms = Room.objects.all().filter(is_separation=False)
        RoomEntryFormSetFactory = modelformset_factory(AnimalRoomEntry,
                                                       form=FlockEntryRoomForm,
                                                       formset=FlockEntryRoomFormSet,
                                                       extra=len(rooms))
        initial = []
        for room in rooms:
            initial.append({'number_of_animals': room.capacity, 'room': room})

        formset = RoomEntryFormSetFactory(initial=initial)
        return render(request, self.template_name, {'formset': formset})

    def post(self, request, *args, **kwargs):
        RoomEntryFormsetFactory = modelformset_factory(AnimalRoomEntry,
                                                       form=FlockEntryRoomForm,
                                                       formset=FlockEntryRoomFormSet)
        formset = RoomEntryFormsetFactory(request.POST)

        if formset.is_valid():
            formset.save()
            return HttpResponseRedirect(reverse('buildings:migration_wizard'))
        return render(request, self.template_name, {'formset': formset})


class LinkExitsToRoomsView(View):
    form_class = AnimalExitRoomForm

    def get(self, request, *args, **kwargs):
        exit_id = request.GET.get('exit_id')
        selected_exit = AnimalExits.objects.get(id=exit_id)
        flock = selected_exit.flock
        rooms = [obj for obj in Room.objects.all() if (obj.get_animals_for_flock(flock_id=flock.id, at_date=selected_exit.date) > 0)]
        AnimalExitLinkToRoomFormSetFactory = modelformset_factory(AnimalRoomExit,
                                                                  formset=AnimalExitRoomFormSet,
                                                                  form=AnimalExitRoomForm,
                                                                  extra=len(rooms))

        initial = []
        for room in rooms:
            initial.append({'animal_exit': exit_id, 'number_of_animals': 0, 'room': room})
        formset = AnimalExitLinkToRoomFormSetFactory(initial=initial)
        return render(request, 'buildings/animal_exit_room.html', {'formset': formset})

    def post(self, request, *args, **kwargs):
        AnimalExitLinkToRoomFormSetFactory = modelformset_factory(AnimalRoomExit,
                                                                  formset=AnimalExitRoomFormSet,
                                                                  form=AnimalExitRoomForm)

        formset = AnimalExitLinkToRoomFormSetFactory(request.POST)
        if formset.is_valid():
            formset.save()
            return HttpResponseRedirect(reverse('buildings:migration_wizard'))

        return render(request, 'buildings/animal_exit_room.html', {'formset': formset})


class LinkDeathsToRoomsView(TemplateView):
    """
        This class provides the view to link an existing death to a room.
        Note that this will create two things:
        - A Death to Room link
        - An RoomExit
    """
    template_name = 'buildings/animal_death_rooms.html'

    def get(self, request, *args, **kwargs):

        initial = [{'death_id': obj.id} for obj in AnimalDeath.objects.all() if obj.deathinroom_set.count() == 0]
        FormSetFactory = formset_factory(AnimalDeathRoomForm, extra=0)
        formset = FormSetFactory(initial=initial)
        return render(request, self.template_name, {'formset': formset})

    def post(self, request, *args, **kwargs):
        FormSetFactory = formset_factory(AnimalDeathRoomForm, extra=0)
        formset = FormSetFactory(request.POST)
        if formset.is_valid():
            for form in formset.forms:
                form.save()
            return HttpResponseRedirect(reverse('buildings:migration_wizard'))
        return render(request, self.template_name, {'formset': formset})


class LinkSeparationsToRoomsView(TemplateView):
    """
        This class provides the view to link an existing separation to a source and a destination room.
        Note that this will create multiple things:
        - An AnimalSeparation to Room link
        - A RoomExit (Room where the animal comes from)
        - A RoomEntry (Room where the animal went into)
        - Optionally, another room exit, coupled to the death of the exit of the separation. (Only if the separation
        has death or exit link.
    """
    template_name = 'buildings/animal_separation_room.html'

    def get(self, request, *args, **kwargs):

        initial = [{'separation_id': obj.id} for obj in AnimalSeparation.objects.all()]
        FormSetFactory = formset_factory(AnimalSeparationRoomForm, extra=0)
        formset = FormSetFactory(initial=initial)
        return render(request, self.template_name, {'formset': formset})

    def post(self, request, *args, **kwargs):
        FormSetFactory = formset_factory(AnimalSeparationRoomForm, extra=0)
        formset = FormSetFactory(request.POST)
        if formset.is_valid():
            for form in formset.forms:
                form.save()
            return HttpResponseRedirect(reverse('buildings:migration_wizard'))
        return render(request, self.template_name, {'formset': formset})
