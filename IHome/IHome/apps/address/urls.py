from django.conf.urls import url, include
from . import views

urlpatterns = [
    url(r'^api/v1.0/areas/$', views.GetAreasview.as_view(), ),
]
