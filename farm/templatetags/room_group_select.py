from django import template


register = template.Library()


@register.inclusion_tag('farm/room_group.html')
def display_room_group(widget, group_id, roomGroupInfo):
    print(roomGroupInfo)
    return {'id': group_id, 'widget': widget, 'group': roomGroupInfo}
