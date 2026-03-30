from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.conf import settings
import os
from datetime import datetime
from .models import ImageRecord, UserProfile
from .utils.yolo_detector import OfficeObjectDetector
from PIL import Image
import json
from django.contrib.auth import logout, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages

# 全局检测器实例
detector = OfficeObjectDetector()


# Superuser
# Username: admin
# Email address: (直接回车，留空)
# Password: (输入密码，不会显示，admin123456)


@login_required
def home(request):
    """
    个人中心首页视图函数
    """
    user = request.user

    # 获取统计信息
    total_detections = ImageRecord.objects.filter(user=user, detection_status='completed').count()
    today_detections = ImageRecord.objects.filter(
        user=user,
        detection_status='completed',
        detection_time__date=datetime.now().date()
    ).count()
    total_uploads = ImageRecord.objects.filter(user=user).count()

    # 获取最近5条识别记录
    recent_records = ImageRecord.objects.filter(
        user=user,
        detection_status='completed'
    )[:5]

    context = {
        'user': user,
        'total_detections': total_detections,
        'today_detections': today_detections,
        'total_uploads': total_uploads,
        'recent_records': recent_records,
    }

    return render(request, 'detector/home.html', context)


# def test_media_access(request):
#     """
#     测试媒体文件访问
#     """
#     import os
#     from django.http import HttpResponse, JsonResponse
#     from django.conf import settings
#
#     test_file = os.path.join(settings.MEDIA_ROOT, 'videos', 'results', 'test.txt')
#
#     # 创建测试文件
#     os.makedirs(os.path.dirname(test_file), exist_ok=True)
#     with open(test_file, 'w') as f:
#         f.write('如果能看到这个文件，说明媒体文件配置正确！')
#
#     test_url = '/media/videos/results/test.txt'
#
#     return HttpResponse(f"""
#     <html>
#     <head><title>媒体文件测试</title></head>
#     <body>
#         <h2>媒体文件访问测试</h2>
#         <p><strong>MEDIA_URL:</strong> {settings.MEDIA_URL}</p>
#         <p><strong>MEDIA_ROOT:</strong> {settings.MEDIA_ROOT}</p>
#         <p><strong>测试文件路径:</strong> {test_file}</p>
#         <p><strong>测试文件 URL:</strong> <a href="{test_url}" target="_blank">{test_url}</a></p>
#         <p><strong>文件存在:</strong> {os.path.exists(test_file)}</p>
#         <hr>
#         <p>请点击上面的测试文件 URL，如果能看到文字，说明 Django 媒体文件服务配置正确。</p>
#         <p><a href="/">返回首页</a></p>
#     </body>
#     </html>
#     """)

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
            # 创建用户资料
            UserProfile.objects.create(user=user)
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})


def user_logout(request):
    logout(request)
    return redirect('home')


@login_required
def upload_avatar(request):
    """上传头像"""
    if request.method == 'POST' and request.FILES.get('avatar'):
        avatar_file = request.FILES['avatar']

        # 验证文件类型
        allowed_types = ['image/jpeg', 'image/png', 'image/jpg']
        if avatar_file.content_type not in allowed_types:
            messages.error(request, '只支持 JPG、PNG 格式的图片')
            return redirect('home')

        # 验证文件大小（5MB）
        if avatar_file.size > 5 * 1024 * 1024:
            messages.error(request, '图片大小不能超过 5MB')
            return redirect('home')

        # 获取或创建用户资料
        profile, created = UserProfile.objects.get_or_create(user=request.user)

        # 删除旧头像文件（如果存在）
        if profile.avatar:
            if os.path.isfile(profile.avatar.path):
                os.remove(profile.avatar.path)

        # 保存新头像
        profile.avatar = avatar_file
        profile.save()

        messages.success(request, '头像上传成功！')
        return redirect('home')

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

        # 获取选择的模型
        selected_models = request.POST.getlist('selected_models')
        laptop_only = 'laptop' in selected_models and len(selected_models) == 1

        print(f"[UPLOAD] 文件名：{uploaded_file.name}")
        print(f"[UPLOAD] 文件大小：{uploaded_file.size} bytes")
        print(f"[UPLOAD] 选择的模型：{selected_models}")
        print(f"[UPLOAD] 仅笔记本模式：{laptop_only}")

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
            return render(request, 'upload.html', {'error': f'文件保存失败：{str(e)}'})

        # 创建图片记录
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
                detection_status='pending',
                selected_models=selected_models
            )

            print(f"[UPLOAD] ✓ 数据库记录创建成功！ID={image_record.id}")

        except Exception as e:
            print(f"[UPLOAD] ✗ 数据库记录创建失败：{e}")
            import traceback
            traceback.print_exc()
            return render(request, 'upload.html', {'error': f'无法保存记录：{str(e)}'})

        # 执行检测
        try:
            print(f"[UPLOAD] 开始执行 YOLO 检测...")
            start_time = datetime.now()
            print(f"[UPLOAD] 检测开始时间：{start_time}")

            # 根据选择的模型进行检测
            if laptop_only:
                print("[UPLOAD] 使用笔记本专用检测模式")
                result_img, detections, stats = detector.detect_laptop_only(original_path)
                result_filename = f"result_laptop_{timestamp}.jpg"
            elif selected_models:
                print(f"[UPLOAD] 使用指定模型检测：{selected_models}")
                result_img, detections, stats = detector.detect_with_models(original_path, selected_models)
                result_filename = f"result_models_{timestamp}.jpg"
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
                'mode': 'laptop_only' if laptop_only else ('custom' if selected_models else 'all')
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
                    'total_objects': len(detections),
                    'selected_models': selected_models
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

            return render(request, 'upload.html', {'error': error_message})

    print(f"[UPLOAD] 不是 POST 请求或没有上传文件，返回上传页面")
    return render(request, 'upload.html')


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
        'selected_models': record.selected_models,
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


