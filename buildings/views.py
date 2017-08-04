from datetime import date

from django.shortcuts import render, get_object_or_404, HttpResponseRedirect, reverse
from django.views.generic import TemplateView
from .models import Building, Room, FeedType


class GroupData:
    def __init__(self, name):
        self.name = name
        self.rooms = []
        self.groups = {}


def index(request):
    buildings = Building.objects.all()
    if len(buildings) == 1:
        return HttpResponseRedirect(reverse('buildings:building_detail', kwargs={'building_id': buildings[0].id}))
    return render(request, 'buildings/index.html', {'buildings': buildings})


class RoomDetailView(TemplateView):
    template_name = 'buildings/room_detail.html'

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        room = get_object_or_404(Room, id=self.kwargs['room_id'])
        context_data.update({'room': room})
        return context_data


class BuildingDetailView(TemplateView):
    template_name = 'buildings/building.html'

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        building = get_object_or_404(Building, id=self.kwargs['building_id'])
        feed_types = self.__generate_feeding_data(building)
        context_data.update({'building': building, 'feed_types': feed_types})
        return context_data

    def __generate_feeding_data(self, building):
        data = []
        feed_types = FeedType.objects.all()
        for feed_type in feed_types:
            name = feed_type.name
            capacity = building.feed_capacity(feed_type)
            remaining = building.get_estimated_remaining_feed(date.today(), feed_type)
            consumption = building.get_average_feed_consumption(date.today(), feed_type)
            data.append({'name': name, 'capacity': capacity, 'remaining': remaining, 'consumption': consumption})

        return data
