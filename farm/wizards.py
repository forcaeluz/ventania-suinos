from django.urls import reverse
from django.forms import formset_factory
from django.utils.translation import ugettext as _
from django.shortcuts import HttpResponseRedirect


from formtools.wizard.views import SessionWizardView

from flocks.models import Flock
from buildings.models import Room, AnimalRoomExit, AnimalRoomEntry, AnimalRoomTransfer

from .forms import AnimalEntryForm, AnimalEntryRoomForm, AnimalEntryRoomFormset, GroupExitForm, AnimalExitRoomForm
from .forms import EasyFatForm, AnimalDeathForm, AnimalExitRoomFormset, AnimalSeparationDistinctionForm
from .forms import SingleAnimalExitForm, AnimalDeathUpdateForm

from .forms import TreatmentRoomAndSymptomsForm, DosageConfirmationForm, MedicationChoiceForm
from .forms import AnimalTransferFromForm, AnimalTransferFromDetailedFormset, AnimalTransferToForm


from .models import AnimalEntry, AnimalExit, NewTreatment


class EasyFatWizard(SessionWizardView):

    """This is a base class for the wizards inside EasyFat."""

    wizard_name = _('EasyFat Wizard')
    template_name = 'farm/form_wizard.html'
    title_dict = {}

    def done(self, form_list, **kwargs):
        raise NotImplementedError('EasyFatWizard is only an abstraction.')

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)
        context.update({'wizard_title': self.wizard_name})

        current_step = self.steps.current
        title = self.title_dict.get(current_step, current_step)
        context.update({'step_title': title})
        return context


class AnimalEntryBaseWizard(EasyFatWizard):

    """Base class for the AnimalEntry wizards.

    This class is a base class for the wizards used to create and update the AnimalEntries. It provides the form list,
    title_dict.

    The sub-classes are responsible for implementing the functions to collect and save the data.
    """

    form_list = [
        ('flock_information', AnimalEntryForm),
        ('building_information', formset_factory(form=AnimalEntryRoomForm, formset=AnimalEntryRoomFormset, extra=0))
    ]

    title_dict = {'flock_information': _('General flock information'),
                  'building_information': _('Placement of animals in the buildings')}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.animal_entry = AnimalEntry()

    def done(self, form_list, **kwargs):
        """Should be implemented in sub-classes."""
        raise NotImplementedError('EasyFatWizard is only an abstraction.')

    def _guess_initial_building_info(self):
        """Guess values for the form initial information for the building information step."""
        initial = []
        selected_rooms = self.get_cleaned_data_for_step('flock_information').get('rooms')
        animals = self.get_cleaned_data_for_step('flock_information').get('number_of_animals')
        default_entry = int(animals / len(selected_rooms))
        for room in selected_rooms:
            initial.append({'room': room, 'number_of_animals': default_entry})

        return initial

    def _get_initial_building_info(self):
        """Get the form initial information for the building information step, based on the AnimalEntry."""
        room_entries = self.animal_entry.flock.animalroomentry_set.all()
        initial = []

        for room in room_entries:
            initial.append({'room': room.room, 'number_of_animals': room.number_of_animals})

        return initial

    def _get_form_kwargs_building_info(self):
        """Get the form kwargs for the building information step."""
        number_of_animals = self.get_cleaned_data_for_step('flock_information')['number_of_animals']
        return {'number_of_animals': number_of_animals}


class RegisterNewAnimalEntry(AnimalEntryBaseWizard):

    """A wizard for registering new animal entries."""

    wizard_name = _('Register new animal entry')

    def done(self, form_list, **kwargs):
        """Save the wizard's data if valid, and redirects to the index page."""
        flock_info = self.get_cleaned_data_for_step('flock_information')
        room_info = self.get_cleaned_data_for_step('building_information')

        self.animal_entry.set_flock(data=flock_info)
        self.animal_entry.update_room_entries(room_info)
        if self.animal_entry.is_valid():
            self.animal_entry.save()

        return HttpResponseRedirect(reverse('farm:index'))

    def get_form_initial(self, step):
        """Get initial data for the form for the given step."""
        initial = None
        if step == 'building_information':
            initial = super()._guess_initial_building_info()

        return initial

    def get_form_kwargs(self, step=None):
        """Get the kwargs data for the given step."""
        kwargs = super().get_form_kwargs(step)
        if step == 'building_information':
            kwargs.update(super()._get_form_kwargs_building_info())

        return kwargs


