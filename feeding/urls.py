from django.conf.urls import url

from . import views

app_name = 'feeding'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^create_type', views.create_type, name='create_type'),
    url(r'^save_type', views.save_type, name='save_type'),
    url(r'^create_feed_entry', views.create_feed_entry, name='create_feed_entry'),
    url(r'^save_feed_entry', views.save_feed_entry, name='save_feed_entry'),
]