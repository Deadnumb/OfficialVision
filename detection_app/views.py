from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout

# 主页
def home(request):
    # 路径改为 detector/home.html
    return render(request, 'detector/home.html')

# 登录
def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

# 注册
def user_register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})
def upload(request):
    return render(request, 'upload.html')  # 后面你可以创建 upload.html 作为上传页
from django.contrib.auth import logout

def user_logout(request):
    logout(request)
    return redirect('home')  # 退出后跳回主页
# 结果页
def result(request):
    return render(request, 'result.html')