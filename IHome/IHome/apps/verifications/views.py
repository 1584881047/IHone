import json
import random

from django.shortcuts import render

# Create your views here.


from django.http import JsonResponse, HttpResponse
from django.shortcuts import render

# Create your views here.
from django.views import View
from django_redis import get_redis_connection

from IHome.libs.captcha.captcha import captcha

from utils import response_code

from celery_tasks.sms.tasks import ccp_send_sms_code


class ImageCodeView(View):
    def get(self, request):
        """

        :param request:
        :param uuid: 唯一标识
        :return:  图片

        """
        uuid = request.GET.get('cur')
        per_uuid = request.GET.get('pre')
        # 获取图片验证码
        text, image = captcha.generate_captcha()
        # 链接django-redis 数据库
        redis_conn = get_redis_connection('verify_code')

        # 存入redis 数据
        redis_conn.setex('img_%s' % uuid, 300, text)
        print(text,uuid)

        return HttpResponse(image, content_type='imgae/jpg')


class SMSCodeView(View):
    def post(self, request):
        """
        校验图形验证码,并且发送短信
        :param request:
        :param SMSCodeView:
        :return:
        """
        # 获取参数
        requet_data =json.loads( request.body.decode())
        mobile = requet_data.get('mobile')
        image_code_cli = requet_data.get('image_code')
        uuid = requet_data.get('image_code_id')

        # 非空校验
        if not all([image_code_cli, image_code_cli]):
            return JsonResponse(
                {'code': response_code.RET.DATAERR, 'errmsg': '必传参数不能为空'})

        # 链接数据库
        redis_conn = get_redis_connection('verify_code')

        # 取出数据
        image_code_ser = redis_conn.get('img_%s' % uuid)

        # 校验数据
        if image_code_ser is None:
            return JsonResponse(
                {'code': response_code.RET.DATAERR, 'errmsg': '图片验证码过时'})

        print(image_code_cli, uuid)
        print(image_code_ser.decode(), uuid)
        # 校验验证码
        if image_code_cli.lower() != image_code_ser.decode().lower():
            return JsonResponse(
                {'code': response_code.RET.DATAERR, 'errmsg': '图形验证码不一致'})



        # 删除验证码
        try:
            redis_conn.delete('img_%s' % uuid)
        except BaseException as e:
            print(e)

        return self.send_sms_code(mobile)

    def send_sms_code(self, mobile):
        """
        发送验证码
        :param mobile: 手机号
        :return:
        """
        # 链接数据库
        redis_conn = get_redis_connection('verify_code')
        # 校验频繁发送
        send_flag= redis_conn.get('sms_flag_%s' % mobile)
        if send_flag:
            return JsonResponse(
                {'code': response_code.RET.REQERR, 'errmsg': '请勿频繁操作'})
        # 生成随机验证码
        sms_code = '%06d' % random.randint(0, 999999)
        print(sms_code)

        # 保存短信验证码
        pl = redis_conn.pipeline()
        pl.setex('sms_code_%s' % mobile, 300, sms_code)
        pl.setex('sms_flag_%s' % mobile, 60, 1)
        pl.execute()


        # 发送短信验证码
        # celery 用delay 去调用,开启异步
        ccp_send_sms_code.delay(mobile,sms_code)

        return JsonResponse(
            {'code': response_code.RET.OK, 'errmsg': 'OK'})