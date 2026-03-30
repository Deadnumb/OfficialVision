from django.conf import settings
import os
from datetime import datetime
from .utils.yolo_detector import OfficeObjectDetector


class DetectionService:
    """
    检测服务类
    负责处理图片上传、模型选择、检测和结果保存
    """

    def __init__(self):
        self.detector = OfficeObjectDetector()

    def process_image(self, uploaded_file, selected_models=None):
        """
        处理上传的图片并进行检测

        Args:
            uploaded_file: 上传的文件对象
            selected_models: 选择的模型列表，如 ['laptop', 'keyboard']，None 表示使用所有模型

        Returns:
            dict: 包含检测结果的上下文信息
        """
        date_path = datetime.now().strftime('%Y/%m/%d')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 保存上传的文件
        original_path = self._save_uploaded_file(uploaded_file, date_path, timestamp)

        # 执行检测
        if selected_models and len(selected_models) > 0:
            result_img, detections, stats = self.detector.detect_with_models(
                original_path, selected_models
            )
            mode_suffix = '_'.join(selected_models)
        else:
            result_img, detections, stats = self.detector.detect(original_path)
            mode_suffix = 'all'

        # 保存结果图片
        result_path = self._save_result_image(result_img, date_path, timestamp, mode_suffix)

        # 构建上下文
        context = {
            'original_url': f'/media/uploads/{date_path}/{os.path.basename(original_path)}',
            'result_url': f'/media/results/{date_path}/{os.path.basename(result_path)}',
            'detections': detections,
            'stats': stats,
            'total': len(detections),
            'mode': mode_suffix if selected_models else 'all',
            'selected_models': selected_models
        }

        return context

    def _save_uploaded_file(self, uploaded_file, date_path, timestamp):
        """保存上传的文件"""
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads', date_path)
        os.makedirs(upload_dir, exist_ok=True)

        original_filename = f"upload_{timestamp}_{uploaded_file.name}"
        original_path = os.path.join(upload_dir, original_filename)

        with open(original_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        return original_path

    def _save_result_image(self, result_img, date_path, timestamp, mode_suffix):
        """保存结果图片"""
        result_dir = os.path.join(settings.MEDIA_ROOT, 'results', date_path)
        os.makedirs(result_dir, exist_ok=True)

        result_filename = f"result_{mode_suffix}_{timestamp}.jpg"
        result_path = os.path.join(result_dir, result_filename)

        self.detector.save_result_image(result_img, result_path)

        return result_path


# 全局服务实例
detection_service = DetectionService()