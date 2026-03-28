from django.shortcuts import render

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.conf import settings
import os
from datetime import datetime
from .models import DetectionResult
from .utils.yolo_detector import OfficeObjectDetector
from PIL import Image
import json

# 全局检测器实例
detector = OfficeObjectDetector()


def home(request):
    """
    首页视图函数，显示上传图片的表单
    Author:
    Args:
        request(HttpRequest):Django的HttpRequest对象

    Returns:
        HttpResponse:返回渲染后的HTML页面

    """
    # return render(request, 'detector/home.html')


def upload_image(request):
    """
    上传图片并进行目标检测的视图函数
    Author:
    Args:
        request(HttpRequest):Django的HttpRequest对象

    Returns:
        HttpResponse:返回渲染后的HTML页面

    """
    # if request.method == 'POST' and request.FILES.get('image'):
    #     # 保存上传的图片
    #     uploaded_file = request.FILES['image']
    #
    #     # 生成日期路径
    #     date_path = datetime.now().strftime('%Y/%m/%d')
    #
    #     upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads', date_path)
    #     os.makedirs(upload_dir, exist_ok=True)
    #
    #     # 生成唯一文件名
    #     timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    #     original_filename = f"upload_{timestamp}_{uploaded_file.name}"
    #     original_path = os.path.join(upload_dir, original_filename)
    #
    #     # 保存原始图片
    #     with open(original_path, 'wb+') as destination:
    #         for chunk in uploaded_file.chunks():
    #             destination.write(chunk)
    #
    #     try:
    #         # 进行目标检测
    #         result_img, detections, stats = detector.detect(original_path)
    #
    #         # 保存结果图片
    #         result_dir = os.path.join(settings.MEDIA_ROOT, 'results', date_path)
    #         os.makedirs(result_dir, exist_ok=True)
    #
    #         result_filename = f"result_{timestamp}.jpg"
    #         result_path = os.path.join(result_dir, result_filename)
    #         detector.save_result_image(result_img, result_path)
    #
    #         # 返回正确的URL（包含日期路径）
    #         context = {
    #             'original_url': f'/media/uploads/{date_path}/{original_filename}',
    #             'result_url': f'/media/results/{date_path}/{result_filename}',
    #             'detections': detections,
    #             'stats': stats,
    #             'total': len(detections),
    #         }
    #
    #         return render(request, 'detector/result.html', context)
    #
    #     except Exception as e:
    #         error_message = f"检测失败: {str(e)}"
    #         return render(request, 'detector/home.html', {'error': error_message})
    #
    # return redirect('home')


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
    # result = get_object_or_404(DetectionResult, id=result_id)
    #
    # context = {
    #     'result': result,
    #     'original_url': settings.MEDIA_URL + str(result.original_image),
    #     'result_url': settings.MEDIA_URL + str(result.result_image),
    #     'detections': result.detection_data.get('detections', []),
    #     'stats': result.detection_data.get('statistics', {}),
    #     'total': result.detection_data.get('total_objects', 0),
    # }
    #
    # return render(request, 'detector/result.html', context)