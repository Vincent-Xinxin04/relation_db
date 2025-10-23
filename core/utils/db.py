from typing import List, Tuple, Optional, Dict, Any, Union
import pymysql
from django.conf import settings


def get_db_conn() -> Optional[pymysql.connections.Connection]:
    conn = None
    try:
        db_conf = settings.DATABASES['default']

        # 多用户并发通过"连接创建/释放管控"实现
        conn = pymysql.connect(
            host=db_conf['HOST'],
            port=int(db_conf['PORT']),  # 强制整数，避免格式错误
            user=db_conf['USER'],
            password=db_conf['PASSWORD'],
            database=db_conf['NAME'],  # 仅连接业务数据库DB_lab1
            charset='utf8mb4',  # 保证中文数据完整性
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=10,  # 防僵死连接
            autocommit=False,  # 支持事务
        )

        # 轻量校验：验证业务数据库连接存活
        if not conn.open:
            raise Exception(f"业务数据库（{db_conf['NAME']}）连接存活校验失败")

        return conn

    except pymysql.Error as e:
        error_code = e.args[0] if e.args else 0
        error_msg = str(e)
        # 细化错误提示，关联文档段落（便于答辩排查）
        error_map = {
            1045: "用户名/密码错误",
            1049: "业务数据库（DB_lab1）不存在",
            10060: "Linux服务器3306端口未开放",
            1130: "`django`用户无远程访问权限",
            1142: "用户权限不足",
            1064: "SQL语法错误"
        }
        raise Exception(f"数据库连接失败（错误码：{error_code}）：{error_map.get(error_code, error_msg)}")

    except Exception as e:
        # 资源释放：确保异常时关闭连接
        if conn and conn.open:
            conn.close()
        raise Exception(f"数据库连接异常：{str(e)}")


def exec_query(
        sql: str,
        params: Optional[Union[Tuple, Dict]] = None,
        return_single: bool = False,
        conn: Optional[pymysql.connections.Connection] = None
) -> Union[List[Dict], Dict, None]:
    """
    通用查询工具（参数化防注入，支持单条结果返回）
    """
    local_conn = None
    cursor = None
    try:
        # 支持外部传入连接（用于事务）或创建新连接
        if conn:
            local_conn = conn
        else:
            local_conn = get_db_conn()

        cursor = local_conn.cursor()
        # 参数化查询：防范SQL注入
        cursor.execute(sql, params or ())
        result = cursor.fetchall()
        # 支持返回单条结果（简化业务层代码，如查询单个商品/客户）
        return result[0] if (return_single and result) else result
    except Exception as e:
        # 补充SQL上下文，便于答辩时定位问题
        error_detail = f"查询失败（SQL片段：{sql[:100]}... | 参数：{params}）：{str(e)}"
        raise Exception(error_detail)
    finally:
        # 确保游标、连接资源释放
        # 注意：如果是外部传入的连接，不在这里关闭
        if cursor:
            cursor.close()
        if local_conn and local_conn.open and conn is None:  # 只关闭本地创建的连接
            local_conn.close()


def exec_update(
        sql: str,
        params: Optional[Union[Tuple, Dict]] = None,
        return_id: bool = False,
        batch: bool = False,
        params_list: Optional[List[Union[Tuple, Dict]]] = None,
        conn: Optional[pymysql.connections.Connection] = None
) -> int:
    """
    通用更新工具（支持事务回滚、批量执行、自增ID返回）
    """
    local_conn = None
    cursor = None
    try:
        # 支持外部传入连接（用于事务）或创建新连接
        if conn:
            local_conn = conn
        else:
            local_conn = get_db_conn()

        cursor = local_conn.cursor()

        # 批量/单条执行分支
        if batch and params_list and isinstance(params_list, list):
            cursor.executemany(sql, params_list)  # 批量执行效率高于循环单条
        else:
            cursor.execute(sql, params or ())

        # 事务提交：所有操作成功才确认
        # 注意：如果是外部传入的连接，由外部控制提交
        if conn is None:
            local_conn.commit()

        # 返回自增ID（插入数据时用，如创建客户/订单）或影响行数（修改/删除时用）
        if return_id:
            cursor.execute("SELECT LAST_INSERT_ID()")
            result = cursor.fetchone()
            return result['LAST_INSERT_ID()'] if result else 0
        return cursor.rowcount
    except Exception as e:
        # 事务回滚：任意步骤失败则恢复初始状态
        if local_conn and local_conn.open:
            local_conn.rollback()
        error_detail = f"更新失败（SQL片段：{sql[:100]}... | 批量：{batch}）：{str(e)}"
        raise Exception(error_detail)
    finally:
        if cursor:
            cursor.close()
        if local_conn and local_conn.open and conn is None:  # 只关闭本地创建的连接
            local_conn.close()


def with_transaction(func):
    """
    事务装饰器：控制复杂业务原子性（如订单创建：客户→订单→明细→库存）
    """
    def wrapper(*args, **kwargs):
        conn = None
        try:
            conn = get_db_conn()
            # 传入连接确保多步操作共用同一事务
            result = func(conn, *args, **kwargs)
            conn.commit()
            return result
        except Exception as e:
            if conn and conn.open:
                conn.rollback()  # 异常时回滚，符合ACID特性
            raise Exception(f"事务执行失败：{str(e)}")
        finally:
            if conn and conn.open:
                conn.close()  # 释放连接

    return wrapper


# 新增：简化查询函数，用于简单的单表查询
def simple_query(table: str, fields: List[str] = None,
                 where: str = None, params: Tuple = None,
                 limit: int = None) -> List[Dict]:
    """
    简化查询函数，用于快速执行简单查询
    """
    field_list = ", ".join(fields) if fields else "*"
    sql = f"SELECT {field_list} FROM {table}"

    if where:
        sql += f" WHERE {where}"

    if limit:
        sql += f" LIMIT {limit}"

    return exec_query(sql, params)


# 新增：检查表是否存在
def table_exists(table_name: str) -> bool:
    """
    检查表是否存在
    """
    try:
        sql = "SHOW TABLES LIKE %s"
        result = exec_query(sql, (table_name,), return_single=True)
        return result is not None
    except Exception:
        return False