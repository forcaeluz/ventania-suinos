from django.conf.urls import url
from django.contrib.auth.decorators import login_required, permission_required

from .views import FarmIndexView, RegisterNewAnimalEntry, RegisterNewAnimalExit, RegisterNewAnimalDeath, \
    RegisterNewAnimalSeparation, RegisterSingleAnimalExit, EditAnimalEntry, EditAnimalDeath, EditAnimalSeparation

app_name = 'farm'
urlpatterns = [
    url(r'^$', login_required(FarmIndexView.as_view()), name='index'),
    url(r'^register_group_entry', login_required(RegisterNewAnimalEntry.as_view()), name='animal_entry'),
    url(r'^edit_group_entry/(?P<flock_id>[0-9]+)', login_required(EditAnimalEntry.as_view()), name='edit_animal_entry'),
    url(r'^edit_animal_death/(?P<death_id>[0-9]+)', login_required(EditAnimalDeath.as_view()), name='edit_animal_death'),
    url(r'^register_group_exit', login_required(RegisterNewAnimalExit.as_view()), name='animal_exit'),
    url(r'^register_animal_death', login_required(RegisterNewAnimalDeath.as_view()), name='animal_death'),
    url(r'^register_animal_separation', login_required(RegisterNewAnimalSeparation.as_view()), name='animal_separation'),
    url(r'^edit_animal_separation/(?P<separation_id>[0-9]+)', login_required(EditAnimalSeparation.as_view()), name='edit_animal_separation'),
    url(r'^register_single_exit', login_required(RegisterSingleAnimalExit.as_view()), name='single_animal_exit'),
]