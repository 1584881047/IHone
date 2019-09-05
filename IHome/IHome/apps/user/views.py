import json
import re
from urllib.parse import urlencode

from django import http
from django.db import DatabaseError
from django.shortcuts import redirect
from django.views import View
from django_redis import get_redis_connection
from django.contrib.auth import login, logout, authenticate

from user.models import User
from user.utils import LoginRequiredMixin, checkIdcard
from utils.qiniu.main import _upload_to_qiniu
from utils.response_code import RET


def get_html_file(request, file_name):
    if file_name != 'favicon.ico':
        file_name = '/static/html/' + file_name
    params = request.GET
    if params:
        result = urlencode(params)
        return redirect(file_name + '?{}'.format(result))
    return redirect(file_name)


def index(request):
    return redirect('/static/html/index.html')


class LoginView(View):

    def post(self, request):
        # 获取参数
        request_data = json.loads(request.body.decode())

        mobile = request_data.get('mobile')
        password = request_data.get('password')

        # 非空校验
        if not all([mobile, password]):
            return http.HttpResponseForbidden('缺少必传参数')
        # 判断格式
        if not re.match(r'^1[3456789]\d{9}$', mobile):
            return http.HttpResponseForbidden('用户名格式不正确')

        if not re.match(r'^[a-zA-Z0-9_-]{8,20}$', password):
            return http.HttpResponseForbidden('密码格式不正确')
        user = authenticate(username=mobile, password=password)
        if user is None:
            return http.JsonResponse({'errno': RET.LOGINERR, 'errmsg': "用户或者密码有误"})
        login(request, user)
        return http.JsonResponse({'errno': RET.OK, 'errmsg': "登录成功"})


class logoutView(View):
    def delete(self, request):
        if not request.user.is_authenticated:
            return http.JsonResponse({'errno': RET.SESSIONERR, 'errmsg': " 用户未登录"})
        logout(request)
        response = http.JsonResponse({'errno': RET.OK, 'errmsg': "退出成功"})
        response.delete_cookie('username')
        return response


class RegisterView(View):
    """用户注册"""

    def post(self, request):
        """
        注册用户
        :param request: 请求对象
        :return:
        """
        request_data = json.loads(request.body.decode())

        mobile = request_data.get('mobile')
        password2 = request_data.get('password2')
        password = request_data.get('password')
        phonecode = request_data.get('phonecode')

        # 非空校验
        if not all([mobile, password, password2, phonecode]):
            return http.HttpResponseForbidden('必传参数不能为空')
        # 参数校验
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden('请输入8-20位的密码')
        if password != password2:
            return http.HttpResponseForbidden('两次输入的密码不一致')
        if not re.match(r'^1[345789]\d{9}$', mobile):
            return http.HttpResponseForbidden('手机号码格式不正确')

        # 获取短信验证码
        redis_conn = get_redis_connection('verify_code')
        sms_code_ser = redis_conn.get('sms_code_%s' % mobile).decode()
        if sms_code_ser != phonecode:
            return http.HttpResponseForbidden('短信验证码有误')

        # 保存数据库
        try:
            user = User.objects.create_user(password=password, mobile=mobile, username=mobile)
        except DatabaseError:
            return http.JsonResponse({'errno': RET.ROLEERR, 'errmsg': "注册失败"})
        # # 会话保持
        login(request, user)
        # # 保存用户名草cookie
        response = http.JsonResponse({'errno': RET.OK, 'errmsg': "注册成功"})
        response.set_cookie('username', user.username, max_age=3600 * 24 * 7)
        # 重定向到首页
        return http.JsonResponse({'errno': RET.OK, 'errmsg': "注册成功"})


class GetSessionView(View):
    def get(self, request):
        user = request.user
        try:
            user = User.objects.get(id=user.id)
        except:
            return http.JsonResponse({"errno": "0", "errmsg": "OK", "data": {"user_id": '', "name": ""}})

        return http.JsonResponse({"errno": "0", "errmsg": "OK", "data": {"user_id": user.id, "name": user.username}})


class UserInfoView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        try:
            user = User.objects.get(id=user.id)
        except BaseException as e:
            return http.JsonResponse({"errno": RET.DATAERR, "errmsg": "获取用户信息失败", })

        return http.JsonResponse({"errno": RET.OK, "errmsg": "OK",
                                  "data": {"name": user.username, "avatar_url": user.avatar_url,
                                           "mobile": user.mobile}})

    def post(self, request):
        name = json.loads(request.body.decode()).get('name')
        user = request.user
        try:
            user = User.objects.get(id=user.id)
            user.username = name
            user.save()
        except BaseException as e:
            print(e)
            return http.JsonResponse({'errno': RET.IOERR, 'errmsg': "修改用户姓名失败"})
        login(request, user)
        return http.JsonResponse({'errno': RET.OK, 'errmsg': "OK"})


class UpImgFileView(LoginRequiredMixin, View):
    def post(self, request):
        file = request.FILES.get('avatar')
        if not file:
            return http.JsonResponse({'errno': RET.PARAMERR, 'errmsg': "必传参数不能为空"})

        file_name = 'user_avatar_url_%s'% request.user.id
        url = _upload_to_qiniu(file,file_name)
        request.user.avatar_url = url
        request.user.save()
        data = {
            'name':request.user.username,
            'avatar_url':request.user.avatar_url,
            'mobile':request.user.mobile
        }
        return http.JsonResponse({'errno': RET.OK, 'errmsg': "OK",'data':data})


class PerfectUserView(LoginRequiredMixin, View):

    def get(self, request):
        try:
            user = User.objects.get(id=request.user.id)
        except:
            return http.JsonResponse({'errno': RET.USERERR, 'errmsg': "用户不存在或未激活"})

        return http.JsonResponse(
            {'errno': RET.OK, 'errmsg': "OK", "data": {'real_name': user.real_name, 'id_card': user.id_card}})



    def post(self, request):
        request_data = json.loads(request.body.decode())
        real_name = request_data.get('real_name')
        id_card = request_data.get('id_card')
        if not all([real_name, id_card]):
            return http.JsonResponse({'errno': RET.PARAMERR, 'errmsg': "必传参数不能为空"})

        check_id_flag = checkIdcard(id_card)
        if not check_id_flag:
            return http.JsonResponse({'errno': RET.PARAMERR, 'errmsg': "证件号不合法"})
        if not re.match(r'^[\u4E00-\u9FA5]{2,4}$', real_name):
            return http.JsonResponse({'errno': RET.PARAMERR, 'errmsg': "姓名不合法"})

        try:
            user = User.objects.get(id=request.user.id)
            user.real_name = real_name
            user.id_card = id_card
            user.save()

        except:
            return http.JsonResponse({'errno': RET.USERERR, 'errmsg': "用不信息更新失败"})

        return http.JsonResponse({'errno': RET.OK, 'errmsg': "OK"})
