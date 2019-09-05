
from django.conf.urls import url,include
from  . import views


urlpatterns = [
url(r'^(?P<file_name>.*?\.html$)', views.get_html_file, ),
url(r'^$', views.index, ),
url(r'^api/v1.0/user/register/$', views.RegisterView.as_view(), ),
url(r'^api/v1.0/login/$', views.LoginView.as_view(), ),
url(r'^api/v1.0/logout/$', views.logoutView.as_view(), ),
url(r'^api/v1.0/session/$', views.GetSessionView.as_view(), ),
url(r'^api/v1.0/user/profile/$', views.UserInfoView.as_view(), ),
url(r'^api/v1.0/user/avatar/$', views.UpImgFileView.as_view(), ),
url(r'^api/v1.0/user/auth/$', views.PerfectUserView.as_view(), ),

]
