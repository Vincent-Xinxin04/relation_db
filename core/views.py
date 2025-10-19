from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db import transaction
import traceback
from core.utils.order_tools import create_order, get_order_list, update_order_status, delete_order
from core.utils.product_tools import get_product_list
from core.utils.customer_tools import get_customer_list, get_customer_detail, update_customer as update_customer_tool, \
    delete_customer as delete_customer_tool, create_customer as create_customer_tool, get_customer_by_phone
from core.utils.performance import performance_log, get_access_logs
import traceback
from django.contrib.auth import logout
@login_required
@performance_log
def order_manage(request):
    """订单管理视图（只处理GET请求）"""
    if request.method == 'GET':
        customer_id = request.GET.get('customer_id')
        customer_detail = None
        if customer_id:
            customer_detail = get_customer_detail(customer_id)

        # 总是获取日志数据，不再需要show_logs参数
        access_logs = get_access_logs(limit=50)

        return render(request, 'order_manage.html', {
            'orders': get_order_list(limit=50),
            'products': get_product_list(limit=100),
            'customers': get_customer_list(limit=100),
            'customer_detail': customer_detail,
            'access_logs': access_logs,
        })

    # 如果不是GET请求，原代码中处理POST的部分已经拆分到其他视图，所以这里可以返回错误
    return JsonResponse({"code": 400, "msg": "不支持的请求方法"})


@login_required
@performance_log
def order_create(request):
    """创建订单"""
    if request.method != 'POST':
        return JsonResponse({"code": 400, "msg": "只支持POST请求"})

    try:
        # 调试信息
        print("收到创建订单请求")
        print("客户姓名:", request.POST.get('cust_name'))
        print("客户电话:", request.POST.get('cust_phone'))
        print("客户地址:", request.POST.get('cust_addr'))
        print("商品项:", request.POST.get('items'))

        # 检查是否选择了商品
        items_str = request.POST.get('items', '')
        if not items_str or items_str.strip() == '':
            return JsonResponse({"code": 400, "msg": "请至少选择一个商品"})

        # 解析商品项
        items = []
        for item in items_str.split(';'):
            if item.strip():
                # 验证商品项格式
                if ':' not in item:
                    return JsonResponse({"code": 400, "msg": f"商品项格式错误: {item}"})
                items.append(item.strip())

        if not items:
            return JsonResponse({"code": 400, "msg": "请至少选择一个商品"})

        # 调用创建订单函数
        msg = create_order(
            cust_name=request.POST.get('cust_name'),
            cust_phone=request.POST.get('cust_phone'),
            cust_addr=request.POST.get('cust_addr'),
            items=items
        )
        return JsonResponse({"code": 200, "msg": msg})

    except Exception as e:
        # 记录详细错误信息
        error_traceback = traceback.format_exc()
        print(f"创建订单异常: {str(e)}")
        print(f"详细堆栈: {error_traceback}")

        # 返回详细的错误信息，但避免泄露敏感信息
        error_msg = str(e)
        if "doesn't have a default value" in error_msg:
            return JsonResponse({"code": 500, "msg": "数据库字段缺失，请联系管理员"})
        elif "foreign key constraint" in error_msg.lower():
            return JsonResponse({"code": 500, "msg": "数据关联错误，请检查客户或商品是否存在"})
        else:
            return JsonResponse({"code": 500, "msg": f"系统错误: {error_msg}"})


@login_required
@performance_log
def order_update_status(request):
    """更新订单状态"""
    if request.method != 'POST':
        return JsonResponse({"code": 400, "msg": "只支持POST请求"})

    try:
        order_id = request.POST.get('order_id')
        status = request.POST.get('status')
        if not order_id or not status:
            return JsonResponse({"code": 400, "msg": "订单ID和状态不能为空"})

        msg = update_order_status(
            order_id=int(order_id),
            status=status
        )
        return JsonResponse({"code": 200, "msg": msg})

    except Exception as e:
        error_traceback = traceback.format_exc()
        print(f"更新订单状态异常: {str(e)}")
        print(f"详细堆栈: {error_traceback}")
        return JsonResponse({"code": 500, "msg": f"系统错误: {str(e)}"})


@login_required
@performance_log
def order_delete(request):
    """删除订单"""
    if request.method != 'POST':
        return JsonResponse({"code": 400, "msg": "只支持POST请求"})

    try:
        order_id = request.POST.get('order_id')
        if not order_id:
            return JsonResponse({"code": 400, "msg": "订单ID不能为空"})

        msg = delete_order(order_id=int(order_id))
        return JsonResponse({"code": 200, "msg": msg})

    except Exception as e:
        error_traceback = traceback.format_exc()
        print(f"删除订单异常: {str(e)}")
        print(f"详细堆栈: {error_traceback}")
        return JsonResponse({"code": 500, "msg": f"系统错误: {str(e)}"})


@login_required
@performance_log
def customer_detail(request, customer_id):
    """客户详情API"""
    try:
        customer = get_customer_detail(customer_id)
        if not customer:
            return JsonResponse({"code": 404, "msg": "客户不存在"})

        return JsonResponse({
            "code": 200,
            "data": customer
        })
    except Exception as e:
        return JsonResponse({"code": 500, "msg": f"获取客户详情失败: {str(e)}"})


@login_required
@performance_log
def create_customer(request):
    """创建客户API"""
    if request.method != 'POST':
        return JsonResponse({"code": 405, "msg": "只支持POST方法"})

    try:
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        address = request.POST.get('address')

        if not all([name, phone, address]):
            return JsonResponse({"code": 400, "msg": "姓名、电话和地址不能为空"})

        # 创建客户并获取完整的客户信息
        customer_id = create_customer_tool(name, phone, address)

        # 获取新创建的客户的完整信息
        customer = get_customer_detail(customer_id)

        return JsonResponse({
            "code": 200,
            "msg": "客户创建成功",
            "customer": customer
        })

    except Exception as e:
        return JsonResponse({"code": 500, "msg": f"创建客户失败: {str(e)}"})


@login_required
@performance_log
def update_customer(request, customer_id):
    """更新客户信息API"""
    if request.method != 'POST':
        return JsonResponse({"code": 405, "msg": "只支持POST方法"})

    try:
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        address = request.POST.get('address')

        if not all([name, phone, address]):
            return JsonResponse({"code": 400, "msg": "姓名、电话和地址不能为空"})

        msg = update_customer_tool(customer_id, name, phone, address)

        # 获取更新后的客户信息
        customer = get_customer_detail(customer_id)

        return JsonResponse({
            "code": 200,
            "msg": msg,
            "customer": customer  # 返回更新后的客户信息
        })

    except Exception as e:
        return JsonResponse({"code": 500, "msg": f"更新客户信息失败: {str(e)}"})


@login_required
@performance_log
def delete_customer(request, customer_id):
    """删除客户API"""
    if request.method != 'POST':
        return JsonResponse({"code": 405, "msg": "只支持POST方法"})

    try:
        msg = delete_customer_tool(customer_id)
        return JsonResponse({"code": 200, "msg": msg})

    except Exception as e:
        return JsonResponse({"code": 500, "msg": f"删除客户失败: {str(e)}"})