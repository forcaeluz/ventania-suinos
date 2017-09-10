from django.shortcuts import render, get_object_or_404, HttpResponseRedirect, reverse
from django.views.generic import TemplateView
from .models import Building, Room, FeedType


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

    """Class view for detailed information about a building."""

    template_name = 'buildings/building.html'

    def get_context_data(self, **kwargs):
        """Get the context data for the building view.

        :param kwargs:
        :return:
        """
        context_data = super().get_context_data(**kwargs)
        building = get_object_or_404(Building, id=self.kwargs['building_id'])
        feed_types = FeedType.objects.all()
        context_data.update({'building': building, 'feed_types': feed_types})
        return context_data

