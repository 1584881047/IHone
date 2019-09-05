
from django.conf.urls import url,include
from  . import views


urlpatterns = [
    url(r'^api/v1.0/imagecode/$', views.ImageCodeView.as_view(), ),
    url(r'^api/v1.0/smscode/$', views.SMSCodeView.as_view(), ),

]
