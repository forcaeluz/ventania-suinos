from datetime import date
from django.utils.translation import ugettext as _

from ui_objects.templatetags.kpi import Kpi
from feeding.models import FeedType

from .models import Flock

# kpi_list.append(Kpi(number_of_animals, 'Number of living animals', 'address-book', 'green', '', '#'))
# kpi_list.append(Kpi(weight, 'Estimated Weight (kg)', 'balance-scale', 'green', '', '#'))
# kpi_list.append(Kpi(self.flock.expected_exit_date.strftime('%x'), 'Exit date', 'calendar', 'green', '', '#'))
# kpi_list.append(Kpi(self.flock.death_percentage, 'Death percentage', 'heartbeat', 'green', '', '#'))
# kpi_list.append(Kpi('S2 Aloj/S2', 'Current feed type', 'cutlery', 'yellow', 'Register Transition', '#'))


class LivingAnimalsKpi(Kpi):

    def __init__(self, value):
        super().__init__(value, _('Number of animals on farm'), 'address-book', 'primary', _('Details'), '#')


class EstimatedWeightKpi(Kpi):

    def __init__(self, value):
        super().__init__("{:.2f}".format(value),
                         _('Estimated average weight (kg)'), 'balance-scale', 'primary', _('Details'), '#')


class ExitDateKpi(Kpi):
    def __init__(self, value):
        assert isinstance(value, date)
        today = date.today()
        delta = value - today
        color = 'green'
        if 0 < delta.days < 14:
            color = 'yellow'
        if delta.days < 0:
            color = 'red'

        super().__init__(value.strftime('%x'), _('Expected exit date'), 'calendar', color, _('Details'), '#')


class DeathPercentageKpi(Kpi):
    def __init__(self, value):
        color = 'green'
        if 1.0 <= value < 2.0:
            color = 'yellow'
        if value >= 2.0:
            color = 'red'

        super().__init__("{:.2f}".format(value), _('Death percentage'), 'heartbeat', color, _('Details'), '#')


class CurrentFeedTypeKpi(Kpi):

    def __init__(self, flock):
        assert isinstance(flock, Flock)
        super().__init__('', _('Suggested feed type'), 'cutlery', 'primary', _('Details'), '#')
        time_since_entry = date.today() - flock.entry_date
        time_since_entry = time_since_entry.days
        time_to_exit = date.today() - flock.expected_exit_date
        time_to_exit = time_to_exit.days

        for feed_type in FeedType.objects.all():
            start = feed_type.start_feeding_age
            stop = feed_type.stop_feeding_age
            if (start >= 0 and time_since_entry >= start) or (start < 0 and time_to_exit >= start):
                beyond_start = True
            else:
                beyond_start = False

            if (stop <= 0 and time_to_exit <= stop) or (stop > 0 and time_since_entry <= stop):
                before_end = True
            else:
                before_end = False

            if beyond_start and before_end:
                self.value = feed_type.name


class AnimalSeparationKpi(Kpi):
    def __init__(self, value):
        color = 'green'
        if 1.0 <= value < 2.0:
            color = 'yellow'
        if value >= 2.0:
            color = 'red'

        super().__init__("{:.2f}".format(value), _('Animal separation'), 'exclamation-triangle', color, _('Details'), '#')
