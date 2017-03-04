from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from .models import Flock
from .forms import FlockForm, AnimalExitsForm, AnimalDeathForm


@login_required
def index(request):
    current_flocks = [obj for obj in Flock.objects.all() if obj.number_of_living_animals > 0]
    old_flocks = [obj for obj in Flock.objects.all() if obj.number_of_living_animals == 0]
    old_flocks = old_flocks[:8]
    return render(request, 'flocks/index.html', {'current_flocks': current_flocks, 'old_flocks': old_flocks})


@login_required
def create(request):
    form = FlockForm()
    return render(request, 'flocks/create.html', {'form': form})


@login_required
def save(request):
    form = FlockForm(request.POST)

    if form.is_valid():
        data = form.cleaned_data
        flock = Flock(entry_date=data.get('entry_date'),
                      entry_weight=data.get('entry_weight'),
                      number_of_animals=data.get('number_of_animals'))
        flock.save()
        return HttpResponseRedirect('/flocks/')

    return render(request, 'flocks/create.html', {'form': form})


@login_required
def detail(request, flock_id):
    flock = get_object_or_404(Flock, pk=flock_id)
    exit_list = flock.animalexits_set.all()
    death_list = flock.animaldeath_set.all()
    param_list = {
        'flock': flock,
        'exits_list': exit_list,
        'death_list': death_list
    }
    return render(request, 'flocks/detail.html', param_list)


@login_required
def create_animal_death(request):
    form = AnimalDeathForm()
    return render(request, 'animaldeaths/create.html', {'form': form})


@login_required
def save_animal_death(request):
    form = AnimalDeathForm(request.POST)
    if form.is_valid():
        form.save()
        return HttpResponseRedirect('/flocks/detail/%d' % form.cleaned_data['flock'].id)

    return render(request, 'animaldeaths/create.html', {'form': form})


@login_required
def create_animal_exit(request):
    form = AnimalExitsForm()
    return render(request, 'animalexits/create.html', {'form': form})


@login_required
def save_animal_exit(request):
    form = AnimalExitsForm(request.POST)

    if form.is_valid():
        form.save()
        return HttpResponseRedirect('/flocks/detail/%d' % form.cleaned_data['flock'].id)

    return render(request, 'animalexits/create.html', {'form': form})

