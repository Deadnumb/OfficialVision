from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class ImageRecord(models.Model):
    """
    图片记录模型
    整合了上传记录和检测结果，一张图片一条记录
    """
    DETECTION_STATUS_CHOICES = [
        ('pending', '待检测'),
        ('completed', '已完成'),
        ('failed', '检测失败'),
    ]

    DETECTION_MODE_CHOICES = [
        ('all', '全物品检测'),
        ('laptop_only', '仅笔记本检测'),
    ]

    # 外键关联到 Django 内置用户表
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户', related_name='image_records')

    # 上传信息
    uploaded_image = models.ImageField(upload_to='uploads/%Y/%m/%d/', verbose_name='上传图片')
    upload_time = models.DateTimeField(default=timezone.now, verbose_name='上传时间')
    file_size = models.BigIntegerField(default=0, verbose_name='文件大小 (字节)')
    file_name = models.CharField(max_length=255, blank=True, verbose_name='原始文件名')

    # 检测信息
    detection_status = models.CharField(max_length=20, choices=DETECTION_STATUS_CHOICES, default='pending',
                                        verbose_name='检测状态')
    detection_mode = models.CharField(max_length=20, choices=DETECTION_MODE_CHOICES, default='all',
                                      verbose_name='检测模式')
    result_image = models.ImageField(upload_to='results/%Y/%m/%d/', blank=True, null=True, verbose_name='识别结果图片')
    detection_time = models.DateTimeField(blank=True, null=True, verbose_name='检测时间')

    # 检测结果数据
    total_objects = models.IntegerField(default=0, verbose_name='物品总数')
    detection_data = models.JSONField(default=dict, blank=True, verbose_name='检测数据')
    processing_time = models.FloatField(default=0.0, verbose_name='处理耗时')
    selected_models = models.JSONField(default=list, blank=True, verbose_name='选择的模型')

    # 备注
    notes = models.TextField(blank=True, verbose_name='备注')

    class Meta:
        verbose_name = '图片记录'
        verbose_name_plural = '图片记录'
        ordering = ['-upload_time']

    def __str__(self):
        status_text = self.get_detection_status_display()
        return f"{self.user.username} 的图片记录 - {self.upload_time.strftime('%Y-%m-%d %H:%M')} ({status_text})"

    def is_detected(self):
        """判断是否已检测"""
        return self.detection_status == 'completed'


class UserProfile(models.Model):
    """用户资料模型"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/%Y/%m/', blank=True, null=True, verbose_name='头像')
    bio = models.TextField(blank=True, null=True, verbose_name='个人简介')
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='手机号')

    class Meta:
        verbose_name = '用户资料'
        verbose_name_plural = '用户资料'

    def __str__(self):
        return f"{self.user.username}的资料"