from core.utils.db import exec_query, exec_update
from typing import List, Dict, Optional


def get_customer_by_phone(phone: str) -> Optional[Dict]:
    """根据手机号查询客户"""
    sql = "SELECT customer_id, name, phone FROM customer WHERE phone = %s"
    return exec_query(sql, (phone,), return_single=True)


def create_customer(name: str, phone: str, address: str) -> int:
    """创建客户"""
    if get_customer_by_phone(phone):
        raise Exception(f"手机号 {phone} 已注册客户，无法重复创建")

    sql = """
          INSERT INTO customer (name, phone, address, reg_date)
          VALUES (%s, %s, %s, CURDATE())
          """
    return exec_update(sql, (name, phone, address), return_id=True)


def get_customer_list(limit: int = 100):
    """获取客户列表"""
    sql = """
          SELECT customer_id,
                 name,
                 phone,
                 address,
                 reg_date,
                 (SELECT COUNT(*) FROM shop_order WHERE customer_id = customer.customer_id)                       as order_count,
                 (SELECT COALESCE(SUM(total_amount), 0) \
                  FROM shop_order \
                  WHERE customer_id = customer.customer_id)                                                       as total_spent
          FROM customer
          ORDER BY reg_date DESC
              LIMIT %s
          """
    return exec_query(sql, (limit,))


def get_customer_detail(customer_id: int):
    """获取客户详细信息"""
    try:
        customer_sql = """
                       SELECT customer_id,
                              name,
                              phone,
                              address,
                              reg_date
                       FROM customer
                       WHERE customer_id = %s
                       """
        customer = exec_query(customer_sql, (customer_id,), return_single=True)

        if not customer:
            return None

        order_stats_sql = """
                          SELECT COUNT(*)                                           as total_orders,
                                 COALESCE(SUM(total_amount), 0)                     as total_spent,
                                 COALESCE(AVG(total_amount), 0)                     as avg_order_value,
                                 MAX(create_time)                                   as last_order_date,
                                 SUM(CASE WHEN status = '已完成' THEN 1 ELSE 0 END) as completed_orders,
                                 SUM(CASE WHEN status = '待处理' THEN 1 ELSE 0 END) as pending_orders,
                                 SUM(CASE WHEN status = '已发货' THEN 1 ELSE 0 END) as shipped_orders
                          FROM shop_order
                          WHERE customer_id = %s
                          """
        order_stats = exec_query(order_stats_sql, (customer_id,), return_single=True)

        recent_orders_sql = """
                            SELECT order_id,
                                   order_code,
                                   total_amount,
                                   status,
                                   create_time
                            FROM shop_order
                            WHERE customer_id = %s
                            ORDER BY create_time DESC LIMIT 10
                            """
        recent_orders = exec_query(recent_orders_sql, (customer_id,))

        if order_stats:
            order_stats = {
                'total_orders': order_stats.get('total_orders', 0) or 0,
                'total_spent': float(order_stats.get('total_spent', 0) or 0),
                'avg_order_value': float(order_stats.get('avg_order_value', 0) or 0),
                'last_order_date': order_stats.get('last_order_date'),
                'completed_orders': order_stats.get('completed_orders', 0) or 0,
                'pending_orders': order_stats.get('pending_orders', 0) or 0,
                'shipped_orders': order_stats.get('shipped_orders', 0) or 0
            }
        else:
            order_stats = {
                'total_orders': 0,
                'total_spent': 0.0,
                'avg_order_value': 0.0,
                'last_order_date': None,
                'completed_orders': 0,
                'pending_orders': 0,
                'shipped_orders': 0
            }

        customer.update({
            'order_stats': order_stats,
            'recent_orders': recent_orders or []
        })

        return customer
    except Exception as e:
        print(f"获取客户详情失败: {str(e)}")
        return None


def update_customer(customer_id: int, name: str, phone: str, address: str) -> str:
    """更新客户信息"""
    try:
        # 先检查客户是否存在
        customer_sql = "SELECT customer_id FROM customer WHERE customer_id = %s"
        customer = exec_query(customer_sql, (customer_id,), return_single=True)

        if not customer:
            raise Exception(f"客户ID {customer_id} 不存在")

        # 检查手机号是否已被其他客户使用
        phone_check_sql = "SELECT customer_id FROM customer WHERE phone = %s AND customer_id != %s"
        existing_customer = exec_query(phone_check_sql, (phone, customer_id), return_single=True)

        if existing_customer:
            raise Exception(f"手机号 {phone} 已被其他客户使用")

        # 更新客户信息
        update_sql = """
                     UPDATE customer
                     SET name    = %s,
                         phone   = %s,
                         address = %s
                     WHERE customer_id = %s
                     """
        result = exec_update(update_sql, (name, phone, address, customer_id))

        if result > 0:
            return f"客户信息更新成功"
        else:
            return "客户信息未发生变化"

    except Exception as e:
        raise Exception(f"更新客户失败: {str(e)}")


def delete_customer(customer_id: int) -> str:
    """删除客户"""
    try:
        # 先检查客户是否存在
        customer_sql = "SELECT customer_id FROM customer WHERE customer_id = %s"
        customer = exec_query(customer_sql, (customer_id,), return_single=True)

        if not customer:
            raise Exception(f"客户ID {customer_id} 不存在")

        # 检查客户是否有订单
        order_check_sql = "SELECT COUNT(*) as order_count FROM shop_order WHERE customer_id = %s"
        order_count = exec_query(order_check_sql, (customer_id,), return_single=True)

        if order_count and order_count['order_count'] > 0:
            raise Exception(f"客户有关联订单，无法删除。请先删除相关订单")

        # 删除客户
        delete_sql = "DELETE FROM customer WHERE customer_id = %s"
        result = exec_update(delete_sql, (customer_id,))

        if result > 0:
            return f"客户删除成功"
        else:
            raise Exception("删除客户失败，可能客户不存在")

    except Exception as e:
        raise Exception(f"删除客户失败: {str(e)}")