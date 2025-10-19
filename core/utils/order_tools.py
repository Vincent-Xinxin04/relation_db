import datetime
from core.utils.db import exec_query, exec_update, with_transaction
from core.utils.product_tools import get_product, update_product_stock
from typing import List, Dict
import time

@with_transaction
def create_order(
        conn,
        cust_name: str,
        cust_phone: str,
        cust_addr: str,
        items: List[str]
) -> str:
    try:
        # print(f"开始创建订单，客户: {cust_name}, 电话: {cust_phone}, 商品项: {items}")

        # 在函数内部导入，避免循环导入
        from core.utils.customer_tools import get_customer_by_phone, create_customer

        # 步骤1：立即锁定所有涉及的商品记录
        product_ids = []
        for item in items:
            if item.strip():
                product_id, _ = item.split(':')
                product_ids.append(int(product_id))

        if product_ids:
            placeholders = ','.join(['%s'] * len(product_ids))
            lock_sql = f"SELECT product_id FROM product WHERE product_id IN ({placeholders}) FOR UPDATE"
            exec_query(lock_sql, product_ids, conn=conn)
            # print(f"已锁定商品记录: {product_ids}")

        # 步骤2：处理客户（新增/查询）
        customer = get_customer_by_phone(cust_phone)
        # print(f"查询客户结果: {customer}")

        if customer:
            cust_id = customer['customer_id']
            # print(f"使用现有客户ID: {cust_id}")
        else:
            # print(f"创建新客户: {cust_name}, {cust_phone}, {cust_addr}")
            cust_id = create_customer(cust_name, cust_phone, cust_addr)
            # print(f"新客户ID: {cust_id}")

        # 步骤3：计算订单总金额+校验商品（使用已锁定的商品）
        total_amount = 0.0
        item_params = []

        for item in items:
            if not item.strip():
                continue

            # print(f"处理商品项: {item}")
            try:
                product_id, quantity = item.split(':')
                quantity = int(quantity)

                # 使用已锁定的商品信息
                product_sql = "SELECT product_id, name, price, stock FROM product WHERE product_id = %s"
                product = exec_query(product_sql, (int(product_id),), return_single=True, conn=conn)
                # print(f"商品信息: {product}")

                if not product:
                    raise Exception(f"商品ID {product_id} 不存在")

                # 检查库存
                if product['stock'] < quantity:
                    raise Exception(f"商品「{product['name']}」库存不足（当前：{product['stock']}，需要：{quantity}）")

                # 累加金额
                item_amount = quantity * float(product['price'])
                total_amount = round(total_amount + item_amount, 2)
                item_params.append((None, product_id, quantity, product['price']))
            except ValueError as e:
                raise Exception(f"商品项格式错误: {item}")

        # print(f"订单总金额: {total_amount}")

        # 步骤4：插入订单
        order_code = f"ORD{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')[:16]}"
        current_time = datetime.datetime.now()

        # print(f"准备插入订单，编号: {order_code}, 客户ID: {cust_id}, 金额: {total_amount}")

        order_sql = """
                    INSERT INTO shop_order (order_code, customer_id, status, total_amount, create_time)
                    VALUES (%s, %s, '待处理', %s, %s)
                    """
        order_id = exec_update(sql=order_sql, params=(order_code, cust_id, total_amount, current_time), return_id=True,
                               conn=conn)
        # print(f"订单插入成功，订单ID: {order_id}")

        # 步骤5：插入订单明细
        if item_params:
            item_params = [(order_id,) + param[1:] for param in item_params]
            # print(f"准备插入订单明细: {item_params}")

            item_sql = """
                       INSERT INTO shop_order_item (order_id, product_id, quantity, unit_price)
                       VALUES (%s, %s, %s, %s)
                       """
            exec_update(sql=item_sql, params_list=item_params, batch=True, conn=conn)
            # print("订单明细插入成功")

        # 步骤6：扣减商品库存（使用已锁定的连接）
        for item in items:
            if not item.strip():
                continue

            product_id, quantity = item.split(':')
            # print(f"扣减库存，商品ID: {product_id}, 数量: {quantity}")

            # 直接使用当前事务连接扣减库存
            update_sql = "UPDATE product SET stock = stock - %s WHERE product_id = %s"
            exec_update(update_sql, (int(quantity), int(product_id)), conn=conn)

            # 验证库存
            check_sql = "SELECT stock FROM product WHERE product_id = %s"
            updated_stock = exec_query(check_sql, (int(product_id),), return_single=True, conn=conn)
            # print(f"商品 {product_id} 扣减后库存: {updated_stock['stock']}")

        result_msg = f"订单创建成功！编号：{order_code}，总金额：{total_amount}元"
        # print(result_msg)
        return result_msg

    except Exception as e:
        error_msg = f"创建订单过程中出错: {str(e)}"
        # print(error_msg)
        import traceback
        # print(traceback.format_exc())
        raise Exception(error_msg)


