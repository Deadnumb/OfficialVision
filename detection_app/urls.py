from django.urls import path
from . import views

urlpatterns = [
    # 根路径 → 登录页（实现先登录再访问）
    path('', views.user_login, name='login'),
    # 登录页（兼容 /login/ 访问）
    path('login/', views.user_login, name='login'),
    # 注册页
    path('register/', views.user_register, name='register'),
    # 上传页
    path('upload/', views.upload, name='upload'),
    # 结果页
    path('result/', views.result, name='result'),
    # 退出登录
    path('logout/', views.user_logout, name='logout'),
    # 主页（可选）
    path('home/', views.home, name='home'),
]