from django.conf.urls import url

from . import views

app_name = 'flocks'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^detail/(?P<flock_id>[0-9]+)', views.FlockDetailView.as_view(), name='detail'),
    # url(r'^create', views.create, name='create'),
    # url(r'^save', views.save, name='save'),
    #
    # url(r'animalexits/create', views.create_animal_exit, name='create_animal_exit'),
    # url(r'animalexits/save', views.save_animal_exit, name='save_animal_exit'),
    #
    # url(r'animaldeaths/create', views.create_animal_death, name='create_animal_death'),
    # url(r'animaldeaths/save', views.save_animal_death, name='save_animal_death'),
    #
    # url(r'^animalseparation/create', views.create_animal_separation, name='create_animal_separation'),
    # url(r'^animalseparation/save$', views.save_animal_separation, name='save_animal_separation'),
    # url(r'^animalseparation/detail/(?P<separation_id>[0-9]+)', views.view_animal_separation, name='separation_detail'),
    # url(r'^animalseparation/died', views.create_separation_death, name='make_animal_separation_died'),
    # url(r'^animalseparation/save_death', views.save_separation_death, name='save_separation_death'),
    # url(r'^animalseparation/exit', views.create_separation_exit, name='make_animal_separation_exit'),
    # url(r'^animalseparation/save_exit', views.save_separation_exit, name='save_separation_exit'),
]