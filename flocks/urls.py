from django.conf.urls import url

from . import views

app_name = 'flocks'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^detail/(?P<flock_id>[0-9]+)', views.detail, name='detail'),
    url(r'^create', views.create, name='create'),
    url(r'^save', views.save, name='save'),
    url(r'animalexits/create', views.create_animal_exit, name='create_animal_exit'),
    url(r'animalexits/save', views.save_animal_exit, name='save_animal_exit'),
]