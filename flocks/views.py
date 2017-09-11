from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView
from .forms import FlockForm
from .kpis import *


@login_required
def index(request):
    current_flocks = [obj for obj in Flock.objects.all() if obj.number_of_living_animals > 0]
    old_flocks = [obj for obj in Flock.objects.all().order_by('-entry_date') if obj.number_of_living_animals == 0]
    old_flocks = old_flocks[:8]
    return render(request, 'flocks/index.html', {'current_flocks': current_flocks, 'previous_flocks': old_flocks})


@login_required
def create(request):
    form = FlockForm()
    return render(request, 'flocks/create.html', {'form': form})


@login_required
def save(request):
    form = FlockForm(request.POST)

    if form.is_valid():
        data = form.cleaned_data
        flock = Flock(entry_date=data.get('entry_date'),
                      entry_weight=data.get('entry_weight'),
                      number_of_animals=data.get('number_of_animals'))
        flock.save()
        return HttpResponseRedirect('/flocks/')

    return render(request, 'flocks/create.html', {'form': form})


class FlockDetailView(TemplateView):
    template_name = 'flocks/detail.html'

    def get(self, request, *args, **kwargs):
        flock_id = kwargs.get('flock_id', None)
        self.flock = get_object_or_404(Flock, pk=flock_id)
        return super().get(request, args, kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'flock': self.flock})
        context.update({'death_list': self.flock.animaldeath_set.all()})
        context.update({'separation_list': self.flock.animalseparation_set.all()})
        context.update({'exits_list': self.flock.animalflockexit_set.all()})
        context.update({'current_rooms': self.__get_building_info()})
        context.update({'kpi_list': self.__create_kpis()})
        return context

    def __get_building_info(self):
        room_entries = self.flock.animalroomentry_set.all()
        current_rooms = [obj.room for obj in room_entries if obj.room.get_animals_for_flock(self.flock.id) > 0]
        return [{'name': obj.__str__(), 'occupancy': obj.get_animals_for_flock(self.flock.id)} for obj in current_rooms]

    def __create_kpis(self):
        kpi_list = []

        kpi_list.append(NumberOfAnimalsKpi(self.flock))
        kpi_list.append(EstimatedWeightKpi(self.flock))
        kpi_list.append(ExitDateKpi(self.flock))
        kpi_list.append(DeathPercentageKpi(self.flock))
        kpi_list.append(CurrentFeedTypeKpi(self.flock))
        kpi_list.append(SeparationsKpi(self.flock))
        return kpi_list
