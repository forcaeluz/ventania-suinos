from django.contrib import admin
from .models import Room, Building, RoomGroup, Silo
# Register your models here.

admin.site.register(Room)
admin.site.register(RoomGroup)
admin.site.register(Building)
admin.site.register(Silo)