# ==================== 视频上传检测功能 ====================
# @login_required(login_url='login')  # 已注释，用于测试
def upload_video(request):
    """
    视频上传并逐帧检测
    流程：上传视频 -> 拆分帧 -> YOLO 检测标注 -> 合成视频
    """
    print("=" * 60)
    print("[VIDEO] ========== 开始处理视频上传 ==========")
    print(f"[VIDEO] 请求方法：{request.method}")
    print(f"[VIDEO] FILES: {list(request.FILES.keys()) if request.FILES else '无'}")

    # GET 请求：显示上传页面
    if request.method == 'GET':
        return render(request, 'detector/video_upload.html')

    # POST 请求：处理视频上传
    try:
        # 1. 验证文件是否存在
        if 'video' not in request.FILES:
            error_msg = '请选择要上传的视频文件'
            print(f"[VIDEO] ✗ 错误：{error_msg}")
            return render(request, 'detector/video_upload.html', {'error': error_msg})

        uploaded_video = request.FILES['video']
        print(f"[VIDEO] 文件名：{uploaded_video.name}")
        print(f"[VIDEO] 文件大小：{uploaded_video.size} bytes")
        print(f"[VIDEO] 文件类型：{uploaded_video.content_type}")

        # 2. 验证文件大小（最大 100MB）
        max_size = 100 * 1024 * 1024
        if uploaded_video.size > max_size:
            error_msg = f'视频文件过大，最大允许 {max_size // (1024*1024)} MB'
            print(f"[VIDEO] ✗ 错误：{error_msg}")
            return render(request, 'detector/video_upload.html', {'error': error_msg})

        # 3. 验证文件扩展名
        allowed_ext = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
        ext = os.path.splitext(uploaded_video.name)[1].lower()
        if ext not in allowed_ext:
            error_msg = f'不支持的文件类型 {ext}，请上传 MP4/AVI/MOV/MKV/WEBM 格式'
            print(f"[VIDEO] ✗ 错误：{error_msg}")
            return render(request, 'detector/video_upload.html', {'error': error_msg})

        # 4. 生成时间戳和路径
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        temp_dir = None

        # 5. 保存原始视频
        video_dir = os.path.join(settings.MEDIA_ROOT, 'videos', 'uploads')
        os.makedirs(video_dir, exist_ok=True)
        original_filename = f"{timestamp}_{uploaded_video.name}"
        original_video_path = os.path.join(video_dir, original_filename)

        print(f"[VIDEO] 保存原始视频到：{original_video_path}")
        with open(original_video_path, 'wb+') as f:
            for chunk in uploaded_video.chunks():
                f.write(chunk)
        print(f"[VIDEO] ✓ 原始视频保存成功")

        # 6. 准备输出视频路径
        result_dir = os.path.join(settings.MEDIA_ROOT, 'videos', 'results')
        os.makedirs(result_dir, exist_ok=True)
        output_filename = f"detected_{timestamp}.mp4"
        output_video_path = os.path.join(result_dir, output_filename)
        print(f"[VIDEO] 输出视频路径：{output_video_path}")

        # 7. 创建临时目录
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp', timestamp)
        os.makedirs(temp_dir, exist_ok=True)
        print(f"[VIDEO] 临时目录：{temp_dir}")

        # 8. 打开视频文件
        print("[VIDEO] 正在打开视频文件...")
        cap = cv2.VideoCapture(original_video_path)
        if not cap.isOpened():
            raise Exception("无法打开视频文件，请检查文件是否损坏或编码不受支持")

        # 9. 获取视频参数
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        print(f"[VIDEO] 视频参数：fps={fps}, 分辨率={width}x{height}, 总帧数={total_frames}")

        # 修正无效参数
        if fps <= 0:
            fps = 25
            print("[VIDEO] ⚠️ fps 无效，使用默认值 25")
        if width <= 0 or height <= 0:
            width, height = 640, 480
            print(f"[VIDEO] ⚠️ 分辨率无效，使用默认值 {width}x{height}")

        # 10. 创建视频写入器 - 使用最简单的配置
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

        if not out.isOpened():
            error_msg = "无法创建输出视频文件"
            print(f"[VIDEO] ✗ 错误：{error_msg}")
            print(f"[VIDEO] 输出路径：{output_video_path}")
            print(f"[VIDEO] 参数：fourcc=mp4v, fps={fps}, size={width}x{height}")
            raise Exception(error_msg)

        print(f"[VIDEO] ✓ 视频写入器创建成功")
        print(f"[VIDEO] 编码器：mp4v, FPS: {fps}, 分辨率：{width}x{height}")

        # 11. 逐帧处理 - 简化版本
        print("[VIDEO] 🚀 开始逐帧处理...")
        all_detections = []
        frame_count = 0
        start_time = datetime.now()

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1

            try:
                # 直接使用帧进行检测和写入，不保存临时文件
                # 调用检测器
                temp_frame_path = os.path.join(temp_dir, f"frame_{frame_count:06d}.jpg")
                cv2.imwrite(temp_frame_path, frame)

                result_img, detections, stats = detector.detect(temp_frame_path)
                all_detections.append(detections)

                # 写入标注后的帧
                out.write(result_img)

                # 删除临时文件
                if os.path.exists(temp_frame_path):
                    os.remove(temp_frame_path)

                if frame_count % 30 == 0:
                    elapsed = (datetime.now() - start_time).total_seconds()
                    print(f"[VIDEO] 进度：{frame_count}/{total_frames} 帧，耗时 {elapsed:.1f}s")

            except Exception as e:
                print(f"[VIDEO] ✗ 第 {frame_count} 帧失败：{e}")
                out.write(frame)
                continue

        print(f"[VIDEO] ✓ 处理完成，共 {frame_count} 帧")

        # 12. 释放资源
        cap.release()
        out.release()
        print("[VIDEO] ✓ 视频资源已释放")

        # 验证输出文件
        if not os.path.exists(output_video_path):
            raise Exception(f"输出视频文件不存在：{output_video_path}")

        output_size = os.path.getsize(output_video_path)
        print(f"[VIDEO] 📁 OpenCV 输出的视频大小：{output_size} bytes ({output_size / 1024 / 1024:.2f} MB)")

        if output_size == 0:
            raise Exception("输出视频文件大小为 0，处理失败")

        # 使用 OpenCV 验证
        test_cap = cv2.VideoCapture(output_video_path)
        if not test_cap.isOpened():
            print(f"[VIDEO] ✗ OpenCV 无法打开输出视频")
        else:
            test_frames = int(test_cap.get(cv2.CAP_PROP_FRAME_COUNT))
            test_fps = test_cap.get(cv2.CAP_PROP_FPS)
            test_cap.release()
            print(f"[VIDEO] ✓ OpenCV 验证成功：{test_frames} 帧，{test_fps} FPS")

        # 使用 ffmpeg 重新编码为浏览器兼容格式
        print(f"[VIDEO] 🎬 开始使用 ffmpeg 重新编码为浏览器兼容格式...")
        try:
            import subprocess

            final_output = output_video_path
            temp_output = output_video_path + '.reencoded.mp4'

            # ffmpeg 命令 - 使用 H.264 编码，yuv420p 像素格式
            cmd = [
                'ffmpeg',
                '-i', output_video_path,           # 输入文件
                '-c:v', 'libx264',                 # 视频编码器：H.264
                '-preset', 'medium',               # 编码速度预设
                '-crf', '23',                      # 质量 (0-51, 越小质量越高)
                '-pix_fmt', 'yuv420p',            # 像素格式（浏览器兼容关键）
                '-movflags', '+faststart',        # 支持边下载边播放
                '-c:a', 'aac',                     # 音频编码器
                '-b:a', '128k',                    # 音频比特率
                '-y',                              # 覆盖输出文件
                temp_output
            ]

            print(f"[VIDEO] 执行 ffmpeg 命令...")
            print(f"[VIDEO] {' '.join(cmd)}")

            # 执行 ffmpeg
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            stdout, stderr = process.communicate()

            if process.returncode == 0:
                # 检查新文件
                if os.path.exists(temp_output):
                    new_size = os.path.getsize(temp_output)
                    print(f"[VIDEO] ✅ ffmpeg 重新编码成功！")
                    print(f"[VIDEO] 📁 新文件大小：{new_size} bytes ({new_size / 1024 / 1024:.2f} MB)")

                    # 验证新文件
                    test_new = cv2.VideoCapture(temp_output)
                    if test_new.isOpened():
                        new_frames = int(test_new.get(cv2.CAP_PROP_FRAME_COUNT))
                        new_fps = test_new.get(cv2.CAP_PROP_FPS)
                        test_new.release()
                        print(f"[VIDEO] ✓ 新视频验证：{new_frames} 帧，{new_fps} FPS")

                        # 替换原文件
                        os.replace(temp_output, output_video_path)
                        print(f"[VIDEO] ✓ 已替换为重新编码的文件")
                    else:
                        print(f"[VIDEO] ✗ 警告：无法验证新视频")
                        if os.path.exists(temp_output):
                            os.remove(temp_output)
                else:
                    print(f"[VIDEO] ✗ ffmpeg 输出文件不存在")
            else:
                print(f"[VIDEO] ✗ ffmpeg 失败，返回码：{process.returncode}")
                print(f"[VIDEO] stderr: {stderr.decode('utf-8', errors='ignore')}")
                if os.path.exists(temp_output):
                    os.remove(temp_output)

        except FileNotFoundError:
            print(f"[VIDEO] ✗ ffmpeg 未找到，请确认已正确安装")
        except Exception as e:
            print(f"[VIDEO] ✗ ffmpeg 处理失败：{e}")
            import traceback
            traceback.print_exc()

        # 13. 清理临时目录
        if temp_dir and os.path.exists(temp_dir):
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            print("[VIDEO] ✓ 临时目录已清理")

        # 14. 汇总统计信息
        summary = {}
        for frame_dets in all_detections:
            for det in frame_dets:
                label = det.get('item', 'unknown')
                summary[label] = summary.get(label, 0) + 1

        print(f"[VIDEO] 📊 检测统计：{summary}")
        print(f"[VIDEO] ✅ 视频处理完成！")

        # 15. 返回结果页面
        context = {
            'original_video_url': f'/media/videos/uploads/{original_filename}',
            'result_video_url': f'/media/videos/results/{output_filename}',
            'summary': summary,
            'total_frames': frame_count,
            'processed_frames': len(all_detections),
            'debug_info': True,
            'file_exists': os.path.exists(output_video_path),
            'file_size': output_size,
            'absolute_result_path': output_video_path,
            'absolute_original_path': original_video_path,
            # 添加可访问性测试
            'media_url': settings.MEDIA_URL,
            'media_root': settings.MEDIA_ROOT,
        }

        print(f"[VIDEO] ========== 处理完成 ==========")
        print(f"[VIDEO] MEDIA_URL: {settings.MEDIA_URL}")
        print(f"[VIDEO] MEDIA_ROOT: {settings.MEDIA_ROOT}")
        print(f"[VIDEO] 原始视频：{original_video_path}")
        print(f"[VIDEO] 检测结果：{output_video_path}")
        print(f"[VIDEO] 文件存在：{os.path.exists(output_video_path)}")
        print(f"[VIDEO] 文件可读：{os.access(output_video_path, os.R_OK)}")

        # 测试 URL 是否能访问
        test_url = f'/media/videos/results/{output_filename}'
        print(f"[VIDEO] 测试 URL: {test_url}")

        return render(request, 'detector/video_result.html', context)

    except Exception as e:
        error_msg = f"视频处理失败：{str(e)}"
        print(f"[VIDEO] ✗ 严重错误：{error_msg}")
        import traceback
        traceback.print_exc()

        # 清理临时目录
        if temp_dir and os.path.exists(temp_dir):
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            print("[VIDEO] ✓ 临时目录已清理")

        return render(request, 'detector/video_upload.html', {'error': error_msg})


# ==================== 其他视图函数 ====================