class EditAnimalEntry(AnimalEntryBaseWizard):

    """A wizard to edit existing new animal entries."""

    wizard_name = _('Register animal entry')

    def get_form_initial(self, step):
        """Get initial data for the form for the given step."""
        initial = None
        flock = Flock.objects.get(id=self.kwargs.get('flock_id', None))
        self.animal_entry.set_flock(instance=flock)
        rooms = [an_entry.room for an_entry in self.animal_entry.room_entries]
        if step == 'flock_information':
            initial = {'number_of_animals': flock.number_of_animals,
                       'date': flock.entry_date,
                       'weight': flock.entry_weight,
                       'rooms': rooms}

        if step == 'building_information':
            initial = super()._guess_initial_building_info()

        return initial

    def get_form_kwargs(self, step=None):
        """Get the kwargs data for the given step."""
        kwargs = super().get_form_kwargs(step)
        flock = Flock.objects.get(id=self.kwargs.get('flock_id', None))
        self.animal_entry.set_flock(instance=flock)

        if step == 'flock_information':
            kwargs.update({'flock': self.animal_entry.flock})
        elif step == 'building_information':
            kwargs.update(super()._get_form_kwargs_building_info())

        return kwargs

    def done(self, form_list, **kwargs):
        """Save the wizard's data if valid, and redirects to the index page."""
        flock = Flock.objects.get(id=self.kwargs.get('flock_id', None))
        flock_data = self.get_cleaned_data_for_step('flock_information')
        building_data = self.get_cleaned_data_for_step('building_information')
        self.animal_entry.set_flock(instance=flock)
        self.animal_entry.update_flock(flock_data)
        self.animal_entry.update_room_entries(building_data)
        if self.animal_entry.is_valid():
            self.animal_entry.save()

        return HttpResponseRedirect(reverse('flocks:detail', kwargs={'flock_id': self.animal_entry.flock.id}))


class RegisterNewAnimalExit(EasyFatWizard):

    """Wizard to register new animal exits."""

    form_list = [
        ('general_information', GroupExitForm),
        ('building_information', formset_factory(form=AnimalExitRoomForm, formset=AnimalExitRoomFormset, extra=0)),
        ('overview', EasyFatForm)
    ]

    wizard_name = _('Register animal group exit')

    title_dict = {'general_information': _('General exit information'),
                  'building_information': _('Specific room information'),
                  'overview': _('Overview')}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_form_initial(self, step):
        initial = []
        if step == 'building_information':
            selected_rooms = self.get_cleaned_data_for_step('general_information').get('rooms')
            for room in selected_rooms:
                initial.append({'room': room, 'number_of_animals': 0})

        return initial

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)

        if self.steps.current == 'overview':
            context.update({'warnings': ['This is only an overview. Changing values does not affect the '
                                         'data that is going to be saved.']})
            form1 = self.get_form('general_information', self.storage.get_step_data('general_information'))
            form2 = self.get_form('building_information', self.storage.get_step_data('building_information'))
            context.update({'form_displays': [form1, form2]})
        return context

    def get_form_kwargs(self, step=None):
        kwargs = super().get_form_kwargs(step)
        if step == 'building_information':
            number_of_animals = self.get_cleaned_data_for_step('general_information')['number_of_animals']
            kwargs.update({'number_of_animals': number_of_animals})

        return kwargs

    def get_template_names(self):
        if self.steps.current == 'overview':
            return 'farm/wizard_overview.html'
        else:
            return self.template_name

    def done(self, form_list, **kwargs):
        saver = AnimalExit()
        saver.set_animal_farm_exit(cleaned_data=self.get_cleaned_data_for_step('general_information'))
        saver.set_room_exit_information(self.get_cleaned_data_for_step('building_information'))
        saver.clean()
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


