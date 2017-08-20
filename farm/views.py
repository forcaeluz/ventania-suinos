from django.views.generic import TemplateView, FormView
from django.shortcuts import render, HttpResponseRedirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils.translation import ugettext as _


from feeding.models import FeedType
from flocks.models import Flock, AnimalSeparation, AnimalDeath, AnimalFarmExit
from flocks.kpis import NumberOfAnimalsKpi, DeathPercentageKpi, SeparationsKpi, GrowRateKpi, InTreatmentKpi
from buildings.models import Room
from medications.models import Treatment

from .forms import AnimalSeparationForm, AnimalSeparationUpdateForm
from .forms import FeedTransitionForm, FeedEntryForm

# Delete forms
from .forms import AnimalDeathDeleteForm, AnimalSeparationDeleteForm, AnimalEntryDeleteForm, AnimalExitDeleteForm


class FarmWarning:
    def __init__(self, title, content, link):
        self.title = title
        self.content = content
        self.link = link


class FarmIndexView(TemplateView):
    template_name = "farm/index.html"

    def __init__(self):
        super().__init__()
        self.current_flocks = Flock.objects.present_at_farm()
        self.active_separations = [obj for obj in AnimalSeparation.objects.all() if obj.active]
        self.number_of_living_animals = sum([obj.number_of_living_animals for obj in self.current_flocks])
        self.farm_capacity = sum([room.capacity for room in Room.objects.all()])

    def get_context_data(self, **kwargs):
        context = super(FarmIndexView, self).get_context_data(**kwargs)
        context['flocks'] = self.current_flocks
        context['separations'] = [obj for obj in AnimalSeparation.objects.all() if obj.active]
        context['feed_types'] = FeedType.objects.all()
        context['kpis'] = self.generate_kpi_data()
        context['treatments'] = [obj for obj in Treatment.objects.all() if obj.is_active is True]
        context['warnings'] = self.generate_warnings()
        return context

    def generate_kpi_data(self):
        """Generate all the desired KPIs."""
        kpi_list = []
        kpi_list.extend(self.generate_flock_kpis())
        return kpi_list

    @staticmethod
    def generate_flock_kpis():
        """Generate KPIs with flock related information."""
        kpi_list = []

        kpi_list.append(NumberOfAnimalsKpi())
        kpi_list.append(DeathPercentageKpi())
        kpi_list.append(SeparationsKpi())
        kpi_list.append(GrowRateKpi())
        kpi_list.append(InTreatmentKpi())
        return kpi_list

    def generate_warnings(self):
        # No warnings for the time being.
        warning_list = []
        return warning_list


class EasyFatFormView(FormView):
    form_title = 'Form'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'form_title': self.form_title})
        return context


class DeleteAnimalEntry(FormView):
    template_name = 'farm/delete_confirm.html'
    form_class = AnimalEntryDeleteForm

    def get(self, request, *args, **kwargs):
        flock = get_object_or_404(Flock, id=kwargs.pop('flock_id'))
        form = AnimalEntryDeleteForm(flock=flock)
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        flock = get_object_or_404(Flock, id=kwargs.pop('flock_id'))
        form = AnimalEntryDeleteForm(request.POST, flock=flock)

        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('farm:index'))
        return render(request, self.template_name, {'form': form})


class RegisterNewAnimalSeparation(EasyFatFormView):
    template_name = 'farm/single_form.html'
    form_class = AnimalSeparationForm
    success_url = reverse_lazy('farm:index')

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'form_title': 'Register new separation'})
        return context


class EditAnimalSeparation(TemplateView):
    template_name = 'farm/single_form.html'

    def get(self, request, *args, **kwargs):
        separation = kwargs.get('separation_id')
        form = AnimalSeparationUpdateForm(separation_id=separation)
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        separation = kwargs.get('separation_id')
        form = AnimalSeparationUpdateForm(request.POST, separation_id=separation)

        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('flocks:detail', kwargs={'flock_id': form.separation.flock.id}))
        return render(request, self.template_name, {'form': form})


class DeleteDeath(EasyFatFormView):
    template_name = 'farm/delete_confirm.html'
    form_title = 'Delete animal death'
    form_class = AnimalDeathDeleteForm

    def form_valid(self, form):
        self.kwargs.update({'flock_id': form.death.flock.id})
        form.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('flocks:detail', kwargs={'flock_id': self.kwargs.get('flock_id')})

    def get_form_kwargs(self, **kwargs):
        kwargs = super().get_form_kwargs()
        kwargs.update({'death': get_object_or_404(AnimalDeath, id=self.kwargs.get('death_id'))})
        return kwargs


class DeleteSeparation(EasyFatFormView):
    template_name = 'farm/delete_confirm.html'
    form_class = AnimalSeparationDeleteForm
    form_title = 'Delete animal separation'

    def form_valid(self, form):
        self.kwargs.update({'flock_id': form.separation.flock.id})
        form.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('flocks:detail', kwargs={'flock_id': self.kwargs.get('flock_id')})

    def get_form_kwargs(self, **kwargs):
        kwargs = super().get_form_kwargs()
        kwargs.update({'separation': get_object_or_404(AnimalSeparation, id=self.kwargs.get('separation_id'))})
        return kwargs


class DeleteExit(EasyFatFormView):
    template_name = 'farm/delete_confirm.html'
    form_class = AnimalExitDeleteForm
    form_title = 'Delete animal exit'
    success_url = reverse_lazy('farm:index')

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_form_kwargs(self, **kwargs):
        kwargs = super().get_form_kwargs()
        kwargs.update({'exit': get_object_or_404(AnimalFarmExit, id=self.kwargs.get('exit_id'))})
        return kwargs


class RegisterFeedTransition(EasyFatFormView):
    form_class = FeedTransitionForm
    template_name = 'farm/single_form.html'
    form_title = 'Register feeding transition'
    success_url = reverse_lazy('farm:index')

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


class FeedEntryView(EasyFatFormView):
    template_name = 'farm/single_form.html'
    form_title = _('Register new feed entry')
    form_class = FeedEntryForm
    success_url = reverse_lazy('farm:index')

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)
