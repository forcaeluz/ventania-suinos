from django import template


register = template.Library()


@register.inclusion_tag('buildings/progressbar.html')
def room_occupancy_bar(room):
    return {'name': room.name,
            'occupancy': room.occupancy,
            'capacity': room.capacity,
            'overcapacity': room.occupancy - room.capacity}


@register.inclusion_tag('buildings/room_group_occupancy.html')
def room_group_occupancy(group):
    return {'group': group}
