import os
import sys
import django

# 设置Django环境
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'relation_db.settings')
django.setup()

from core.models import Customer, Category, Product, ProductCategory, Order, OrderItem, AccessLog
from django.contrib.auth.models import User
from django.db import transaction
from django.db import connection


def clear_all_data():
    """清除所有表的数据"""
    print("🧹 开始清除所有表数据...")

    # 按照外键依赖关系逆序删除，避免外键约束错误
    tables = [
        ('访问日志', AccessLog),
        ('订单明细', OrderItem),
        ('订单', Order),
        ('商品分类关联', ProductCategory),
        ('商品', Product),
        ('分类', Category),
        ('客户', Customer),
    ]

    try:
        with transaction.atomic():
            for table_name, model in tables:
                count = model.objects.count()
                model.objects.all().delete()
                print(f"✅ 已清除 {table_name} 表: {count} 条记录")

        print("✅ 所有表数据清除完成！")

        # 显示清除后的统计
        print_stats()

    except Exception as e:
        print(f"清除数据时出错: {e}")
        print("正在回滚事务...")


def reset_auto_increment():
    """重置所有表的自增ID"""
    print("\n🔄 重置自增ID...")

    # MySQL重置自增ID的SQL语句
    reset_sql = [
        "ALTER TABLE access_logs AUTO_INCREMENT = 1;",
        "ALTER TABLE shop_order_item AUTO_INCREMENT = 1;",
        "ALTER TABLE shop_order AUTO_INCREMENT = 1;",
        "ALTER TABLE product_category AUTO_INCREMENT = 1;",
        "ALTER TABLE product AUTO_INCREMENT = 1;",
        "ALTER TABLE category AUTO_INCREMENT = 1;",
        "ALTER TABLE customer AUTO_INCREMENT = 1;",
    ]

    try:
        with connection.cursor() as cursor:
            for sql in reset_sql:
                try:
                    cursor.execute(sql)
                    table_name = sql.split(' ')[2]  # 提取表名
                    print(f"置 {table_name} 自增ID")
                except Exception as e:
                    print(f"⚠️  重置自增ID时警告: {e}")

        print("自增ID重置完成！")

    except Exception as e:
        print(f"❌ 重置自增ID时出错: {e}")


def clear_specific_table():
    """选择性清除特定表的数据"""
    print("\n🎯 选择性清除数据")
    print("1. 客户表")
    print("2. 商品表")
    print("3. 订单表")
    print("4. 分类表")
    print("5. 访问日志表")
    print("6. 所有表")

    try:
        choice = input("请选择要清除的表 (1-6): ").strip()

        if choice == '1':
            count = Customer.objects.count()
            Customer.objects.all().delete()
            print(f"✅ 已清除客户表: {count} 条记录")
        elif choice == '2':
            count = Product.objects.count()
            Product.objects.all().delete()
            print(f"✅ 已清除商品表: {count} 条记录")
        elif choice == '3':
            # 先删除订单明细，再删除订单
            order_item_count = OrderItem.objects.count()
            order_count = Order.objects.count()
            OrderItem.objects.all().delete()
            Order.objects.all().delete()
            print(f"✅ 已清除订单表: {order_count} 条记录")
            print(f"✅ 已清除订单明细表: {order_item_count} 条记录")
        elif choice == '4':
            # 先删除商品分类关联，再删除分类
            product_category_count = ProductCategory.objects.count()
            category_count = Category.objects.count()
            ProductCategory.objects.all().delete()
            Category.objects.all().delete()
            print(f"✅ 已清除分类表: {category_count} 条记录")
            print(f"✅ 已清除商品分类关联表: {product_category_count} 条记录")
        elif choice == '5':
            count = AccessLog.objects.count()
            AccessLog.objects.all().delete()
            print(f"✅ 已清除访问日志表: {count} 条记录")
        elif choice == '6':
            clear_all_data()
        else:
            print("❌ 无效选择")

    except Exception as e:
        print(f"❌ 清除特定表时出错: {e}")


def print_stats():
    """打印当前数据统计"""
    print("\n📊 === 当前数据统计 ===")
    print(f"客户数量: {Customer.objects.count()}")
    print(f"分类数量: {Category.objects.count()}")
    print(f"商品数量: {Product.objects.count()}")
    print(f"商品分类关联数量: {ProductCategory.objects.count()}")
    print(f"订单数量: {Order.objects.count()}")
    print(f"订单明细数量: {OrderItem.objects.count()}")
    print(f"访问日志数量: {AccessLog.objects.count()}")


def safe_clear_with_confirmation():
    """带确认的安全清除"""
    print("⚠️  警告: 此操作将永久删除所有数据！")
    print("当前数据统计:")
    print_stats()

    confirmation = input("\n确定要清除所有数据吗？(输入 'YES' 确认): ").strip()

    if confirmation == 'YES':
        clear_all_data()
        reset_choice = input("是否重置自增ID？(y/n): ").strip().lower()
        if reset_choice == 'y':
            reset_auto_increment()
    else:
        print("❌ 操作已取消")


def main():
    """主菜单"""
    while True:
        print("\n" + "=" * 50)
        print("🗑️  数据清除工具")
        print("=" * 50)
        print("1. 安全清除所有数据（带确认）")
        print("2. 选择性清除特定表数据")
        print("3. 仅重置自增ID")
        print("4. 查看当前数据统计")
        print("5. 退出")
        print("=" * 50)

        try:
            choice = input("请选择操作 (1-5): ").strip()

            if choice == '1':
                safe_clear_with_confirmation()
            elif choice == '2':
                clear_specific_table()
            elif choice == '3':
                reset_auto_increment()
            elif choice == '4':
                print_stats()
            elif choice == '5':
                print("👋 退出程序")
                break
            else:
                print("❌ 无效选择，请重新输入")

            # 每次操作后暂停一下
            if choice != '5':
                input("\n按回车键继续...")

        except KeyboardInterrupt:
            print("\n\n👋 用户中断，退出程序")
            break
        except Exception as e:
            print(f"❌ 发生错误: {e}")
            input("\n按回车键继续...")


if __name__ == "__main__":
    main()