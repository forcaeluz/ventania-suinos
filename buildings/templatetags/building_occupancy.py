from django import template
from datetime import date

register = template.Library()


@register.inclusion_tag('buildings/tags/progressbar.html')
def room_occupancy_bar(room):
    """Template tag for the progress bar that shows room occupancy.

    :param room: The room
    :return: A dictionary used in the progressbar template.
    """
    return {'name': room.name,
            'occupancy': room.occupancy,
            'capacity': room.capacity,
            'overcapacity': room.occupancy - room.capacity}


@register.inclusion_tag('buildings/tags/room_group_occupancy.html')
def room_group_occupancy(group):
    """Template tag for the table for progress-bars for a room groupd.

    :param group: The room group.
    :return: A dict for the room-group used in the template.
    """
    return {'group': group}


@register.inclusion_tag('buildings/tags/feed_progressbar.html')
def feed_remains(feed_type, building):
    """Template tag for the progress bar for feed availability.

    :param feed_type: The feed type for which information is desired.
    :param building: The building.
    :return: A dict used in the template, with the usage/remaining information.
    """
    remaining = building.get_estimated_remaining_feed(at_date=date.today(), feed_type=feed_type)
    consumption = building.get_average_feed_consumption(at_date=date.today(), feed_type=feed_type)
    capacity = building.feed_capacity(feed_type)
    return {'name': feed_type.name,
            'capacity': capacity,
            'remaining': remaining,
            'consumption': consumption,
            'remaining_after_consumption': remaining - consumption
            }