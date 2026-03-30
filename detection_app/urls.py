from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
"""
URL配置
1. 首页：显示所有检测结果
2. 上传图片：允许用户上传图片进行检测
3. 检测结果：显示单个检测结果的详细信息

"""
urlpatterns = [
    path('', views.home, name='home'),  # 首页
    path('upload/', views.upload_image, name='upload'),
    path('result/<int:result_id>/', views.show_result, name='result'),
    path('register/', views.user_register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('history/', views.history, name='history'),
    path('upload-records/', views.upload_records, name='upload_records'),
    path('upload/video/', views.upload_video, name='upload_video'),
    path('test-media/', views.test_media_access, name='test_media'),  # 测试媒体文件
]
