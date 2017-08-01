from django.conf.urls import url
from django.contrib.auth.decorators import login_required, permission_required

from .views import index, RoomDetailView
app_name = 'buildings'
urlpatterns = [
    url(r'^$', login_required(index), name='index'),
    url(r'^room/(?P<room_id>[0-9]+)', login_required(RoomDetailView.as_view()), name='room_detail'),
]