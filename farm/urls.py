from django.conf.urls import url
from django.contrib.auth.decorators import login_required, permission_required

from .views import FarmIndexView, RegisterNewAnimalEntry, RegisterNewAnimalExit

app_name = 'farm'
urlpatterns = [
    url(r'^$', login_required(FarmIndexView.as_view()), name='index'),
    url(r'^register_incoming_animals', login_required(RegisterNewAnimalEntry.as_view()), name='animal_entry'),
    url(r'^register_outgoing_animals', login_required(RegisterNewAnimalExit.as_view()), name='animal_exit')
]