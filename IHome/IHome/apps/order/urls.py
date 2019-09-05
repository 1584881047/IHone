
from django.conf.urls import url,include
from  . import views


urlpatterns = [
url(r'^api/v1.0/orders/$', views.GetOrderView.as_view(), ),
url(r'^api/v1.0/orders/comment/$', views.PushCommView.as_view(), ),



]
