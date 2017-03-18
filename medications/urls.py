from django.conf.urls import url
from . import views


app_name = 'medications'

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^new_medication', views.new_medication, name='new_medication'),
    url(r'^save_medication', views.save_medication, name='save_medication'),
    url(r'^new_entry', views.new_entry, name='new_entry'),
    url(r'^save_entry', views.save_entry, name='save_entry'),
    url(r'new_treatment', views.new_treatment, name='new_treatment'),
    url(r'save_treatment', views.save_treatment, name='save_treatment'),
    url(r'new_application', views.new_application, name='new_application'),
    url(r'save_application', views.save_application, name='save_application')
]