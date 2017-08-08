from django import template
from datetime import date

register = template.Library()


@register.inclusion_tag('buildings/tags/progressbar.html')
def room_occupancy_bar(room):
    return {'name': room.name,
            'occupancy': room.occupancy,
            'capacity': room.capacity,
            'overcapacity': room.occupancy - room.capacity}


@register.inclusion_tag('buildings/tags/room_group_occupancy.html')
def room_group_occupancy(group):
    return {'group': group}


@register.inclusion_tag('buildings/tags/feed_progressbar.html')
def feed_remains(feed_type, building):
    remaining = building.get_estimated_remaining_feed(at_date=date.today(), feed_type=feed_type)
    consumption = building.get_average_feed_consumption(at_date=date.today(), feed_type=feed_type)
    capacity = building.feed_capacity(feed_type)
    return {'name': feed_type.name,
            'capacity': capacity,
            'remaining': remaining,
            'consumption': consumption,
            'remaining_after_consumption': remaining - consumption
            }