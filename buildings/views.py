from django.shortcuts import render

from .models import Building


class GroupData:
    def __init__(self, name):
        self.name = name
        self.rooms = []
        self.groups = {}


def index(request):
    buildings = Building.objects.all()
    return render(request, 'buildings/index.html', {'buildings': buildings})
