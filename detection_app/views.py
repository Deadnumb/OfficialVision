from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.db.backends.base.base.BaseDatabaseWrapper import timezone
from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.conf import settings
import os
from datetime import datetime
from .models import DetectionResult, User
from .utils.auth import get_vip_remaining_days, is_vip
from .utils.yolo_detector import OfficeObjectDetector
from PIL import Image
import json
from django.contrib.auth import logout, login

# 全局检测器实例
detector = OfficeObjectDetector()
VIP_PACKAGES = [
    {'days': 6, 'price': 6, 'name': '6天VIP'},
    {'days': 30, 'price': 30, 'name': '30天VIP'},
    {'days': 365, 'price': 365, 'name': '365天VIP'},
    {'days': -1, 'price': 500, 'name': '永久VIP'},  # -1表示永久
]

def home(request):
    """
    首页视图函数，显示上传图片的表单
    Author:
    Args:
        request(HttpRequest):Django的HttpRequest对象

    Returns:
        HttpResponse:返回渲染后的HTML页面

    """
    return render(request, 'detector/home.html')



def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

# 注册
def user_register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})
def upload(request):
    return render(request, 'upload.html')  # 后面你可以创建 upload.html 作为上传页



def user_logout(request):
    logout(request)
    return redirect('home')  # 退出后跳回主页


def upload_image(request):
    """
    上传图片并进行目标检测的视图函数
    Author:
    Args:
        request(HttpRequest):Django 的 HttpRequest 对象

    Returns:
        HttpResponse:返回渲染后的 HTML 页面

    """
    if request.method == 'POST' and request.FILES.get('image'):
        uploaded_file = request.FILES['image']
        laptop_only = request.POST.get('laptop_only') == 'true'

        date_path = datetime.now().strftime('%Y/%m/%d')

        upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads', date_path)
        os.makedirs(upload_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        original_filename = f"upload_{timestamp}_{uploaded_file.name}"
        original_path = os.path.join(upload_dir, original_filename)

        with open(original_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        try:
            # 根据模式选择检测方法
            if laptop_only:
                result_img, detections, stats = detector.detect_laptop_only(original_path)
                result_filename = f"result_laptop_{timestamp}.jpg"
            else:
                result_img, detections, stats = detector.detect(original_path)
                result_filename = f"result_{timestamp}.jpg"

            result_dir = os.path.join(settings.MEDIA_ROOT, 'results', date_path)
            os.makedirs(result_dir, exist_ok=True)

            result_path = os.path.join(result_dir, result_filename)
            detector.save_result_image(result_img, result_path)

            context = {
                'original_url': f'/media/uploads/{date_path}/{original_filename}',
                'result_url': f'/media/results/{date_path}/{result_filename}',
                'detections': detections,
                'stats': stats,
                'total': len(detections),
                'mode': 'laptop_only' if laptop_only else 'all'
            }

            return render(request, 'detector/result.html', context)

        except Exception as e:
            error_message = f"检测失败：{str(e)}"
            return render(request, 'detector/home.html', {'error': error_message})

    return redirect('home')


def upload_image_laptop(request):
    """
    上传图片并仅检测笔记本电脑的视图函数
    Author:Young
    Args:
        request(HttpRequest):Django 的 HttpRequest 对象

    Returns:
        HttpResponse:返回渲染后的 HTML 页面

    """
    if request.method == 'POST' and request.FILES.get('image'):
        uploaded_file = request.FILES['image']

        date_path = datetime.now().strftime('%Y/%m/%d')

        upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads', date_path)
        os.makedirs(upload_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        original_filename = f"upload_laptop_{timestamp}_{uploaded_file.name}"
        original_path = os.path.join(upload_dir, original_filename)

        with open(original_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        try:
            result_img, detections, stats = detector.detect_laptop_only(original_path)

            result_dir = os.path.join(settings.MEDIA_ROOT, 'results', date_path)
            os.makedirs(result_dir, exist_ok=True)

            result_filename = f"result_laptop_{timestamp}.jpg"
            result_path = os.path.join(result_dir, result_filename)
            detector.save_result_image(result_img, result_path)

            context = {
                'original_url': f'/media/uploads/{date_path}/{original_filename}',
                'result_url': f'/media/results/{date_path}/{result_filename}',
                'detections': detections,
                'stats': stats,
                'total': len(detections),
                'mode': 'laptop_only'
            }

            return render(request, 'detector/result.html', context)

        except Exception as e:
            error_message = f"检测失败：{str(e)}"
            return render(request, 'detector/home.html', {'error': error_message})

    return redirect('home')

def show_result(request, result_id):
    """
    显示检测结果的视图函数
    Author:
    Args:
        request(HttpRequest):Django的HttpRequest对象
        result_id(int):检测结果的ID

    Returns:
        HttpResponse:返回渲染后的HTML页面

    """
    result = get_object_or_404(DetectionResult, id=result_id)

    context = {
        'result': result,
        'original_url': settings.MEDIA_URL + str(result.original_image),
        'result_url': settings.MEDIA_URL + str(result.result_image),
        'detections': result.detection_data.get('detections', []),
        'stats': result.detection_data.get('statistics', {}),
        'total': result.detection_data.get('total_objects', 0),
    }

    return render(request, 'detector/result.html', context)


def vip_page(request):
    """
    显示VIP页面
    Author:
    Args:
        request: HttpRequest对象

    Returns:
        HttpResponse: 返回渲染后的HTML页面
    """
    # 获取当前登录用户（根据你的登录逻辑调整）
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    user = User.objects.get(id=user_id)

    context = {
        'packages': VIP_PACKAGES,
        'is_vip': is_vip(user),
        'remaining_days': get_vip_remaining_days(user),
    }
    return render(request, 'detector/vip.html', context)


def vip_recharge(request, PERMANENT_VIP_DATE=None):
    """
    充值VIP的视图函数
    Author:
    Args:
        request(HttpRequest):Django的HttpRequest对象
        PERMANENT_VIP_DATE: 永久VIP的日期

    Returns:
        HttpResponse: 返回渲染后的HTML页面
    """
    if request.method != 'POST':
        return redirect('vip_page')

    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    user = User.objects.get(id=user_id)

    # 获取用户选择的套餐
    package_days = int(request.POST.get('package_days', 0))

    # 计算新的到期时间
    if package_days == -1:
        # 永久VIP
        new_expire = PERMANENT_VIP_DATE
    else:
        # 普通套餐：在当前到期时间基础上累加，或从当前时间开始
        if user.vip_expire_at and user.vip_expire_at > timezone.now():
            # VIP未过期，续费累加
            new_expire = user.vip_expire_at + timezone.timedelta(days=package_days)
        else:
            # VIP已过期或从未开通，从当前时间开始
            new_expire = timezone.now() + timezone.timedelta(days=package_days)

    # 更新用户VIP信息
    user.vip_expire_at = new_expire
    user.save()

    return redirect('vip_page')