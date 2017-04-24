from django.conf.urls import url
from django.contrib.auth.decorators import login_required, permission_required

from .views import index, migrate, save_migrate
app_name = 'buildings'
urlpatterns = [
    url(r'^$', index, name='index'),
    url(r'^migrate$', migrate, name='migrate'),
    url(r'^save_migrate$', save_migrate, name='save_migrate'),
]