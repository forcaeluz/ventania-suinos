from django.views.generic import TemplateView
from django.urls import reverse

from feeding.models import FeedType
from flocks.models import Flock, AnimalSeparation, AnimalExits
from buildings.models import Room

from statistics import mean
from datetime import datetime, timedelta


class FarmKpi:
    def __init__(self, kpi_class, title, value, unit):
        self.kpi_class = kpi_class
        self.title = title
        self.value = value
        self.unit = unit


class FarmWarning:
    def __init__(self, title, content, link):
        self.title = title
        self.content = content
        self.link = link


class FarmIndexView(TemplateView):
    template_name = "farm/index.html"

    def __init__(self):
        self.current_flocks = [obj for obj in Flock.objects.all() if obj.number_of_living_animals > 0]
        self.active_separations = [obj for obj in AnimalSeparation.objects.all() if obj.active]
        self.number_of_living_animals = sum([obj.number_of_living_animals for obj in self.current_flocks])
        self.farm_capacity = sum([room.capacity for room in Room.objects.all()])

    def get_context_data(self, **kwargs):
        context = super(FarmIndexView, self).get_context_data(**kwargs)
        context['flocks'] = [obj for obj in Flock.objects.all() if obj.number_of_living_animals > 0]
        context['separations'] = [obj for obj in AnimalSeparation.objects.all() if obj.active]
        context['feed_types'] = FeedType.objects.all()
        context['kpis'] = self.generate_kpi_data()
        context['warnings'] = self.generate_warnings()
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
        kpi_list = []

        number_of_animals = sum([obj.number_of_animals for obj in self.current_flocks])
        number_of_dead_animals = sum([obj.animaldeath_set.count() for obj in self.current_flocks])
        death_percentage = number_of_dead_animals / number_of_animals * 100
        number_of_separated_animals = len(self.active_separations)

        separation_percentage = number_of_separated_animals / number_of_animals * 100
        kpi_list.append(FarmKpi('success', 'Animals on Farm', self.number_of_living_animals, ''))

        if self.farm_capacity is not 0:
            kpi_list.append(FarmKpi('success', 'Occupancy', '%.2f' % (self.number_of_living_animals * 100 / self.farm_capacity), '%'))

        kpi_death_perc = FarmKpi('danger', 'Death Percentage', '%.2f' % death_percentage, '%')
        if death_percentage < 2:
            kpi_death_perc.kpi_class = 'success'
        elif death_percentage < 5:
            kpi_death_perc.kpi_class = 'warning'
        kpi_list.append(kpi_death_perc)
        kpi_list.append(FarmKpi('warning', 'Animal Separation', '%.2f' % separation_percentage, '%'))

        return kpi_list

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

    def generate_warnings(self):
        warning_list = []
        number_of_living_animals = sum([obj.number_of_living_animals for obj in self.current_flocks])
        number_of_animals_in_rooms = sum([room.occupancy for room in Room.objects.all()])
        if number_of_living_animals != number_of_animals_in_rooms+1:
            warning = FarmWarning('Data Inconsistency:', 'The number of living animals is not equal to the number of '
                                                         'animals inside rooms. This might be due to an update from a'
                                                         'version without the Buildings module to a version with the '
                                                         'Buildings module. You have to manually update the room '
                                                         'information, with the <a href="%s">wizard.</a>' % reverse('buildings:migration_wizard'),
                                  '')
            warning_list.append(warning)

        return warning_list


class RegisterNewAnimalEntry(TemplateView):
    """
        This class is a generic view for registering new flocks. If the buildings app is installed, it will
        request building information as well, otherwise it will only request flock information.
    """
    def get(self, request, *args, **kwargs):
        super().get(request, *args, **kwargs)


class RegisterNewAnimalExit(TemplateView):
    """
        This class is a generic view for registering new exits. If the buildings app is installed, it will
        request building information as well.    
    """
    pass
