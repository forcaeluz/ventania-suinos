from django.contrib import admin
from .models import Room, Building, RoomGroup, Silo, AnimalRoomEntry, AnimalRoomExit
# Register your models here.

admin.site.register(Room)
admin.site.register(RoomGroup)
admin.site.register(Building)
admin.site.register(Silo)
admin.site.register(AnimalRoomEntry)
admin.site.register(AnimalRoomExit)


