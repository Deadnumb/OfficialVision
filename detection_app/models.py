from django.db import models
from django.utils import timezone

PERMANENT_VIP_YEAR = 9999
PERMANENT_VIP_DATA = timezone.datetime(PERMANENT_VIP_YEAR,
                                       12,
                                       31,
                                       23,
                                       59,
                                       59
                                       )


class User(models.Model):
    """
    用户模型
    存储用户的注册信息和登录凭证
    """
    # 显示用名称，可重复
    username = models.CharField(max_length=50, verbose_name='用户名')
    # 登录用账号，必须唯一
    account = models.CharField(max_length=50, unique=True, verbose_name='账号')
    # 加密后的密码
    password = models.CharField(max_length=128, verbose_name='密码')
    # 注册时间
    created_at = models.DateTimeField(default=timezone.now, verbose_name='注册时间')
    # VIP到期时间
    vip_expire_at = models.DateTimeField(null=True, blank=True, verbose_name='VIP到期时间')

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户'

    def __str__(self):
        return f"{self.username}({self.account})"


class DetectionResult(models.Model):
    """
    检测记录模型
    存储用户的检测记录，关联到用户表
    """
    # 外键关联到用户表，on_delete=CASCADE表示用户删除时，其记录也删除
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')
    # 原始上传图片路径
    original_image = models.ImageField(upload_to='uploads/%Y/%m/%d/', verbose_name='原始图片')
    # YOLO检测后的结果图片路径
    result_image = models.ImageField(upload_to='results/%Y/%m/%d/', verbose_name='识别结果图片')
    # 检测时间
    created_at = models.DateTimeField(default=timezone.now, verbose_name='检测时间')

    class Meta:
        verbose_name = '检测记录'
        verbose_name_plural = '检测记录'
        # 按时间倒序排列，最新的在前
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} 的检测记录 - {self.created_at.strftime('%Y-%m-%d %H:%M')}"