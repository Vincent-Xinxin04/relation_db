from core.utils.db import exec_query, exec_update
from typing import Dict, List

from core.utils.db import exec_query, exec_update
from typing import Dict, List
import time


def get_product(product_id: int) -> Dict:
    """
    查询商品
    """
    sql = """
          SELECT p.product_id, p.name, p.price, p.stock, GROUP_CONCAT(c.name) AS categories
          FROM product p
                   LEFT JOIN product_category pc ON p.product_id = pc.product_id
                   LEFT JOIN category c ON pc.category_id = c.category_id
          WHERE p.product_id = %s
          GROUP BY p.product_id \
          """
    product = exec_query(sql, (product_id,), return_single=True)
    if not product:
        raise Exception(f"商品ID {product_id} 不存在（表：product）")
    return product


def update_product_stock(product_id: int, reduce_qty: int) -> str:
    """
    扣减商品库存（带锁等待超时处理）
    """
    max_retries = 5
    base_delay = 0.5  # 基础延迟0.5秒

    for attempt in range(max_retries):
        try:
            # 先查库存，再扣减
            product = get_product(product_id)
            if product['stock'] < reduce_qty:
                raise Exception(f"商品「{product['name']}」库存不足（当前：{product['stock']}，需扣减：{reduce_qty}）")

            sql = "UPDATE product SET stock = stock - %s WHERE product_id = %s"
            result = exec_update(sql, (reduce_qty, product_id))

            # 验证更新是否成功
            updated_product = get_product(product_id)
            if updated_product['stock'] != product['stock'] - reduce_qty:
                raise Exception(
                    f"库存更新失败，预期库存: {product['stock'] - reduce_qty}，实际库存: {updated_product['stock']}")

            return f"库存扣减成功，剩余：{updated_product['stock']}"

        except Exception as e:
            if "Lock wait timeout" in str(e) and attempt < max_retries - 1:
                wait_time = base_delay * (2 ** attempt)  # 指数退避
                print(f"锁等待超时，第{attempt + 1}次重试，等待{wait_time}秒...")
                time.sleep(wait_time)
                continue
            else:
                raise Exception(f"库存扣减失败（尝试{attempt + 1}次）: {str(e)}")


def get_product_list(limit: int = 100) -> List[Dict]:
    """获取商品列表"""
    sql = """
          SELECT p.product_id, p.name, p.price, p.stock, GROUP_CONCAT(c.name) AS categories
          FROM product p
                   LEFT JOIN product_category pc ON p.product_id = pc.product_id
                   LEFT JOIN category c ON pc.category_id = c.category_id
          GROUP BY p.product_id
              LIMIT %s \
          """
    return exec_query(sql, (limit,))