class RegisterSingleAnimalExit(EasyFatWizard):
    """
        This Wizard is to register deaths. Usually this can be done in a single step, however,
        in some cases, it is necessary to distinguish the animal (in the case of separated animals).
        In those cases an extra step is added, used to distinguish between the animals.
    """

    wizard_name = _('Register animal death')
    form_list = [
        ('exit_information', SingleAnimalExitForm),
        ('animal_distinction', AnimalSeparationDistinctionForm),
        ('overview', EasyFatForm)
    ]

    title_dict = {'exit_information': _('General exit information'),
                  'animal_distinction': _('Distinguishing animals'),
                  'overview': _('Overview')}

    def __init__(self, **kwargs):
        condition_dict = {'animal_distinction': self.needs_animal_distinction}
        kwargs.update({'condition_dict': condition_dict})
        super().__init__(**kwargs)

    def done(self, form_list, **kwargs):
        # get the forms
        forms = kwargs.get('form_dict')
        exit_form = forms.get('exit_information')
        separation_form = forms.get('animal_distinction', None)

        if separation_form:  # Some distinction is needed.
            # Set the flock value in the exit form. Otherwise it won't always be able
            # to fill in the animal's flock.
            separation = separation_form.cleaned_data.get('separation', None)
            if separation is not None:
                exit_form.set_flock(separation.flock)

            # After saving we can get the exit value, and fill in on the distinction form.
            exit_form.save()
            animal_exit = exit_form.animal_exit
            separation_form.set_exit(animal_exit)
            separation_form.save()
        else:  # Death form is clear, no separation attached.
            exit_form.save()

        return HttpResponseRedirect(reverse('farm:index'))

    def get_form_kwargs(self, step=None):
        if step == 'animal_distinction':
            room = self.get_cleaned_data_for_step('exit_information')['room']
            return {'room': room}
        else:
            return {}

    @staticmethod
    def needs_animal_distinction(wizard_instance):
        """
        Class function to determine is the animal distinction step needs to be performed.
        It's made a static method to support the way it is called by the FormWizard.
        :param wizard_instance:
        :return:
        """
        data = wizard_instance.get_cleaned_data_for_step('exit_information') or None
        if data:
            return data['room'].is_separation
        return True


class RegisterNewAnimalDeath(EasyFatWizard):
    """
        This Wizard is to register deaths. Usually this can be done in a single step, however,
        in some cases, it is necessary to distinguish the animal (in the case of separated animals).
        In those cases an extra step is added, used to distinguish between the animals.
    """

    wizard_name = _('Register animal death')
    form_list = [
        ('death_information', AnimalDeathForm),
        ('animal_distinction', AnimalSeparationDistinctionForm),
        ('overview', EasyFatForm)
    ]

    title_dict = {'death_information': _('General death information'),
                  'animal_distinction': _('Distinguishing animals'),
                  'overview': _('Overview')}

    def __init__(self, **kwargs):
        condition_dict = {'animal_distinction': self.needs_animal_distinction}
        kwargs.update({'condition_dict': condition_dict})
        super().__init__(**kwargs)

    def done(self, form_list, **kwargs):
        # get the forms
        forms = kwargs.get('form_dict')
        death_form = forms.get('death_information')
        distinction_form = forms.get('animal_distinction', None)

        if distinction_form:  # Some distinction is needed.
            # Set the flock value in the death form. Otherwise it won't always be able
            # to fill in the animal's flock.
            death_form.set_flock(distinction_form.cleaned_data.get('separation', None))
            # After saving we can get the death value, and fill in on the distinction form.
            death_form.save()
            death = death_form.death

            distinction_form.set_death(death)
            distinction_form.save()
        else:  # Death form is clear, no separation attached.
            death_form.save()

        return HttpResponseRedirect(reverse('farm:index'))

    def get_form_kwargs(self, step=None):
        if step == 'animal_distinction':
            room = self.get_cleaned_data_for_step('death_information')['room']
            return {'room': room}
        else:
            return {}

    @staticmethod
    def needs_animal_distinction(wizard_instance):
        """
        Class function to determine is the animal distinction step needs to be performed.
        It's made a static method to support the way it is called by the FormWizard.
        :param wizard_instance:
        :return:
        """
        data = wizard_instance.get_cleaned_data_for_step('death_information') or None
        if data:
            return data['room'].is_separation and data['room'].occupancy > 1
        return True


