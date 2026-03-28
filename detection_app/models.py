from django.db import models
from django.utils import timezone


class DetectionResult(models.Model):
    """
    检测结果模型

    original_image: 原始图片
    result_image: 检测结果图片
    upload_time: 上传时间
    """

    # original_image = models.ImageField(upload_to='uploads/')
    # result_image = models.ImageField(upload_to='results/')
    # upload_time = models.DateTimeField(default=timezone.now)

    def __str__(self):
        """
        返回检测结果的字符串表示
        Author:
        Returns:
            str: 检测结果的字符串表示

        """
        # return f"检测 {self.id}"