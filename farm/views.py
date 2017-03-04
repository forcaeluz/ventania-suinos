from django.shortcuts import render
from feeding.models import FeedType
from flocks.models import Flock
from statistics import mean


def index(request):
    feeding_types = FeedType.objects.all()
    flocks = [obj for obj in Flock.objects.all() if obj.number_of_living_animals > 0]
    if len(flocks) == 0 or feeding_types.count() == 0:
        return render(request, 'farm/welcome.html')

    n_animals = sum([flock.number_of_living_animals for flock in flocks])
    death_perc = mean([flock.death_percentage for flock in flocks])
    params = {
        'flocks': flocks,
        'feed_types': feeding_types,
        'n_animals': n_animals,
        'death_perc': death_perc,
    }
    return render(request, 'farm/index.html', params)
