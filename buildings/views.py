from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView
from .models import Building, Room


class GroupData:
    def __init__(self, name):
        self.name = name
        self.rooms = []
        self.groups = {}


def index(request):
    buildings = Building.objects.all()
    return render(request, 'buildings/index.html', {'buildings': buildings})


class RoomDetailView(TemplateView):
    template_name = 'buildings/room_detail.html'

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        room = get_object_or_404(Room, id=self.kwargs['room_id'])
        context_data.update({'room': room})
        return context_data
