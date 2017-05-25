from django.conf.urls import url
from django.contrib.auth.decorators import login_required, permission_required

from .views import FarmIndexView, RegisterNewAnimalEntry, RegisterNewAnimalExit, RegisterNewAnimalDeath, \
    RegisterNewAnimalSeparation, RegisterSingleAnimalExit

app_name = 'farm'
urlpatterns = [
    url(r'^$', login_required(FarmIndexView.as_view()), name='index'),
    url(r'^register_group_entry', login_required(RegisterNewAnimalEntry.as_view()), name='animal_entry'),
    url(r'^register_group_exit', login_required(RegisterNewAnimalExit.as_view()), name='animal_exit'),
    url(r'^register_animal_death', login_required(RegisterNewAnimalDeath.as_view()), name='animal_death'),
    url(r'^register_animal_separation', login_required(RegisterNewAnimalSeparation.as_view()), name='animal_separation'),
    url(r'^register_single_exit', login_required(RegisterSingleAnimalExit.as_view()), name='single_animal_exit'),
]