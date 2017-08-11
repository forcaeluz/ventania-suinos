from django.test import TestCase
from django.template import Template, Context

from .models import Kpi


class KpiTest(TestCase):
    TEMPLATE = Template("{% load kpi %} {% kpi kpi_data %}")

    def test_normal_case(self):
        kpi = Kpi()
        kpi.value = 'KpiValue'
        rendered = self.TEMPLATE.render(Context({'kpi_data': kpi}))
        self.assertIn('KpiValue', rendered)