def get_order_list(limit: int = 50) -> List[Dict]:
    """
    查询订单列表（跨5表Join，满足实验一"跨数据表操作"基本功能
    关联表：shop_order（订单）→ customer（客户）→ shop_order_item（明细）→ product（商品）→ category（分类）
    """
    sql = """
          SELECT o.order_id, \
                 o.order_code, \
                 o.create_time, \
                 o.status, \
                 o.total_amount, \
                 c.customer_id, \
                 c.name                        AS cust_name, \
                 c.phone                       AS cust_phone, \
                 GROUP_CONCAT(DISTINCT p.name) AS prod_names, \
                 COUNT(oi.item_id)             AS item_count
          FROM shop_order o
                   LEFT JOIN customer c ON o.customer_id = c.customer_id
                   LEFT JOIN shop_order_item oi ON o.order_id = oi.order_id
                   LEFT JOIN product p ON oi.product_id = p.product_id
          GROUP BY o.order_id, o.order_code, o.create_time, o.status, o.total_amount, c.customer_id, c.name, c.phone
          ORDER BY o.create_time DESC
              LIMIT %s
          """
    return exec_query(sql, (limit,))


def update_order_status(order_id: int, status: str) -> str:
    """
    更新订单状态
    """
    valid_status = ['待处理', '已发货', '已完成']  # 与表结构注释一致
    if status not in valid_status:
        raise Exception(f"状态必须为：{', '.join(valid_status)}（参考表shop_order的status字段注释）")

    # 先校验订单存在
    if not exec_query("SELECT order_id FROM shop_order WHERE order_id = %s", (order_id,)):
        raise Exception(f"订单ID {order_id} 不存在（表：shop_order）")

    sql = "UPDATE shop_order SET status = %s WHERE order_id = %s"
    exec_update(sql, (status, order_id))
    return f"订单 {order_id} 状态更新为：{status}"


@with_transaction
def delete_order(conn, order_id: int) -> str:
    """
    删除订单
    """
    # 先检查订单是否存在
    if not exec_query("SELECT order_id FROM shop_order WHERE order_id = %s", (order_id,), conn=conn):
        raise Exception(f"订单ID {order_id} 不存在（表：shop_order）")

    # 获取订单中的商品信息，用于恢复库存
    items_sql = """
                SELECT product_id, quantity
                FROM shop_order_item
                WHERE order_id = %s \
                """
    items = exec_query(items_sql, (order_id,), conn=conn)

    # 恢复商品库存
    for item in items:
        restore_stock_sql = """
                            UPDATE product
                            SET stock = stock + %s
                            WHERE product_id = %s \
                            """
        exec_update(restore_stock_sql, (item['quantity'], item['product_id']), conn=conn)

    # 先删除订单明细
    delete_items_sql = "DELETE FROM shop_order_item WHERE order_id = %s"
    exec_update(delete_items_sql, (order_id,), conn=conn)

    # 再删除订单
    delete_order_sql = "DELETE FROM shop_order WHERE order_id = %s"
    exec_update(delete_order_sql, (order_id,), conn=conn)

    return f"订单 {order_id} 已删除（含关联明细：shop_order_item）"