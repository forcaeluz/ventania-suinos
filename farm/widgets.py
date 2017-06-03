from django.forms.widgets import Widget, ChoiceWidget
from django.utils.html import escape


from buildings.models import Room, RoomGroup, Building


class RoomSelectionWidget(ChoiceWidget):
    allow_multiple_selected = True
    add_id_index = True
    checked_attribute = {'checked': True}
    option_inherits_attrs = False
    input_type = 'checkbox'
    template_name = 'farm/room_selection_widget.html'
    room_template = ''
    room_group_template = ''

    def __init__(self, attrs=None, choices=()):
        print(choices)
        super().__init__(attrs)
        self.room_groups = None

    def create_room_tree(self, value):
        choices = self.choices.queryset.all()
        if value is None:
            value = []

        room_groups = {}
        for room in choices:
            group_info = room_groups.get(room.group.id, self.GroupData(room.group.name))
            group_info.rooms.append(room)
            if str(room.id) in value:
                group_info.collapsed = False
            room_groups.update({room.group.id: group_info})

        changed = True
        while changed:
            changed = False
            keys = list(room_groups.keys())
            for group_id in keys:
                group = RoomGroup.objects.get(id=group_id)
                if group.group is not None:
                    changed = True
                    group_info = room_groups.get(group.group.id, self.GroupData(group.group.name))
                    group_info.groups.update({group_id: room_groups.get(group_id, None)})
                    room_groups.update({group.group.id: group_info})
                    room_groups.pop(group_id)

        for key, group in room_groups.items():
            group.collapsed = False
        self.room_groups = room_groups

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        self.create_room_tree(value)
        context.update({'groups': self.room_groups})
        return context

    class GroupData:
        def __init__(self, name):
            self.name = name
            self.collapsed = True
            self.rooms = []
            self.groups = {}

    class RoomData:
        def __init__(self, name, id):
            self.id = id
            self.name = name
            self.checked = False