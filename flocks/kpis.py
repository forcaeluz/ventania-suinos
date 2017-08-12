from datetime import date, timedelta
from ui_objects.models import Kpi, InfoKpi
from .models import Flock, AnimalFlockExit


class NumberOfAnimalsKpi(InfoKpi):

    """ Kpi for number of animals in the Farm.

        Although not strictly a Key Performance Indicator, this information is displayed in the same style of
        UI.
    """

    icon = 'address-book'
    description = 'Number of animals on farm'
    action = '#'
    action_name = 'Details'

    def __init__(self, flock=None):
        """Constructor.

        When a flock is provided, a KPI is created with only information for that flock. If no flock is supplied, the
        information is collected from all the flocks currently in the farm.
        """
        super().__init__()
        if flock is None:
            self.__setup_farm_level()
        elif isinstance(flock, Flock):
            self.value = flock.number_of_living_animals

    def __setup_farm_level(self):
        """Set's the KPI information up on Farm Level."""
        flocks_on_farm = Flock.objects.present_at_farm()
        count = 0
        for flock in flocks_on_farm:
            count += flock.number_of_living_animals

        self.value = count


class DeathPercentageKpi(Kpi):

    """Kpi for the death percentage."""

    icon = 'heartbeat'
    description = 'Death percentage'
    action_name = 'Details'
    action = '#'

    def __init__(self, flock=None):
        """Constructor.

        When a flock is provided, a KPI is created with only information for that flock. If no flock is supplied, the
        information is collected from all the flocks currently in the farm.
        """
        super().__init__()
        if flock is None:
            self.__setup_farm_level()
        elif isinstance(flock, Flock):
            self.float_value = flock.death_percentage
        self.__setup_color()
        self.value = "{:.2f}%".format(self.float_value)

    def __setup_farm_level(self):
        """Set's the KPI information up on Farm Level."""
        flocks_on_farm = Flock.objects.present_at_farm()
        entry_count = 0
        death_count = 0
        for flock in flocks_on_farm:
            entry_count += flock.number_of_animals
            death_count += flock.animaldeath_set.count()
        self.float_value = death_count * 100 / entry_count

    def __setup_color(self):
        if 1.0 <= self.float_value < 2.0:
            self.color = 'yellow'
        elif self.float_value >= 2.0:
            self.color = 'red'
        else:
            self.color = 'green'


class SeparationsKpi(Kpi):

    """Kpi for the percentage of separated animals."""

    icon = 'exclamation-triangle'
    description = 'Separation percentage'
    action_name = 'Details'
    action = '#'

    def __init__(self, flock=None):
        """Constructor.

        When a flock is provided, a KPI is created with only information for that flock. If no flock is supplied, the
        information is collected from all the flocks currently in the farm.
        """
        super().__init__()
        if flock is None:
            self.__setup_farm_level()
        elif isinstance(flock, Flock):
            self.float_value = flock.separated_animals * 100 / flock.number_of_animals
        self.__setup_color()
        self.value = "{:.2f}%".format(self.float_value)

    def __setup_farm_level(self):
        """Set's the KPI information up on Farm Level."""
        flocks_on_farm = Flock.objects.present_at_farm()
        entry_count = 0
        separation_count = 0
        for flock in flocks_on_farm:
            entry_count += flock.number_of_animals
            separation_count += flock.separated_animals
        self.float_value = separation_count * 100 / entry_count

    def __setup_color(self):
        if 1.5 <= self.float_value < 3.0:
            self.color = 'yellow'
        elif self.float_value >= 3.0:
            self.color = 'red'
        else:
            self.color = 'green'


class GrowRateKpi(Kpi):

    """Kpi for the GrowRate in the past 12 months.

    This KPI is based on historical data only. It considers all the animal exits in the past 365 days,
    and computes a weighted average of the grow rate in this period.
    """

    icon = 'line-chart'
    description = 'Grow Rate'
    action_name = 'Details'
    action = '#'

    def __init__(self):
        """Constructor."""
        super().__init__()
        considering_from = date.today() - timedelta(days=365)
        flocks_exited_past_year = AnimalFlockExit.objects.filter(
            flock__animalflockexit__farm_exit__date__gt=considering_from)
        if not flocks_exited_past_year:
            self.value = 'Unknown'
            self.float_value = None
        else:
            number_of_animals = sum([obj.number_of_animals for obj in flocks_exited_past_year])
            weighted_grow_rate = sum([obj.grow_rate * obj.number_of_animals for obj in flocks_exited_past_year])
            self.float_value = weighted_grow_rate / number_of_animals
            self.value = "{:.2f} kg/day".format(self.float_value)

        self.__setup_color()

    def __setup_color(self):
        if 0.500 <= self.float_value < 0.800:
            self.color = 'yellow'
        elif self.float_value < 0.500:
            self.color = 'red'
        else:
            self.color = 'green'
