from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView
from jchart import Chart
from jchart.config import Axes, DataSet, rgba, Tick

from datetime import datetime, timedelta

from ui_objects.ColorDefinitions import colors

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
        context.update({'kpi_list': self.__create_kpis()})
        context.update({'state_chart': FlockStateChart(self.flock)})
        if self.flock.number_of_living_animals > 0:
            context.update({'distribution_chart': RoomDistributionChart(self.flock)})
        context.update({'time_chart': AnimalsOverTimeChart(self.flock)})
        return context

    def __get_building_info(self):
        room_entries = self.flock.animalroomentry_set.all()
        current_rooms = [obj.room for obj in room_entries if obj.room.get_animals_for_flock(self.flock.id) > 0]
        return [{'name': obj.__str__(), 'occupancy': obj.get_animals_for_flock(self.flock.id)} for obj in current_rooms]

    def __create_kpis(self):
        kpi_list = []
        if self.flock.number_of_living_animals > 0:
            kpi_list.append(EstimatedWeightKpi(self.flock))
            kpi_list.append(ExitDateKpi(self.flock))
            kpi_list.append(CurrentFeedTypeKpi(self.flock))
        return kpi_list

    def __create_room_graph(self):
        pass


class FlockStateChart(Chart):
    chart_type = 'pie'
    legend = False

    def __init__(self, flock):
        super().__init__()
        self.living_animals = flock.number_of_living_animals
        self.dead_animal = (flock.death_percentage * flock.number_of_animals) / 100
        self.separated = flock.get_separated_animals_at_date(datetime.today())
        self.exited_animals = sum([obj.number_of_animals for obj in flock.animalflockexit_set.all()])

    def get_labels(self, **kwargs):
        return ["At Farm", "Dead", "Separated", "Exited"]

    def get_datasets(self, **kwargs):
        data = [self.living_animals, self.dead_animal, self.separated, self.exited_animals]
        pie_colors = [
            colors['green'],
            colors['red'],
            colors['yellow'],
            colors['blue'],
        ]
        return [DataSet(data=data,
                        label="Current Animal States",
                        backgroundColor=pie_colors,
                        hoverBackgroundColor=pie_colors)]


class RoomDistributionChart(Chart):
    chart_type = 'pie'
    legend = False

    def __init__(self, flock):
        super().__init__()
        self.flock = flock
        room_entries = self.flock.animalroomentry_set.all()
        self.current_rooms = [obj.room for obj in room_entries if obj.room.get_animals_for_flock(self.flock.id) > 0]

    def get_labels(self, **kwargs):
        room_labels = [obj.__str__() for obj in self.current_rooms]
        return room_labels

    def get_datasets(self, **kwargs):
        base_colors = ['green', 'blue', 'yellow', 'red']
        # data = [obj.get_animals_for_flock(self.flock.id) for obj in self.current_rooms]
        groups = {}
        group_count = {}
        for room in self.current_rooms:
            groups.setdefault(room.group, []).append(room)
            group_count.update({room.group: group_count.get(room.group, 0) + room.get_animals_for_flock(self.flock.id)})
        inner_data = []
        outer_data = []
        inner_colors = []
        outer_colors = []
        color_counter = 0
        for room_group, rooms in groups.items():
            inner_data.append(group_count.get(room_group))
            inner_colors.append(colors[base_colors[color_counter]])
            outer_color_counter = 1
            for room in rooms:
                outer_data.append(room.get_animals_for_flock(self.flock.id))
                outer_colors.append(colors[base_colors[color_counter] + '-{0}'.format((10-outer_color_counter)*100)])
                outer_color_counter += 1
            color_counter += 1

        return [DataSet(data=outer_data,
                        label="Current Animal Distribution",
                        backgroundColor=outer_colors,
                        hoverBackgroundColor=outer_colors)
                ]


class AnimalsOverTimeChart(Chart):
    chart_type = 'line'

    scales = {
        'xAxes': [Axes(type='time', position='bottom')],
        'yAxes': [{'display': True}]
    }
    tooltips = {'mode': 'x'}

    def __init__(self, flock):
        super().__init__()
        self.flock = flock
        if self.flock.number_of_living_animals > 0:
            self.end_date = datetime.today().date()
        else:
            exit_dates = [obj.date for obj in self.flock.animalflockexit_set.all()]
            self.end_date = max(exit_dates) + timedelta(days=1)

    def get_datasets(self, **kwargs):

        return [DataSet(data=self.__get_living_animals_data(),
                        label='Living Animals',
                        borderColor=colors['green']),
                DataSet(data=self.__get_dead_data(),
                        label='Dead Animals',
                        borderColor=colors['red']),
                DataSet(data=self.__get_separation_data(),
                        label='Separated Animals',
                        borderColor=colors['yellow']),
                DataSet(data=self.__get_exit_data(),
                        label='Exited Animals',
                        borderColor=colors['blue'])
                ]

    def __get_separation_data(self):
        base = self.end_date
        entry_date = self.flock.entry_date
        numdays = (base - entry_date).days
        date_list = [entry_date + timedelta(days=x) for x in range(0, numdays)]
        data_set = [{'x': obj, 'y': self.flock.get_separated_animals_at_date(obj)} for obj in date_list]
        return data_set

    def __get_living_animals_data(self):
        base = self.end_date
        entry_date = self.flock.entry_date
        numdays = (base - entry_date).days
        date_list = [entry_date + timedelta(days=x) for x in range(0, numdays)]
        data_set = [{'x': obj, 'y': self.flock.get_living_animals_at_date(obj)} for obj in date_list]
        return data_set

    def __get_dead_data(self):
        base = self.end_date
        entry_date = self.flock.entry_date
        numdays = (base - entry_date).days
        date_list = [entry_date + timedelta(days=x) for x in range(0, numdays)]
        data_set = [{'x': obj, 'y': self.flock.get_dead_animals_at_date(obj)} for obj in date_list]
        return data_set

    def __get_exit_data(self):
        base = self.end_date
        entry_date = self.flock.entry_date
        numdays = (base - entry_date).days
        date_list = [entry_date + timedelta(days=x) for x in range(0, numdays)]
        data_set = [{'x': obj, 'y': self.flock.get_exited_animals_at_date(obj)} for obj in date_list]
        return data_set