from django import forms
from django.utils.translation import ugettext as tr
from django.core.validators import ValidationError
from .models import AnimalRoomEntry, AnimalRoomExit
from .models import Room, DeathInRoom, AnimalSeparatedFromRoom
from flocks.models import Flock, AnimalExits, AnimalDeath, AnimalSeparation
