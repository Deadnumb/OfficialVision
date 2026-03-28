from django.utils import timezone
from detection_app.models import PERMANENT_VIP_DATE


def is_vip(user):
    """
    检查用户是否为VIP

    参数:
        user: User模型实例
    返回:
        bool: True表示是VIP，False表示不是VIP

    判断逻辑:
        1. vip_expire_at为空 -> 不是VIP
        2. 当前时间 <= vip_expire_at -> 是VIP
    """
    if not user.vip_expire_at:
        return False
    elif timezone.now() <= user.vip_expire_at:
        return True


def get_vip_remaining_days(user):
    """
    获取VIP剩余天数

    参数:
        user: User模型实例
    返回:
        int: 剩余天数，如果不是VIP返回0，永久VIP返回-1
    """
    if not is_vip(user):
        return 0

    # 判断是否为永久VIP（年份达到阈值）
    if user.vip_expire_at.year >= PERMANENT_VIP_DATE.year:
        return -1  # -1表示永久VIP

    # 计算剩余天数
    remaining = user.vip_expire_at - timezone.now()
    return max(0, remaining.days)