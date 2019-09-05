import json
import time

from django import http
import random
import string
from django.shortcuts import render

# Create your views here.
from django.views import View

from address.models import Area
from house.models import House, Facility, HouseImage
from utils.qiniu.main import _upload_to_qiniu
from utils.response_code import RET
from django.core.paginator import Paginator, EmptyPage


class MyhouseListView(View):
    def get(self, request):
        houses = House.objects.filter(user=request.user).order_by('-create_time')
        house_list = []
        for house in houses:
            house_list.append({
                'address': house.address,
                'area_name': house.area.name,
                'ctime': str(house.create_time).split(' ')[0],
                'house_id': house.id,
                'img_url': house.index_image_url,
                'order_count': house.order_count,
                'price': str(house.price),
                'room_count': house.room_count,
                'title': house.title,
                'user_avatar': house.user.avatar_url
            })

        return http.JsonResponse(
            {'errno': RET.OK, 'errmsg': "OK", "data": house_list})


class UphouseInfoView(View):

    def post(self, request):
        request_data = json.loads(request.body.decode())
        for (key, value) in request_data.items():
            if not value:
                return http.HttpResponseForbidden('缺少必传参数')

        try:
            area = Area.objects.get(id=request_data['area_id'])
        except BaseException as e:

            return http.JsonResponse({'errno': RET.PARAMERR, 'errmsg': "area_id参数有误"})

        try:
            facilities = Facility.objects.filter(id__in=request_data['facility'])
        except BaseException as e:
            print(e)
            return http.JsonResponse({'errno': RET.PARAMERR, 'errmsg': "facilities参数有误"})

        try:
            house = House.objects.create(
                user=request.user,
                area=area,
                deposit=request_data['deposit'],
                title=request_data['title'],
                price=request_data['price'],
                address=request_data['address'],
                room_count=request_data['room_count'],
                acreage=request_data['acreage'],
                unit=request_data['unit'],
                capacity=request_data['capacity'],
                beds=request_data['beds'],
                min_days=request_data['min_days'],
                max_days=request_data['max_days'],

            )

            house.facilities.add(*facilities)
            house.save()

        except BaseException as e:
            print(e)
            return http.JsonResponse({'errno': RET.ROLEERR, 'errmsg': "添加房源失败"})

        return http.JsonResponse({'errno': RET.OK, 'errmsg': "OK", 'data': {"house_id": house.id}})


class HouseDetailView(View):
    def get(self, request, house_id):

        try:
            house = House.objects.get(id=house_id)
        except BaseException as e:
            return http.JsonResponse({"errno": RET.DATAERR, "errmsg": "获取房源信息失败", })

        house_comments = []

        house_facilities = []
        facilities = Facility.objects.filter(house=house)
        for facility in facilities:
            house_facilities.append(facility.id)
        house_img_urls = []

        house_imgs = house.houseimage_set.all()
        for house_img  in house_imgs:
            house_img_urls.append(house_img.url)
        try:
            orders = house.order_set.all()
            for order in orders:
                house.comments.append(
                    {
                        'comment': order.comment,
                        'ctime': str(order.create_time).split(' ')[0],
                        'user_name': order.user.username,
                    }
                )
        except BaseException as e:
            pass

        house_data = {}
        house_data['house'] = {
            "acreage": house.acreage,
            "address": house.address,
            "beds": house.beds,
            "capacity": house.capacity,
            'comments': house_comments,
            "deposit": house.deposit,
            'facilities': house_facilities,
            "hid": house.id,
            'img_urls': house_img_urls,
            "max_days": house.max_days,
            "min_days": house.min_days,
            "price": house.price,
            "room_count": house.room_count,
            "title": house.title,
            "unit": house.unit,
            "user_avatar": house.user.avatar_url,
            "user_id": house.user.id,
            "user_name": house.user.username
        }
        house_data['user_id'] =request.user.id or -1

        return http.JsonResponse({'errno': RET.OK, 'errmsg': "OK", 'data': house_data})


class UpHouseImgFileView(View):
    def post(self, request, house_id):
        file = request.FILES.get('house_image')
        if not file:
            return http.JsonResponse({'errno': RET.PARAMERR, 'errmsg': "必传参数不能为空"})
        try:
            house = House.objects.get(id=house_id)
        except BaseException as e:
            return http.JsonResponse({'errno': RET.PARAMERR, 'errmsg': "id有误"})

        file_name = ''.join(random.sample(string.ascii_letters + string.digits, 8))
        url = _upload_to_qiniu(file, file_name)
        if not url:
            return http.JsonResponse({'errno': RET.DATAERR, 'errmsg': "保存图片错误"})
        try:
            HouseImage.objects.create(house=house, url=url)
            if not house.index_image_url:
                house.index_image_url = url
                house.save()
        except BaseException as e:
            print(e)
            return http.JsonResponse({'errno': RET.DATAERR, 'errmsg': "保存图片错误"})

        return http.JsonResponse({'errno': RET.OK, 'errmsg': "OK", 'data': {"url": url}})


class HouseIndexView(View):
    def get(self,request):
        houses = House.objects.all().order_by('-create_time')[:3]
        house_list = []
        for house in houses:
            house_list.append(
                {
                    'house_id':house.id,
                    'img_url':house.index_image_url,
                    'title':house.title
                }
            )

        return http.JsonResponse({'errno': RET.OK, 'errmsg': "OK", 'data': house_list})


class SearchHouseView(View):
    def get(self,request):
        request_data = request.GET.dict()
        for (key,value) in  request_data.items():
            if not value:
                return http.HttpResponseForbidden('缺少必传参数')

        aid = request_data['aid']
        sd = request_data['sd']
        ed = request_data['ed']
        sk = request_data['sk']
        p = request_data['p']




        house_list = []
        try:
            area = Area.objects.get(id = aid)
        except BaseException as e:
            print(e)
            return http.JsonResponse({'errno': RET.PARAMERR, 'errmsg': "aid参数有误"})

        houses = House.objects.filter(area = area).order_by('-create_time')
        for house in houses:
            h_sd = time.strptime((str(house.create_time).split(' ')[0]),'%Y-%m-%d')
            h_sd_list =list(h_sd)[:3]
            if house.max_days == 0:
                house_list.append(house)
            else:
                if h_sd_list[2]+int(house.max_days) > 30:
                    h_sd_list[2]-=30
                    h_sd_list[1]+=1
                    if  h_sd_list[1]>12:
                        h_sd_list[1]-=12
                        h_sd_list[0]+=1

                h_ed ='%s-%s-%s' % (h_sd_list[0],h_sd_list[1],h_sd_list[2]+int(house.max_days))
                if time.mktime(time.strptime(h_ed,'%Y-%m-%d')) >=time.mktime(time.strptime(ed,'%Y-%m-%d')):
                    house_list.append(house)
        paginator = Paginator(house_list, 2)
        # 获取每页商品数据
        try:
            houses = paginator.page(p)
        except EmptyPage:
            # 如果page_num不正确，默认给用户404
            return http.HttpResponseNotFound('empty page')
        # 获取列表页总页数
        total_page = paginator.num_pages
        data_list = {
            'houses':[],
            'total_page':total_page
        }
        for house in houses:
            data_list['houses'].append({
                'house_id':house.id,
                'order_count':house.order_count,
                'title':house.title,
                'ctime':house.create_time,
                'price':house.price,
                'address':house.address,
                'area_name': area.name,
                'room_count':house.room_count,
                'img_url':house.index_image_url,
                'user_avatar':house.user.avatar_url,
            })

        return http.JsonResponse({'errno': RET.OK, 'errmsg': "OK", 'data': data_list})


