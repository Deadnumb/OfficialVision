from django.urls import path
from . import views

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
    # Deleted:path('upload/laptop/', views.upload_image_laptop, name='upload_laptop'),
    # path('profile/', views.uprofile, name='profile'),
    # path('history/', views.history, name='history')
    path('history/', views.history, name='history'),  #历史记录页面
    path('upload-records/', views.upload_records, name='upload_records'),  # 上传记录页面
]
