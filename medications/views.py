from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from django.urls import reverse

from .models import Medication
from .models import Treatment

from .forms import MedicationForm, MedicationEntryForm

@login_required()
def index(request):
    available_medications = Medication.objects.all()
    ongoing_treatment = [obj for obj in Treatment.objects.all() if obj.is_active is True]
    params = {
        'medications': available_medications,
        'treatments': ongoing_treatment
    }
    return render(request, 'medications/index.html', params)


@login_required()
def new_medication(request):
    form = MedicationForm()
    return render(request, 'medications/new_medication.html', {'form': form})


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
    return render(request, 'medications/new_entry.html', {'form': form})


@login_required()
def save_entry(request):
    form = MedicationEntryForm(request.POST)
    if form.is_valid():
        form.save()
        return HttpResponseRedirect(reverse('medications:index'))

    return render(request, 'medications/new_entry.html', {'form': form})


@login_required()
def new_treatment(request):
    return HttpResponseRedirect(reverse('medications:index'))


@login_required()
def save_treatment(request):
    return HttpResponseRedirect(reverse('medications:index'))


@login_required()
def new_application(request):
    return HttpResponseRedirect(reverse('medications:index'))


@login_required()
def save_application(request):
    return HttpResponseRedirect(reverse('medications:index'))