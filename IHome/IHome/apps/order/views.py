import json
import time
from datetime import datetime

from django import http
from django.db import transaction
from django.shortcuts import render

# Create your views here.
from django.utils import timezone
from django.views import View

from house.models import House
from order.models import Order
from user.utils import LoginRequiredMixin
from utils.response_code import RET


class GetOrderView(LoginRequiredMixin, View):
    def get(self, request):
        role = request.GET.get('role')
        user = request.user
        if role == 'landlord':
            # 房东
            houses = House.objects.filter(user=user)
            orders = Order.objects.filter(house__in=houses).order_by('-create_time')
            pass
        elif role == 'custom':
            # 房客
            orders = Order.objects.filter(user=user).order_by('-create_time')
            pass
        else:
            return http.JsonResponse({'errno': RET.PARAMERR, 'errmsg': "role参数有误"})
        order_list = []
        for order in orders:
            order_list.append({
                "amount": order.amount,
                "comment": order.comment,
                "ctime": str(order.create_time).split(' ')[0],
                "days": order.days,
                "end_date": str(order.end_date).split(' ')[0],
                "img_url": order.house.index_image_url,
                "order_id": order.id,
                "start_date": str(order.begin_date).split(' ')[0],
                "status": order.status,
                "title": order.house.title
            })
        return http.JsonResponse(
            {'errno': RET.OK, 'errmsg': "OK", "data": {'orders': order_list}})

    def post(self, request):
        request_data = json.loads(request.body.decode())
        house_id = request_data['house_id']
        start_date = request_data['start_date']
        end_date = request_data['end_date']

        s_time = time.mktime(time.strptime(start_date, '%Y-%m-%d'))
        e_time = time.mktime(time.strptime(end_date, '%Y-%m-%d'))
        count = (e_time - s_time) / (3600 * 24)

        if not all([house_id, start_date, end_date]):
            return http.HttpResponseForbidden('缺少必传参数')

        try:
            house = House.objects.get(id=house_id)
        except BaseException as e:
            return http.JsonResponse({'errno': RET.NODATA, 'errmsg': "house_id参数有误"})

        # order_id = timezone.localtime().strftime('%Y%m%d%H%M%S') + ('%09d' % int(house_id))

        # 开启事物修改数据库
        with transaction.atomic():
            save_id = transaction.savepoint()
            try:
                order_info = Order.objects.create(
                    user=request.user,
                    house=house,
                    begin_date=datetime.strptime(start_date, '%Y-%m-%d'),
                    end_date=datetime.strptime(end_date, '%Y-%m-%d'),
                    days=int(count),
                    house_price=house.price,
                    amount=house.price * int(count),
                )
                house.order_count += 1
                house.save()
            except BaseException as e:
                print(e)
                transaction.savepoint_rollback(save_id)
                return http.JsonResponse({'errno': RET.ROLEERR, 'errmsg': "下单失败失败"})

        return http.JsonResponse(
            {'errno': RET.OK, 'errmsg': "OK", 'data': {'order_id': order_info.id}})

    def put(self, request):
        request_data = json.loads(request.body.decode())
        order_id = request_data.get('order_id')
        action = request_data.get('action')
        reason = request_data.get('reason')

        if not all([order_id, action]):
            return http.HttpResponseForbidden('缺少必传参数')

        try:
            order = Order.objects.get(id=order_id)
        except BaseException as e:
            return http.HttpResponseForbidden('订单号有误')

        if action == 'accept':
            # 接单
            order.status = 'WAIT_COMMENT'

        elif action == 'reject':
            # 拒接单
            if not reason:
                return http.HttpResponseForbidden('请填写拒接原因')
            order.status = 'REJECTED'
            order.comment = reason
        else:
            return http.HttpResponseForbidden('action参数有误')

        order.save()

        return http.JsonResponse(
            {'errno': RET.OK, 'errmsg': "OK"})


class PushCommView(LoginRequiredMixin, View):
    def put(self, request):
        request_data = json.loads(request.body.decode())
        order_id = request_data.get('order_id')
        comment = request_data.get('comment')

        try:
            order = Order.objects.get(id=order_id)
        except BaseException as e:
            return http.HttpResponseForbidden('order参数有误')

        if not comment:
            return http.JsonResponse({'errno': RET.PARAMERR, 'errmsg': "comment参数不能为空"})

        order.comment = comment

        order.status = 'COMPLETE'
        order.save()

        return http.JsonResponse(
            {'errno': RET.OK, 'errmsg': "OK"})
