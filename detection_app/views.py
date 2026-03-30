from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.shortcuts import render
from .service import detection_service
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.conf import settings
import os
from datetime import datetime
from .models import ImageRecord
from .utils.yolo_detector import OfficeObjectDetector
from PIL import Image
import json
from django.contrib.auth import logout, login

# 全局检测器实例
detector = OfficeObjectDetector()

# Superuser
# Username: admin
# Email address: (直接回车，留空)
# Password: (输入密码，不会显示，admin123456)

def home(request):
    """
    首页视图函数，显示上传图片的表单
    Author:
    Args:
        request(HttpRequest):Django 的 HttpRequest 对象

    Returns:
        HttpResponse:返回渲染后的 HTML 页面

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

def user_logout(request):
    logout(request)
    return redirect('home')

def upload_image(request):
    """
    上传图片并进行目标检测的视图函数
    Author:
    Args:
        request(HttpRequest):Django 的 HttpRequest 对象

    Returns:
        HttpResponse:返回渲染后的 HTML 页面

    """
    print("=" * 60)
    print("[UPLOAD] 开始处理上传请求")
    print(f"[UPLOAD] 请求方法：{request.method}")
    print(f"[UPLOAD] 用户：{request.user if hasattr(request, 'user') else 'None'}")
    print(f"[UPLOAD] 用户已登录：{request.user.is_authenticated if hasattr(request, 'user') else 'False'}")

    # 检查用户是否登录
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        print("[UPLOAD] 用户未登录，重定向到登录页")
        return redirect('login')

    if request.method == 'POST' and request.FILES.get('image'):
        uploaded_file = request.FILES['image']
        laptop_only = request.POST.get('laptop_only') == 'true'

        print(f"[UPLOAD] 文件名：{uploaded_file.name}")
        print(f"[UPLOAD] 文件大小：{uploaded_file.size} bytes")
        print(f"[UPLOAD] 检测模式：{'仅笔记本' if laptop_only else '全物品'}")

        date_path = datetime.now().strftime('%Y/%m/%d')

        upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads', date_path)
        os.makedirs(upload_dir, exist_ok=True)

        print(f"[UPLOAD] 上传目录：{upload_dir}")

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        original_filename = f"upload_{timestamp}_{uploaded_file.name}"
        original_path = os.path.join(upload_dir, original_filename)

        print(f"[UPLOAD] 保存路径：{original_path}")

        try:
            with open(original_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            print(f"[UPLOAD] ✓ 文件保存成功")
        except Exception as e:
            print(f"[UPLOAD] ✗ 文件保存失败：{e}")
            import traceback
            traceback.print_exc()
            return render(request, 'detector/home.html', {'error': f'文件保存失败：{str(e)}'})

        # 创建图片记录（待检测状态）- 必须成功创建才能继续
        print(f"[UPLOAD] 准备创建数据库记录...")
        try:
            # 获取文件大小
            file_size = uploaded_file.size if hasattr(uploaded_file, 'size') else 0

            print(f"[UPLOAD] 创建 ImageRecord: user={request.user}, file={original_filename}")

            image_record = ImageRecord.objects.create(
                user=request.user,
                uploaded_image=f'uploads/{date_path}/{original_filename}',
                file_name=uploaded_file.name,
                file_size=file_size,
                detection_mode='laptop_only' if laptop_only else 'all',
                detection_status='pending'
            )

            print(f"[UPLOAD] ✓ 数据库记录创建成功！ID={image_record.id}")

        except Exception as e:
            print(f"[UPLOAD] ✗ 数据库记录创建失败：{e}")
            import traceback
            traceback.print_exc()
            return render(request, 'detector/home.html', {'error': f'无法保存记录：{str(e)}'})

        # 执行检测
        try:
            print(f"[UPLOAD] 开始执行 YOLO 检测...")
            start_time = datetime.now()
            print(f"[UPLOAD] 检测开始时间：{start_time}")

            # 根据模式选择检测方法
            if laptop_only:
                print("[UPLOAD] 使用笔记本专用检测模式")
                result_img, detections, stats = detector.detect_laptop_only(original_path)
                result_filename = f"result_laptop_{timestamp}.jpg"
            else:
                print("[UPLOAD] 使用全物品检测模式")
                result_img, detections, stats = detector.detect(original_path)
                result_filename = f"result_{timestamp}.jpg"

            result_dir = os.path.join(settings.MEDIA_ROOT, 'results', date_path)
            os.makedirs(result_dir, exist_ok=True)

            print(f"[UPLOAD] 结果目录：{result_dir}")

            result_path = os.path.join(result_dir, result_filename)
            print(f"[UPLOAD] 结果路径：{result_path}")

            detector.save_result_image(result_img, result_path)
            print(f"[UPLOAD] ✓ 结果图片保存成功")

            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()

            print(f"[UPLOAD] 检测完成时间：{end_time}")
            print(f"[UPLOAD] 处理耗时：{processing_time}秒")
            print(f"[UPLOAD] 检测到 {len(detections)} 个物体")

            context = {
                'original_url': f'/media/uploads/{date_path}/{original_filename}',
                'result_url': f'/media/results/{date_path}/{result_filename}',
                'detections': detections,
                'stats': stats,
                'total': len(detections),
                'mode': 'laptop_only' if laptop_only else 'all'
            }

            # 更新图片记录为已完成状态
            print(f"[UPLOAD] 准备更新数据库记录状态为 completed...")
            try:
                image_record.result_image = f'results/{date_path}/{result_filename}'
                image_record.detection_status = 'completed'
                image_record.detection_time = end_time
                image_record.total_objects = len(detections)
                image_record.detection_data = {
                    'detections': detections,
                    'statistics': stats,
                    'total_objects': len(detections)
                }
                image_record.processing_time = processing_time
                image_record.save()
                print(f"[UPLOAD] ✓ 数据库记录更新成功！ID={image_record.id}, 状态=completed")
            except Exception as e:
                print(f"[UPLOAD] ✗ 数据库记录更新失败：{e}")
                import traceback
                traceback.print_exc()

            print(f"[UPLOAD] ====== 上传检测流程全部完成 ======")
            return render(request, 'detector/result.html', context)

        except Exception as e:
            error_message = f"检测失败：{str(e)}"
            print(f"[UPLOAD] ✗ YOLO 检测异常：{error_message}")
            import traceback
            traceback.print_exc()

            # 更新记录状态为失败
            try:
                print(f"[UPLOAD] 尝试将记录标记为 failed...")
                image_record.detection_status = 'failed'
                image_record.notes = str(e)
                image_record.save()
                print(f"[UPLOAD] ✓ 记录已标记为失败")
            except Exception as update_error:
                print(f"[UPLOAD] ✗ 更新记录状态失败：{update_error}")

            return render(request, 'detector/home.html', {'error': error_message})

    print(f"[UPLOAD] 不是 POST 请求或没有上传文件，重定向到首页")
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
    # 检查用户是否登录
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        return redirect('login')

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

        # 创建图片记录（待检测状态）
        try:
            file_size = uploaded_file.size if hasattr(uploaded_file, 'size') else 0

            image_record = ImageRecord.objects.create(
                user=request.user,
                uploaded_image=f'uploads/{date_path}/{original_filename}',
                file_name=uploaded_file.name,
                file_size=file_size,
                detection_mode='laptop_only',
                detection_status='pending'
            )
            print(f"[UPLOAD] ✓ 笔记本检测记录创建成功！ID={image_record.id}")
        except Exception as e:
            print(f"[UPLOAD] ✗ 笔记本检测记录创建失败：{e}")
            import traceback
            traceback.print_exc()
            return render(request, 'detector/home.html', {'error': f'无法保存记录：{str(e)}'})

        try:
            start_time = datetime.now()
            result_img, detections, stats = detector.detect_laptop_only(original_path)

            result_dir = os.path.join(settings.MEDIA_ROOT, 'results', date_path)
            os.makedirs(result_dir, exist_ok=True)

            result_filename = f"result_laptop_{timestamp}.jpg"
            result_path = os.path.join(result_dir, result_filename)
            detector.save_result_image(result_img, result_path)

            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()

            context = {
                'original_url': f'/media/uploads/{date_path}/{original_filename}',
                'result_url': f'/media/results/{date_path}/{result_filename}',
                'detections': detections,
                'stats': stats,
                'total': len(detections),
                'mode': 'laptop_only'
            }

            # 更新图片记录为已完成状态
            try:
                image_record.result_image = f'results/{date_path}/{result_filename}'
                image_record.detection_status = 'completed'
                image_record.detection_time = end_time
                image_record.total_objects = len(detections)
                image_record.detection_data = {
                    'detections': detections,
                    'statistics': stats,
                    'total_objects': len(detections)
                }
                image_record.processing_time = processing_time
                image_record.save()
                print(f"[UPLOAD] ✓ 笔记本检测记录更新成功！ID={image_record.id}")
            except Exception as e:
                print(f"[UPLOAD] ✗ 笔记本检测记录更新失败：{e}")
                import traceback
                traceback.print_exc()

            return render(request, 'detector/result.html', context)

        except Exception as e:
            error_message = f"检测失败：{str(e)}"
            print(f"[UPLOAD] ✗ 笔记本检测异常：{error_message}")
            import traceback
            traceback.print_exc()
            try:
                image_record.detection_status = 'failed'
                image_record.notes = str(e)
                image_record.save()
                print(f"[UPLOAD] ✓ 笔记本检测记录已标记为失败")
            except Exception:
                pass
            return render(request, 'detector/home.html', {'error': error_message})

    return redirect('home')

def show_result(request, result_id):
    """
    显示检测结果的视图函数
    Author:
    Args:
        request(HttpRequest):Django 的 HttpRequest 对象
        result_id(int):检测结果的 ID

    Returns:
        HttpResponse:返回渲染后的 HTML 页面

    """
    record = get_object_or_404(ImageRecord, id=result_id)

    context = {
        'record': record,
        'original_url': settings.MEDIA_URL + str(record.uploaded_image),
        'result_url': settings.MEDIA_URL + str(record.result_image) if record.result_image else '',
        'detections': record.detection_data.get('detections', []),
        'stats': record.detection_data.get('statistics', {}),
        'total': record.total_objects,
        'mode': record.detection_mode,
    }

    return render(request, 'detector/result.html', context)

def upload_records(request):
    """
    显示用户上传记录的视图函数
    """
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        return redirect('login')

    page = int(request.GET.get('page', 1))
    page_size = 10
    search_query = request.GET.get('search', '')

    records = ImageRecord.objects.filter(user=request.user)

    if search_query:
        records = records.filter(file_name__icontains=search_query)

    total_records = records.count()
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_records = records[start_idx:end_idx]
    total_pages = (total_records + page_size - 1) // page_size

    context = {
        'records': paginated_records,
        'current_page': page,
        'total_pages': total_pages,
        'total_records': total_records,
        'search_query': search_query,
    }

    return render(request, 'upload_records.html', context)

def history(request):
    """
    显示历史检测记录的视图函数
    """
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        return redirect('login')

    page = int(request.GET.get('page', 1))
    page_size = 10
    search_query = request.GET.get('search', '')

    results = ImageRecord.objects.filter(
        user=request.user,
        detection_status='completed'
    )

    if search_query:
        results = results.filter(file_name__icontains=search_query)

    total_records = results.count()
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_results = results[start_idx:end_idx]
    total_pages = (total_records + page_size - 1) // page_size

    context = {
        'results': paginated_results,
        'current_page': page,
        'total_pages': total_pages,
        'total_records': total_records,
        'search_query': search_query,
        'settings': settings,
    }

    return render(request, 'history.html', context)