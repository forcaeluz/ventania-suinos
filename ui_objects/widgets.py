from django.forms import TextInput


class DatePickerWidget(TextInput):
    def __init__(self):
        attrs = {'class': 'datepicker'}
        super().__init__(attrs)

    class Media:
        css = {'all': ('https://ajax.googleapis.com/ajax/libs/jqueryui/1.12.1/themes/base/jquery-ui.css',)}
        js = ('https://ajax.googleapis.com/ajax/libs/jquery/1.12.1/jquery.min.js',
              'https://ajax.googleapis.com/ajax/libs/jqueryui/1.12.1/jquery-ui.min.js',
              'datepicker.js')

