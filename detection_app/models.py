from django.db import models
from django.utils import timezone


class DetectionResult(models.Model):
    """存储检测结果的简化模型"""
    original_image = models.ImageField(upload_to='uploads/')
    result_image = models.ImageField(upload_to='results/')
    upload_time = models.DateTimeField(default=timezone.now)

    # 移除detection_data字段
    # 或者如果您需要存储检测数据，但不想用JSONField：
    # detection_data = models.TextField(default='{}')  # 用文本字段存储JSON字符串

    def __str__(self):
        return f"检测 {self.id}"