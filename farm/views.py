from django.shortcuts import render
from django.views.generic import TemplateView


from feeding.models import FeedType
from flocks.models import Flock, AnimalSeparation, AnimalExits

from statistics import mean
from datetime import datetime, timedelta


class FarmKpi:
    def __init__(self, kpi_class, title, value, unit):
        self.kpi_class = kpi_class
        self.title = title
        self.value = value
        self.unit = unit


class FarmIndexView(TemplateView):
    template_name = "farm/index.html"

    def get_context_data(self, **kwargs):
        context = super(FarmIndexView, self).get_context_data(**kwargs)
        context['flocks'] = [obj for obj in Flock.objects.all() if obj.number_of_living_animals > 0]
        context['separations'] = [obj for obj in AnimalSeparation.objects.all() if obj.active]
        context['feed_types'] = FeedType.objects.all()
        context['kpis'] = self.generate_kpi_data()
        return context

    def generate_kpi_data(self):
        kpi_list = []
        kpi_list.extend(self.generate_flock_kpis())
        kpi_list.extend(self.generate_historic_kpis())
        return kpi_list

    def generate_flock_kpis(self):
        """
        Generates the FarmKpi for the flocks currently in the farm.
        :return:
        """
        current_flocks = [obj for obj in Flock.objects.all() if obj.number_of_living_animals > 0]
        active_separations = [obj for obj in AnimalSeparation.objects.all() if obj.active]
        number_of_living_animals = sum([obj.number_of_living_animals for obj in current_flocks])
        number_of_animals = sum([obj.number_of_animals for obj in current_flocks])
        number_of_dead_animals = sum([obj.animaldeath_set.count() for obj in current_flocks])
        death_perc = number_of_dead_animals / number_of_animals * 100
        number_of_separated_animals = len(active_separations)

        separation_percentage = number_of_separated_animals / number_of_animals * 100
        kpi_nof_animals = FarmKpi('success', 'Animals on Farm', number_of_living_animals, '')
        kpi_death_perc = FarmKpi('danger', 'Death Percentage', '%.2f' % death_perc, '%')
        if death_perc < 2:
            kpi_death_perc.kpi_class = 'success'
        elif death_perc < 5:
            kpi_death_perc.kpi_class = 'warning'

        kpi_separation = FarmKpi('warning', 'Animal Separation', '%.2f' % separation_percentage, '%')

        return [kpi_nof_animals, kpi_death_perc, kpi_separation]

    def generate_historic_kpis(self):
        considering_from = datetime.today() - timedelta(days=365)
        flocks_exited_past_year = AnimalExits.objects.filter(flock__animalexits__date__gt=considering_from)
        if not flocks_exited_past_year:
            return []

        number_of_animals = sum([obj.number_of_animals for obj in flocks_exited_past_year])
        weighted_grow_rate = mean([obj.grow_rate * obj.number_of_animals for obj in flocks_exited_past_year])
        grow_rate = weighted_grow_rate / number_of_animals
        kpi_grow_rate = FarmKpi('success', 'Grow Rate', '%.2f' % grow_rate, 'kg/day')
        if grow_rate < 0.700:
            kpi_grow_rate.kpi_class = 'danger'
        elif grow_rate < 0.850:
            kpi_grow_rate.kpi_class = 'warning'

        return [kpi_grow_rate]