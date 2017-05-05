from django.views.generic import TemplateView
from django.shortcuts import render, HttpResponseRedirect
from django.urls import reverse
from django.forms import formset_factory
from formtools.wizard.views import CookieWizardView, SessionWizardView
from statistics import mean
from datetime import datetime, timedelta


from feeding.models import FeedType
from flocks.models import Flock, AnimalSeparation, AnimalExits
from buildings.models import Room, AnimalRoomEntry


from .forms import AnimalEntryForm, AnimalEntryRoomForm, AnimalExitForm, AnimalExitRoomForm, AnimalExitRoomFormset
from .forms import EasyFatForm, AnimalEntryRoomFormset
from .models import AnimalExitWizardSaver


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
        if number_of_living_animals != number_of_animals_in_rooms:
            warning = FarmWarning('Data Inconsistency:', 'The number of living animals is not equal to the number of '
                                                         'animals inside rooms. This might be due to an update from a'
                                                         'version without the Buildings module to a version with the '
                                                         'Buildings module. You have to manually update the room '
                                                         'information, with the <a href="%s">wizard.</a>' % reverse('buildings:migration_wizard'),
                                  '')
            warning_list.append(warning)

        return warning_list


class RegisterNewAnimalEntry(SessionWizardView):
    """
        This class is a generic view for registering new flocks. If the buildings app is installed, it will
        request building information as well, otherwise it will only request flock information.
    """
    form_list = [
        ("flock_information", AnimalEntryForm),
        ("building_information", formset_factory(form=AnimalEntryRoomForm, formset=AnimalEntryRoomFormset, extra=0))
    ]
    template_name = 'farm/form_wizard.html'

    def done(self, form_list, **kwargs):
        flock_info = self.get_cleaned_data_for_step('flock_information')
        new_flock = Flock(number_of_animals=flock_info['number_of_animals'],
                          entry_date=flock_info['date'],
                          entry_weight=flock_info['weight'])
        new_flock.full_clean()
        new_flock.save()

        room_info = self.get_cleaned_data_for_step('building_information')
        room_info = [room for room in room_info if room['number_of_animals'] > 0]
        for room in room_info:
            room_entry = AnimalRoomEntry(number_of_animals=room['number_of_animals'],
                                         flock=new_flock,
                                         date=flock_info['date'],
                                         room=room['room'])
            room_entry.full_clean()
            room_entry.save()

        return HttpResponseRedirect(reverse('farm:index'))

    def get_form_initial(self, step):
        if step == 'building_information':
            rooms = [obj for obj in Room.objects.all() if obj.occupancy == 0 and not obj.is_separation]
            animals = int(self.storage.get_step_data('flock_information')['flock_information-number_of_animals'])
            default_entry = int(animals/len(rooms))
            initial = []
            for room in rooms:
                initial.append({'room': room, 'number_of_animals': default_entry})

            return initial

        return super().get_form_initial(step)

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)

        if self.steps.current == 'building_information':
            for sub_form in form.forms:
                if sub_form.warnings:
                    context.update({'warnings': ['With the suggested distribution, some rooms have '
                                                 'more animals than capacity.']})

        return context

    def get_form_kwargs(self, step=None):
        kwargs = super().get_form_kwargs(step)
        if step == 'building_information':
            kwargs.update({'number_of_animals':
                               self.storage.get_step_data('flock_information')['flock_information-number_of_animals']})

        return kwargs

class RegisterNewAnimalExit(SessionWizardView):
    """
        This class is a generic view for registering new exits. If the buildings app is installed, it will
        request building information as well.    
    """
    form_list = [
        ("flock_information", AnimalExitForm),
        ("building_information", formset_factory(form=AnimalExitRoomForm, formset=AnimalExitRoomFormset, extra=0)),
        ("overview", EasyFatForm)
    ]
    template_name = 'farm/form_wizard.html'

    def get_form_initial(self, step):
        initial = []
        if step == 'building_information':
            number_of_animals = int(self.storage.get_step_data('flock_information')['flock_information-number_of_animals'])
            flocks_present = [obj for obj in Flock.objects.order_by('entry_date') if obj.number_of_living_animals > 0]
            oldest = flocks_present[0]
            separated = len([obj for obj in oldest.animalseparation_set.all() if obj.active])
            if number_of_animals >= oldest.number_of_living_animals - separated:
                initial = self.__get_initial_room_data_flock_exit(oldest.id)
            else:
                initial = self.__get_initial_room_data_flock_exit(0)
        return initial

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)

        if self.steps.current == 'building_information':
            pass
        elif self.steps.current == 'overview':
            form_data = [self.get_cleaned_data_for_step('flock_information'),
                         self.__get_building_info_overview()]

            context.update({'form_data': form_data})
        return context

    def get_form_kwargs(self, step=None):
        kwargs = super().get_form_kwargs(step)
        if step == 'building_information':
            kwargs.update({'number_of_animals':
                               self.storage.get_step_data('flock_information')['flock_information-number_of_animals']})

        return kwargs

    def get_template_names(self):
        if self.steps.current == 'overview':
            return 'farm/wizard_overview.html'
        else:
            return self.template_name

    def done(self, form_list, **kwargs):
        group_form = kwargs.get('form_dict')['flock_information']
        building_form = kwargs.get('form_dict')['building_information']
        saver = AnimalExitWizardSaver(group_form, building_form)
        saver.save()
        return HttpResponseRedirect(reverse('farm:index'))

    @staticmethod
    def __get_initial_room_data_flock_exit(oldest_flock_id):
        initial = []
        for room in Room.objects.all():
            if room.get_animals_for_flock(oldest_flock_id) > 0 and not room.is_separation:
                initial.append({'room': room, 'number_of_animals': room.get_animals_for_flock(oldest_flock_id)})
            else:
                initial.append({'room': room, 'number_of_animals': 0})
        return initial

    def __get_building_info_overview(self):
        step_info = self.get_cleaned_data_for_step('building_information')
        step_info = [room for room in step_info if room['number_of_animals'] > 0]
        return step_info


