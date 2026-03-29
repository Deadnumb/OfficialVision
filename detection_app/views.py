from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.files.storage import FileSystemStorage
import os
from ultralytics import YOLO

# 👇 加载你的 table.pt 模型（路径要和你项目结构一致！）
# 你的模型在 D:\OfficeVision\models\table.pt
model = YOLO('models/table.pt')  # 因为 manage.py 在 OfficeVision 根目录，所以直接写 models/table.pt

# 主页
def home(request):
    return render(request, 'detector/home.html')

# 登录
def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('upload')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

# 注册
def user_register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

# 上传 + 检测
@login_required(login_url='/')
def upload(request):
    if request.method == 'POST' and request.FILES.get('image'):
        # 1. 接收上传图片
        image = request.FILES['image']
        fs = FileSystemStorage(location=settings.MEDIA_ROOT)
        filename = fs.save(image.name, image)
        original_path = os.path.join(settings.MEDIA_ROOT, filename)
        original_url = fs.url(filename)

        # 2. 调用 table.pt 模型检测
        results = model(original_path)

        # 3. 生成带框的结果图
        result_filename = 'result_' + filename
        result_path = os.path.join(settings.MEDIA_ROOT, result_filename)
        results[0].save(result_path)
        result_url = fs.url(result_filename)

        # 4. 统计物品数量
        stats = {}
        for res in results:
            for box in res.boxes:
                cls_id = int(box.cls[0])
                cls_name = model.names[cls_id]
                stats[cls_name] = stats.get(cls_name, 0) + 1
        total = sum(stats.values())

        # 5. 跳转到结果页
        return render(request, 'detector/result.html', {
            'original_url': original_url,
            'result_url': result_url,
            'total': total,
            'stats': stats
        })

    return render(request, 'detector/home.html')

# 退出登录
def user_logout(request):
    logout(request)
    return redirect('login')

# 结果页
def result(request):
    return render(request, 'detector/result.html')