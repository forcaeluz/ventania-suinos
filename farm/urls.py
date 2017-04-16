from django.conf.urls import url
from django.contrib.auth.decorators import login_required, permission_required

from .views import FarmIndexView

app_name = 'farm'
urlpatterns = [
    url(r'^$', login_required(FarmIndexView.as_view()), name='index'),
]