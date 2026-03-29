from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.user_login, name='login'),
    path('register/', views.user_register, name='register'),
    path('result/', views.result, name='result'),
    path('upload/', views.upload, name='upload'),
    path('logout/', views.user_logout, name='logout'),
]