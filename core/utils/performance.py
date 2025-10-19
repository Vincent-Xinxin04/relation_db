import time
from django.utils import timezone
from django.http import HttpResponseBase
from django.db import DatabaseError
from django.contrib.auth.models import User
from core.utils.db import exec_update, exec_query
from core.models import AccessLog
import logging

# 创建logger用于记录错误
logger = logging.getLogger(__name__)


def performance_log(view_func):
    """
    装饰器：记录视图访问性能（用户、路径、耗时、IP）
    """

    def wrapper(request, *args, **kwargs) -> HttpResponseBase:
        # 记录请求初始信息
        start_time = timezone.now()
        user = request.user
        access_path = request.path  # 如：/order/
        client_ip = get_client_ip(request)  # 使用函数获取客户端IP

        # 执行业务视图函数
        try:
            response = view_func(request, *args, **kwargs)
            status_code = response.status_code
            error_message = None
        except Exception as e:
            # 如果视图函数抛出异常，记录异常信息
            end_time = timezone.now()
            duration = round((end_time - start_time).total_seconds(), 4)
            status_code = 500
            error_message = str(e)
            log_performance(
                user, access_path, start_time, end_time, duration, client_ip,
                status_code, error_message
            )
            raise  # 重新抛出异常

        # 计算耗时并记录日志（写入access_logs表）
        end_time = timezone.now()
        duration = round((end_time - start_time).total_seconds(), 4)  # 耗时（秒，保留4位小数）

        log_performance(
            user, access_path, start_time, end_time, duration, client_ip,
            status_code, error_message
        )

        return response

    return wrapper


def get_client_ip(request):
    """获取客户端真实IP地址"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]  # 获取第一个IP
    else:
        ip = request.META.get('REMOTE_ADDR', '未知IP')
    return ip.strip()


def log_performance(user, path, start_time, end_time, duration, ip, status_code, error_message):
    """记录性能日志到数据库"""
    try:
        # 使用Django ORM创建记录
        AccessLog.objects.create(
            user=user if user.is_authenticated else None,
            path=path,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            ip=ip
        )

    except DatabaseError as e:
        logger.error(f"性能日志记录失败（数据库错误）：{str(e)}")
    except Exception as e:
        logger.error(f"性能日志记录失败：{str(e)}")


def get_access_logs(limit: int = 100, user_id=None, path_filter=None):
    """获取访问性能日志，支持过滤"""
    # 使用Django ORM查询
    queryset = AccessLog.objects.all()

    # 添加过滤条件
    if user_id:
        queryset = queryset.filter(user_id=user_id)

    if path_filter:
        queryset = queryset.filter(path__icontains=path_filter)

    # 排序和限制
    queryset = queryset.order_by('-start_time')[:limit]

    # 转换为字典格式，保持与之前兼容
    logs = []
    for log in queryset:
        logs.append({
            'log_id': log.log_id,
            'user_id': log.user_id,
            'username': log.user.username if log.user else None,
            'path': log.path,
            'start_time': log.start_time,
            'end_time': log.end_time,
            'duration': log.duration,
            'ip': log.ip
        })

    return logs


def get_performance_stats(days=7):
    """获取性能统计信息"""
    from django.db.models import Count, Avg, Max, Min
    from django.utils import timezone
    from datetime import timedelta

    # 计算起始时间
    start_date = timezone.now() - timedelta(days=days)

    # 使用Django ORM进行聚合查询
    stats = AccessLog.objects.filter(
        start_time__gte=start_date
    ).aggregate(
        total_requests=Count('log_id'),
        avg_duration=Avg('duration'),
        max_duration=Max('duration'),
        min_duration=Min('duration'),
        unique_ips=Count('ip', distinct=True),
        unique_users=Count('user_id', distinct=True)
    )

    return stats


def cleanup_old_logs(days=30):
    """清理指定天数前的旧日志"""
    try:
        from django.utils import timezone
        from datetime import timedelta

        # 计算截止日期
        cutoff_date = timezone.now() - timedelta(days=days)

        # 删除旧日志
        deleted_count, _ = AccessLog.objects.filter(
            start_time__lt=cutoff_date
        ).delete()

        logger.info(f"清理了 {deleted_count} 条 {days} 天前的日志记录")
        return deleted_count
    except Exception as e:
        logger.error(f"清理旧日志失败：{str(e)}")
        return 0


# 保持向后兼容的原始SQL版本（如果需要）
def get_access_logs_sql(limit: int = 100):
    """获取访问性能日志（SQL版本）"""
    sql = """
          SELECT log_id, \
                 user_id, \
                 (SELECT username FROM auth_user WHERE id = access_logs.user_id) as username, \
                 path, \
                 start_time, \
                 end_time, \
                 duration, \
                 ip
          FROM access_logs
          ORDER BY start_time DESC
              LIMIT %s \
          """
    return exec_query(sql, (limit,))