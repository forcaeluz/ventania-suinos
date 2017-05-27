from django.shortcuts import render

from .models import Building


def index(request):
    buildings = Building.objects.all()

    return render(request, 'buildings/index.html', {'buildings': buildings})
