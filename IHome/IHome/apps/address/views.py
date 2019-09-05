from django import http
from django.shortcuts import render

# Create your views here.
from django.views import View

from address.models import Area
from utils.response_code import RET


class GetAreasview(View):
    def get(self,request):
        try:
           areas =  Area.objects.all()
        except BaseException as e:
            return http.JsonResponse({"errno": RET.DATAERR, "errmsg": "获取用户信息失败", })
        area_list = []
        for area in areas:
            area_list.append({
                'aid':area.id,
                'aname':area.name,
            })
        return http.JsonResponse({'errno': RET.OK, 'errmsg': "OK",'data':area_list})

