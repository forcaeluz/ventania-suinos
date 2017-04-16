from django import template

register = template.Library()


@register.inclusion_tag('bootstrap/form.html')
def show_form(form_data):
    return form_data