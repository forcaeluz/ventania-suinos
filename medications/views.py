from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from django.urls import reverse

from .models import Medication
from .models import Treatment

from .forms import MedicationForm, MedicationEntryForm, \
    TreatmentForm, ApplicationForm, TreatmentEndedForm, DiscardForm


@login_required()
def index(request):
    available_medications = Medication.objects.all()
    ongoing_treatment = [obj for obj in Treatment.objects.all() if obj.is_active is True]
    old_treatments = [obj for obj in Treatment.objects.all() if obj.is_active is False]

    params = {
        'medications': available_medications,
        'treatments': ongoing_treatment,
        'old_treatments': old_treatments[:10]
    }
    return render(request, 'medications/index.html', params)


@login_required()
def new_medication(request):
    form = MedicationForm()
    form_data = {
        'form': form,
        'action': reverse('medications:save_medication'),
        'title': 'Medication Information'
    }
    return render(request, 'medications/new_medication.html', {'form_data': form_data})


@login_required()
def save_medication(request):
    form = MedicationForm(request.POST)
    if form.is_valid():
        form.save()
        return HttpResponseRedirect(reverse('medications:index'))

    return render(request, 'medications/new_medication.html', {'form': form})


@login_required()
def new_entry(request):
    form = MedicationEntryForm()
    form_data = {
        'form': form,
        'action': reverse('medications:save_entry'),
        'title': 'Entry Information'
    }
    return render(request, 'medications/new_entry.html', {'form_data': form_data})


@login_required()
def save_entry(request):
    form = MedicationEntryForm(request.POST)
    if form.is_valid():
        form.save()
        return HttpResponseRedirect(reverse('medications:index'))

    return render(request, 'medications/new_entry.html', {'form': form})


@login_required()
def new_treatment(request):
    form = TreatmentForm()
    form_data = {
        'form': form,
        'action': reverse('medications:save_treatment'),
        'title': 'Animal and treatment information'
    }
    return render(request, 'medications/new_treatment.html', {'form_data': form_data})


@login_required()
def save_treatment(request):
    form = TreatmentForm(request.POST)
    if form.is_valid():
        form.save()
        return HttpResponseRedirect(reverse('medications:index'))

    return render(request, 'medications/new_treatment.html', {'form': form})


@login_required()
def new_application(request):
    treatment_id = request.GET.get('treatment_id', None)
    if treatment_id is None:
        return HttpResponseBadRequest()
    form = ApplicationForm(treatment_id=treatment_id)
    parameters = {
        'form': form,
    }
    return render(request, 'medications/new_application.html', parameters)


@login_required()
def save_application(request):
    form = ApplicationForm(request.POST)
    if form.is_valid():
        form.save()
        treatment_id = form.cleaned_data.get('treatment')
        return HttpResponseRedirect(reverse('medications:view_treatment', kwargs={'treatment_id': treatment_id}))

    parameters = {
        'form': form,
    }
    return render(request, 'medications/new_application.html', parameters)


@login_required()
def view_treatment(request, treatment_id):
    treatment = get_object_or_404(Treatment, pk=treatment_id)
    applications = treatment.medicationapplication_set.all().order_by('-date')
    params = {
        'treatment': treatment,
        'applications': applications
    }
    return render(request, 'medications/treatment_detail.html', params)


@login_required()
def stop_treatment(request):
    treatment_id = request.GET.get('treatment_id', None)
    if treatment_id is None:
        return HttpResponseBadRequest()
    form = TreatmentEndedForm(treatment_id=treatment_id)
    parameters = {
        'form': form,
    }
    return render(request, 'medications/stop_treatment.html', parameters)


@login_required()
def save_stop_treatment(request):
    form = TreatmentEndedForm(request.POST)
    if form.is_valid():
        form.save()
        treatment_id = form.cleaned_data.get('treatment')
        return HttpResponseRedirect(reverse('medications:view_treatment', kwargs={'treatment_id': treatment_id}))

    return render(request, 'medications/stop_treatment.html', {'form': form})


@login_required()
def new_discard(request):
    form = DiscardForm()
    form_data = {
        'form': form,
        'action': reverse('medications:save_discard'),
        'title': 'Discard Information'
    }
    return render(request, 'medications/new_discard.html', {'form_data': form_data})


@login_required()
def save_discard(request):
    form = DiscardForm(request.POST)
    if form.is_valid():
        form.save()
        return HttpResponseRedirect(reverse('medications:index'))

    return render(request, 'medications/new_discard.html', {'form': form})


@login_required()
def view_medication(request, medication_id):
    medication = get_object_or_404(Medication, id=medication_id)
    return render(request, 'medications/medication_detail.html', {'medication': medication})


@login_required()
def view_treatment_list(request):
    treatments = Treatment.objects.all()
    return render(request, 'medications/treatment_list.html', {'treatments': treatments})
