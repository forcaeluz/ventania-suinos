from django.conf.urls import url
from django.contrib.auth.decorators import login_required, permission_required

from .views import index, LinkExitsToRoomsView, LinkFlockEntriesToRoomsView, \
    LinkDeathsToRoomsView, LinkSeparationsToRoomsView, MigrationWizard
app_name = 'buildings'
urlpatterns = [
    url(r'^$', index, name='index'),
    url(r'^migrate_wizard$', MigrationWizard.as_view(), name='migration_wizard'),
    url(r'^migrate_entries$', LinkFlockEntriesToRoomsView.as_view(), name='flock_entries_to_rooms'),
    url(r'^migrate_exit$', LinkExitsToRoomsView.as_view(), name='animal_exit_to_rooms'),
    url(r'^migrate_death$', LinkDeathsToRoomsView.as_view(), name='animal_death_to_room'),
    url(r'^migrate_separation$', LinkSeparationsToRoomsView.as_view(), name='animal_separation_to_room'),
]