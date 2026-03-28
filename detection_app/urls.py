from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # 首页
    path('upload/', views.upload_image, name='upload'),
    path('result/<int:result_id>/', views.show_result, name='result'),
]