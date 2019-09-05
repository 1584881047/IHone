
from django.conf.urls import url,include
from  . import views


urlpatterns = [
    url(r'^api/v1.0/houses/$', views.UphouseInfoView.as_view(), ),
    url(r'^api/v1.0/user/houses/$', views.MyhouseListView.as_view(), ),
    url(r'^api/v1.0/houses/index/$', views.HouseIndexView.as_view(), ),
    url(r'^api/v1.0/houses/search/$', views.SearchHouseView.as_view(), ),
    url(r'^api/v1.0/houses/(?P<house_id>\d+)/$', views.HouseDetailView.as_view(), ),
    url(r'^api/v1.0/houses/(?P<house_id>\d+)/images/$', views.UpHouseImgFileView.as_view(), ),

]
