from django import template

register = template.Library()


@register.inclusion_tag('kpi.html')
def kpi(kpi_info):
    return {'kpi': kpi_info}