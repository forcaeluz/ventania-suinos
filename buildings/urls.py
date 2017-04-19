from django.conf.urls import url
from django.contrib.auth.decorators import login_required, permission_required

from .views import index
app_name = 'buildings'
urlpatterns = [
    url(r'^$', index, name='index'),
]