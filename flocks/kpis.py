from datetime import date, timedelta
from django.utils.formats import date_format
from django.urls import reverse, reverse_lazy
from ui_objects.models import Kpi, InfoKpi
from .models import Flock, AnimalFlockExit
from feeding.models import FeedType


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
        if flocks_exited_past_year.count() == 0:
            self.value = 'Unknown'
            self.float_value = 0
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


class InTreatmentKpi(Kpi):
    icon = 'medkit'
    description = 'Ongoing treatments'
    action_name = 'Details'

    def __init__(self):
        self.float_value = 0.0
        self.__setup_farm_level()
        self.__setup_color()

    def __setup_farm_level(self):
        """Set's the KPI information up on Farm Level."""
        flocks_on_farm = Flock.objects.present_at_farm()
        count = 0
        t_count = 0
        for flock in flocks_on_farm:
            count += flock.number_of_living_animals
            t_count += len([obj for obj in flock.treatment_set.all() if obj.is_active is True])

        self.float_value = float(t_count) / count
        self.float_value = 100 * self.float_value
        self.value = str(t_count)

    def __setup_color(self):
        if 1.5 <= self.float_value < 3.0:
            self.color = 'yellow'
        elif self.float_value >= 3.0:
            self.color = 'red'
        else:
            self.color = 'green'


class EstimatedWeightKpi(InfoKpi):

    icon = 'balance-scale'
    description = 'Estimated Weight (kg)'
    action_name = 'Details'

    def __init__(self, flock):
        self.float_value = flock.estimated_avg_weight
        self.value = "{:.2f} kg".format(self.float_value)


class AverageExitWeightKpi(InfoKpi):

    icon = 'balance-scale'
    description = 'Estimated Weight (kg)'
    action_name = 'Details'

    def __init__(self, flock):
        self.float_value = flock.estimated_avg_weight
        self.value = "{:.2f} kg".format(self.float_value)


class ExitDateKpi(Kpi):

    """ Kpi for the ExitDate of a Flock.

    This KPI is used to show the expected exit date. With the colors, the proximity to the end-date is shown.
    """

    icon = 'calendar'
    description = 'Expected exit date'
    action_name = 'Register Group Exit'
    action = reverse_lazy('farm:animal_exit')

    def __init__(self, flock):
        self.float_value = flock.expected_exit_date
        self.value = date_format(flock.expected_exit_date, format='SHORT_DATE_FORMAT', use_l10n=True)
        self.__setup_color()

    def __setup_color(self):
        interval = self.float_value - date.today()
        interval_days = interval.days
        if interval_days > 15:
            self.color = 'green'
        elif interval_days > 0:
            self.color = 'yellow'
        else:
            self.color = 'red'


class CurrentFeedTypeKpi(Kpi):

    """ Kpi for displaying the recommended feed type.

    This KPI is used to show the recommended feed types. With the colors, the match between the recommended and the
    actually being used feed-types are displayed.
    """

    icon = 'cutlery'
    description = 'Current feed type'
    action_name = 'Register feeding transition'

    def __init__(self, flock):
        self.flock = flock
        used_types = self.__get_actual_feeding_types()
        recommended = self.__get_recommended_type()
        if used_types.get(recommended, 0) > 0:
            if len(used_types.keys()) == 1:
                self.color = 'green'
                self.action_name = 'Details'
            else:
                self.color = 'yellow'
        else:
            self.color = 'red'

    def __get_actual_feeding_types(self):
        feed_types = {}
        room_entries = self.flock.animalroomentry_set.all()
        for entry in room_entries:
            room = entry.room
            if room.get_animals_for_flock(flock_id=self.flock.id) > 0 and not room.is_separation:
                feed_type = room.get_feeding_type_at()
                feed_types.update({feed_type: feed_types.get(feed_type, 0) + 1})
        return feed_types

    def __get_recommended_type(self):
        time_since_entry = date.today() - self.flock.entry_date
        time_since_entry = time_since_entry.days
        time_to_exit = date.today() - self.flock.expected_exit_date
        time_to_exit = time_to_exit.days

        for feed_type in FeedType.objects.all():
            start = feed_type.start_feeding_age
            stop = feed_type.stop_feeding_age
            if (time_since_entry >= start >= 0) or (start < 0 and time_to_exit >= start):
                beyond_start = True
            else:
                beyond_start = False

            if (time_to_exit <= stop <= 0) or (stop > 0 and time_since_entry <= stop):
                before_end = True
            else:
                before_end = False

            if beyond_start and before_end:
                self.value = feed_type.name

                return feed_type