class EditAnimalDeath(EasyFatWizard):

    wizard_name = _('Edit animal death')
    form_list = [
        ('death_information', AnimalDeathUpdateForm),
        ('animal_distinction', AnimalSeparationDistinctionForm),
        ('overview', EasyFatForm)
    ]

    title_dict = {'death_information': _('General death information'),
                  'animal_distinction': _('Distinguishing animals'),
                  'overview': _('Overview')}

    def __init__(self, **kwargs):
        condition_dict = {'animal_distinction': self.needs_animal_distinction}
        kwargs.update({'condition_dict': condition_dict})
        super().__init__(**kwargs)

    def get_form_kwargs(self, step=None):
        if step == 'death_information':
            return {'death_id': self.kwargs.get('death_id', 0)}
        elif step == 'animal_distinction':
            room = self.get_cleaned_data_for_step('death_information')['room']
            return {'room': room}
        else:
            return {}

    def done(self, form_list, **kwargs):
        # get the forms
        forms = kwargs.get('form_dict')
        death_form = forms.get('death_information')
        distinction_form = forms.get('animal_distinction', None)

        if distinction_form:  # Some distinction is needed.
            # Set the flock value in the death form. Otherwise it won't always be able
            # to fill in the animal's flock.
            death_form.set_flock(distinction_form.cleaned_data.get('separation', None))
            # After saving we can get the death value, and fill in on the distinction form.
            death_form.save()
            death = death_form.death

            distinction_form.set_death(death)
            distinction_form.save()
        else:  # Death form is clear, no separation attached.
            death_form.save()
        return HttpResponseRedirect(reverse('flocks:detail', kwargs={'flock_id': death_form.death.flock.id}))

    @staticmethod
    def needs_animal_distinction(wizard_instance):
        """
        Class function to determine is the animal distinction step needs to be performed.
        It's made a static method to support the way it is called by the FormWizard.
        :param wizard_instance:
        :return:
        """
        data = wizard_instance.get_cleaned_data_for_step('death_information') or None
        if data:
            return data['room'].is_separation and data['room'].occupancy > 1
        return True


class StartNewTreatment(EasyFatWizard):

    """Wizard for a treatment with medications.

    The wizard not only collects data about the treatment and building information but also gives the user suggestion
    about treatment options.
    """

    wizard_name = _('Register new treatment')
    form_list = [
        ('room_symptoms_information', TreatmentRoomAndSymptomsForm),
        ('medication_choice_information', MedicationChoiceForm),
        ('dosage_information', DosageConfirmationForm),
        ('overview', EasyFatForm)
    ]

    title_dict = {'room_symptoms_information': _('Room and Symptoms'),
                  'medication_choice_information': _('Medication'),
                  'dosage_information': _('Dosage and separation'),
                  'overview': _('Overview')
                  }

    def __init__(self, **kwargs):
        """Constructor."""
        self.treatment = NewTreatment()
        super().__init__(**kwargs)

    def done(self, form_list, **kwargs):
        """Save the new treatment data, and all the necessary objects with it."""
        self.treatment.save()
        return HttpResponseRedirect(reverse('farm:index'))

    def get(self, request, *args, **kwargs):
        """Clean the data from the new treatment."""
        self.treatment.reset()
        return super().get(request, *args, **kwargs)

    def process_step(self, form):
        """Process the data submitted for the current step.

        This is necessary to be able to provide suggestions for the next step.
        """
        if self.steps.current == 'room_symptoms_information':
            self.treatment.process_symptom_form(form.cleaned_data)
        elif self.steps.current == 'medication_choice_information':
            self.treatment.process_medication_form(form.cleaned_data)
        elif self.steps.current == 'dosage_information':
            self.treatment.process_dosage_and_separation_form(form.cleaned_data)
        return super().process_step(form)

    def post(self, request, *args, **kwargs):
        """Override the parent method, in order to load data from previous steps."""
        if self.steps.current == 'medication_choice_information':
            self.treatment.process_symptom_form(self.get_cleaned_data_for_step('room_symptoms_information'))
        elif self.steps.current == 'dosage_information':
            self.treatment.process_symptom_form(self.get_cleaned_data_for_step('room_symptoms_information'))
            self.treatment.process_medication_form(self.get_cleaned_data_for_step('medication_choice_information'))
        elif self.steps.current == 'overview':
            self.treatment.process_symptom_form(self.get_cleaned_data_for_step('room_symptoms_information'))
            self.treatment.process_medication_form(self.get_cleaned_data_for_step('medication_choice_information'))
            self.treatment.process_dosage_and_separation_form(self.get_cleaned_data_for_step('dosage_information'))
        return super().post(request, *args, **kwargs)

    def get_form_kwargs(self, step=None):
        """Generate the kwargs dict for the form in the specified step."""
        kwargs_data = super().get_form_kwargs(step)
        if step == 'medication_choice_information':
            kwargs_data.update({'suggested': self.treatment.suggest_medications()})

        return kwargs_data

    def get_form_initial(self, step):
        """Generate the initial data for the given step.

        For now, only the dosage information has an initial value.
        """
        initial = super().get_form_initial(step)
        if step == 'dosage_information':
            initial.update({'dosage': self.treatment.suggest_dosage()})
        return initial

    def get_context_data(self, form, **kwargs):
        """Generate the context data to be displayed.

        In this wizard this is used to display information about the suggestions given to the user.
        """
        context = super().get_context_data(form, **kwargs)
        current_step = self.steps.current
        if current_step == 'medication_choice_information':
            context.update({'suggestions': ['The first list contains the suggested medications. If your choice is not'
                                            'in that list, pick your choice in the second list, but be aware that is '
                                            'not a suggested medication.']})
        elif current_step == 'dosage_information':
            context.update({'suggestions': ['The suggested dosage is based on an estimated weight.',
                                            'It is strongly advised to separate the animal, to avoid having an animal'
                                            ' being treated in the flock when it exits.']})

        return context


