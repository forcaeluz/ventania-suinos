from django.forms import TextInput


class DatePickerWidget(TextInput):
    def __init__(self):
        attrs = {'class': 'datepicker', 'data-provide': 'datepicker-inline', 'data-date-format': "yyyy-mm-dd"}
        super().__init__(attrs)

    class Media:
        css = {'all': ('https://ajax.googleapis.com/ajax/libs/jqueryui/1.12.1/themes/base/jquery-ui.css',)}

