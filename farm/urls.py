from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from .views import FarmIndexView, RegisterNewAnimalSeparation,  DeleteDeath, EditAnimalSeparation, DeleteSeparation, \
    DeleteAnimalEntry, DeleteExit, RegisterFeedTransition, FeedEntryView
from .wizards import RegisterNewAnimalEntry, RegisterNewAnimalExit, RegisterNewAnimalDeath, RegisterSingleAnimalExit, \
    EditAnimalEntry, EditAnimalDeath


app_name = 'farm'
urlpatterns = [
    url(r'^$', login_required(FarmIndexView.as_view()), name='index'),
    url(r'^new_animal_entry', login_required(RegisterNewAnimalEntry.as_view()), name='new_animal_entry'),
    url(r'^edit_animal_entry/(?P<flock_id>[0-9]+)', login_required(EditAnimalEntry.as_view()), name='edit_animal_entry'),
    url(r'^delete_group_entry/(?P<flock_id>[0-9]+)', login_required(DeleteAnimalEntry.as_view()), name='delete_animal_entry'),
    url(r'^register_group_exit', login_required(RegisterNewAnimalExit.as_view()), name='animal_exit'),
    url(r'^delete_animal_exit/(?P<exit_id>[0-9]+)', login_required(DeleteExit.as_view()), name='delete_animal_exit'),
    url(r'^register_animal_death', login_required(RegisterNewAnimalDeath.as_view()), name='animal_death'),
    url(r'^edit_animal_death/(?P<death_id>[0-9]+)', login_required(EditAnimalDeath.as_view()), name='edit_animal_death'),
    url(r'^delete_death/(?P<death_id>[0-9]+)', login_required(DeleteDeath.as_view()), name='delete_animal_death'),
    url(r'^new_animal_separation', login_required(RegisterNewAnimalSeparation.as_view()), name='new_animal_separation'),
    url(r'^edit_animal_separation/(?P<separation_id>[0-9]+)', login_required(EditAnimalSeparation.as_view()), name='edit_animal_separation'),
    url(r'^delete_separation/(?P<separation_id>[0-9]+)', login_required(DeleteSeparation.as_view()), name='delete_animal_separation'),
    url(r'^register_single_exit', login_required(RegisterSingleAnimalExit.as_view()), name='single_animal_exit'),
    url(r'^register_feed_transition', login_required(RegisterFeedTransition.as_view()), name='new_feed_transition'),
    url(r'^register_feed_entry', login_required(FeedEntryView.as_view()), name='new_feed_entry')
]