class RegisterAnimalTransferWizard(EasyFatWizard):

    """ Wizard for registering transfers inside the farm."""

    wizard_name = _('Register animal transfer')

    form_list = [
        ('generic', AnimalTransferFromForm),
        ('detailed', formset_factory(form=AnimalExitRoomForm, formset=AnimalTransferFromDetailedFormset, extra=0)),
        ('destination', AnimalTransferToForm)
    ]

    title_dict = {'generic': _('Transfer information'),
                  'detailed': _('Detailed origin information'),
                  'destination': _('Destination information')}

    def done(self, form_list, **kwargs):
        date = self.get_cleaned_data_for_step('generic').get('date')
        number_of_animals = self.get_cleaned_data_for_step('generic').get('number_of_animals')
        destiny_rooom = self.get_cleaned_data_for_step('destination').get('room')
        room_exits_list = self.get_cleaned_data_for_step('detailed')
        exit_objects = []
        for room_exit in room_exits_list:
            number_of_animals_in_room = room_exit.get('number_of_animals')
            room = room_exit.get('room')
            flock = next(iter(room.get_flocks_present_at(date)))
            exit_object = AnimalRoomExit(date=date, number_of_animals=number_of_animals_in_room, room=room,
                                         flock=flock)
            exit_object.save()
            exit_objects.append(exit_object)

        entry_object = AnimalRoomEntry(room=destiny_rooom, number_of_animals=number_of_animals, date=date, flock=flock)
        entry_object.save()

        for exit_object in exit_objects:
            transfer_object = AnimalRoomTransfer(room_entry=entry_object, room_exit=exit_object)
            transfer_object.save()

        return HttpResponseRedirect(reverse('farm:index'))

    def get_form_initial(self, step):
        initial = []
        if step == 'detailed':
            date = self.get_cleaned_data_for_step('generic').get('date')
            selected_rooms = self.get_cleaned_data_for_step('generic').get('rooms')
            for room in selected_rooms:
                diff = room.get_occupancy_at_date(date) - room.capacity
                initial.append({'room': room, 'number_of_animals': max([0, diff])})

        return initial

    def get_form_kwargs(self, step=None):
        kwargs = super().get_form_kwargs(step)
        if step == 'detailed':
            number_of_animals = self.get_cleaned_data_for_step('generic').get('number_of_animals')
            date = self.get_cleaned_data_for_step('generic').get('date')
            kwargs.update({'number_of_animals': number_of_animals})
            kwargs.update({'date': date})
        return kwargs