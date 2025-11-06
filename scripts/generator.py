import os
import sys
import django

# 设置Django环境
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'relation_db.settings')
django.setup()


import random
from datetime import datetime, timedelta
from decimal import Decimal
from core.models import Customer, Category, Product, ProductCategory, Order, OrderItem, AccessLog
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone

def main():
    """主函数 - 生成真实合理的模拟数据"""
    print("开始生成真实模拟数据...")

    # 先清除现有数据
    clear_existing_data()

    # 生成基础数据
    generate_categories()
    generate_customers(200)  # 200个真实客户
    generate_products(100)  # 100个真实商品
    generate_orders_and_items(100000)  # 10000个真实订单

    print("所有真实模拟数据生成完成！")
    print_stats()


def clear_existing_data():
    """清除现有数据"""
    print("清除现有数据...")
    try:
        OrderItem.objects.all().delete()
        Order.objects.all().delete()
        ProductCategory.objects.all().delete()
        Product.objects.all().delete()
        Customer.objects.all().delete()
        Category.objects.all().delete()
        print("数据清除完成")
    except Exception as e:
        print(f"清除数据时出错: {e}")


def generate_categories():
    """生成商品分类"""
    print("生成商品分类...")
    categories_data = [
        ('手机通讯', '智能手机、功能手机、对讲机等'),
        ('电脑办公', '笔记本电脑、台式机、打印机等'),
        ('家用电器', '电视、冰箱、洗衣机、空调等'),
        ('数码配件', '耳机、充电器、数据线、保护壳等'),
        ('食品饮料', '零食、饮料、生鲜食品等'),
        ('服装鞋帽', '男女服装、鞋类、配饰等'),
        ('美妆护肤', '化妆品、护肤品、个人护理等'),
        ('家居用品', '家具、厨具、家纺等'),
        ('运动户外', '运动装备、户外用品等'),
        ('图书文具', '图书、文具、办公用品等'),
    ]

    for name, desc in categories_data:
        Category.objects.get_or_create(name=name, description=desc)
    print(f"生成 {len(categories_data)} 个分类")


def generate_customers(count=200):
    """生成真实客户数据"""
    print(f"生成 {count} 个真实客户...")

    # 更丰富的姓名组合
    first_names = ['张', '王', '李', '赵', '陈', '刘', '杨', '黄', '周', '吴',
                   '徐', '孙', '胡', '朱', '高', '林', '何', '郭', '马', '罗']
    last_names = ['伟', '芳', '娜', '秀英', '敏', '静', '磊', '洋', '艳', '勇',
                  '军', '杰', '娟', '强', '霞', '平', '刚', '鹏', '超', '明',
                  '华', '兰', '玲', '燕', '辉', '娜', '健', '丹', '萍', '亮']

    cities_districts = {
        '北京': ['朝阳区', '海淀区', '西城区', '东城区', '丰台区'],
        '上海': ['浦东新区', '徐汇区', '长宁区', '静安区', '黄浦区'],
        '广州': ['天河区', '越秀区', '海珠区', '荔湾区', '白云区'],
        '深圳': ['南山区', '福田区', '罗湖区', '宝安区', '龙岗区'],
        '杭州': ['西湖区', '上城区', '下城区', '江干区', '拱墅区'],
        '成都': ['锦江区', '青羊区', '金牛区', '武侯区', '成华区']
    }

    streets = ['人民路', '中山路', '解放路', '建设路', '文化路', '和平路', '青年路', '新华路']

    customers = []
    used_names = set()  # 避免重复姓名

    for i in range(count):
        # 生成唯一姓名
        max_attempts = 50
        for attempt in range(max_attempts):
            name = random.choice(first_names) + random.choice(last_names)
            if name not in used_names:
                used_names.add(name)
                break
        else:
            name = f"客户{i + 1:03d}"

        # 生成唯一手机号
        phone = generate_unique_phone()

        # 生成地址
        city = random.choice(list(cities_districts.keys()))
        district = random.choice(cities_districts[city])
        street = random.choice(streets)
        address = f"{city}市{district}{street}{random.randint(1, 999)}号"

        # 注册日期在最近2年内随机
        reg_date = timezone.now().date() - timedelta(days=random.randint(1, 730))

        customers.append(Customer(
            name=name, phone=phone, address=address, reg_date=reg_date
        ))

    Customer.objects.bulk_create(customers)
    print(f"✅ 生成 {count} 个真实客户完成")


def generate_unique_phone():
    """生成唯一手机号"""
    while True:
        phone = f"1{random.randint(30, 89)}{random.randint(1000, 9999)}{random.randint(1000, 9999)}"
        if not Customer.objects.filter(phone=phone).exists():
            return phone


def generate_products(count=100):
    """生成真实商品数据"""
    print(f"生成 {count} 个真实商品...")
    categories = list(Category.objects.all())

    # 丰富的商品名称词库
    product_names = {
        '手机通讯': [
            'iPhone 15 Pro Max 256GB', '华为 Mate 60 Pro', '小米 14 Ultra',
            'OPPO Find X7', 'vivo X100 Pro', '荣耀 Magic6 Pro',
            '三星 Galaxy S24 Ultra', '一加 12', '红米 K70',
            '真我 GT5 Pro', '魅族 21', '中兴 Axon 40 Ultra'
        ],
        '电脑办公': [
            'MacBook Pro 16英寸 M3', '联想 ThinkPad X1 Carbon', '华为 MateBook X Pro',
            '戴尔 XPS 13', '华硕 ROG 枪神7', '惠普暗影精灵10',
            '微软 Surface Laptop 5', '机械革命蛟龙16', '雷蛇灵刃14',
            '宏碁暗影骑士·擎', '微星冲锋坦克', '神舟战神TX8'
        ],
        '家用电器': [
            '海尔变频空调', '美的智能冰箱', '格力空调柜机',
            '小米电视大师', '索尼BRAVIA电视', 'TCL QLED电视',
            '松下洗衣机', '西门子对开门冰箱', '三星智能冰箱',
            '老板抽油烟机', '方太燃气灶', '九阳破壁机'
        ],
        '数码配件': [
            'AirPods Pro 2', '华为FreeBuds Pro 3', '小米Buds 4 Pro',
            '苹果MagSafe充电器', 'Anker氮化镓充电器', '贝尔金扩展坞',
            '罗技MX Master 3S', '雷蛇黑寡妇键盘', '樱桃机械键盘',
            '西部数据移动硬盘', '闪迪存储卡', '绿联数据线'
        ],
        '食品饮料': [
            '可口可乐经典口味', '百事可乐无糖', '康师傅红烧牛肉面',
            '统一老坛酸菜面', '蒙牛纯牛奶', '伊利安慕希',
            '农夫山泉矿泉水', '康师傅冰红茶', '王老吉凉茶',
            '奥利奥夹心饼干', '乐事薯片', '德芙巧克力'
        ],
        '服装鞋帽': [
            '优衣库HEATTECH保暖内衣', '李宁运动卫衣', '安踏跑步鞋',
            '耐克Air Force 1', '阿迪达斯Superstar', '匡威经典帆布鞋',
            'ZARA修身衬衫', 'H&M休闲裤', '杰克琼斯夹克',
            '太平鸟牛仔裤', '森马T恤', '美特斯邦威外套'
        ],
        '美妆护肤': [
            '雅诗兰黛小棕瓶', '兰蔻小黑瓶', 'SK-II神仙水',
            '欧莱雅复颜霜', '资生堂红腰子', '海蓝之谜面霜',
            '倩碧黄油', '科颜氏金盏花水', '玉兰油大红瓶',
            '完美日记口红', '花西子散粉', '薇诺娜特护霜'
        ],
        '家居用品': [
            '宜家马尔姆床', '顾家家居沙发', '索菲亚衣柜',
            '欧派橱柜', '九牧智能马桶', '箭牌卫浴花洒',
            '苏泊尔炒锅', '爱仕达压力锅', '双立人刀具',
            '富安娜四件套', '水星家纺被芯', '罗莱夏凉被'
        ],
        '运动户外': [
            '耐克篮球鞋', '阿迪达斯足球鞋', '李宁羽毛球拍',
            '亚瑟士跑鞋', '北面冲锋衣', '哥伦比亚登山鞋',
            '迪卡侬运动水壶', 'Keep瑜伽垫', '李宁运动袜',
            '斯伯丁篮球', '威尔逊网球拍', '红双喜乒乓球拍'
        ],
        '图书文具': [
            '新华字典', '现代汉语词典', '五年高考三年模拟',
            'Kindle Paperwhite', '国誉活页本', '百乐钢笔',
            '斑马中性笔', '三菱铅笔', '施德楼橡皮',
            '得力计算器', '晨光文具套装', '真彩马克笔'
        ]
    }

    # 如果没有找到匹配分类的默认商品名称
    default_names = [
        '高端商务礼品', '经典时尚单品', '智能科技产品', '优质生活用品',
        '创意设计商品', '环保健康产品', '精致工艺制品', '多功能实用工具'
    ]

    products = []
    used_codes = set()
    used_names = set()  # 避免重复商品名称

    for i in range(count):
        # 随机选择一个分类
        category = random.choice(categories)

        # 根据分类选择商品名称
        category_name = category.name
        if category_name in product_names:
            # 从该分类的商品名称列表中随机选择
            available_names = [name for name in product_names[category_name] if name not in used_names]
            if available_names:
                name = random.choice(available_names)
                used_names.add(name)
            else:
                # 如果该分类的名称都用完了，从默认名称中选择并添加分类特征
                base_name = random.choice(default_names)
                name = f"{category_name}{base_name}"
        else:
            # 对于未定义分类，使用默认名称
            base_name = random.choice(default_names)
            name = f"{category_name}{base_name}"

        # 生成唯一编码
        code = generate_unique_product_code(used_codes)
        used_codes.add(code)

        # 根据分类生成合理价格范围
        price_ranges = {
            '手机通讯': (2000, 12000),
            '电脑办公': (4000, 25000),
            '家用电器': (1000, 20000),
            '数码配件': (100, 3000),
            '食品饮料': (5, 100),
            '服装鞋帽': (50, 2000),
            '美妆护肤': (100, 3000),
            '家居用品': (200, 10000),
            '运动户外': (100, 5000),
            '图书文具': (10, 500)
        }

        price_range = price_ranges.get(category_name, (50, 2000))
        price = Decimal(random.uniform(price_range[0], price_range[1])).quantize(Decimal('0.01'))

        # 根据价格范围设置合理库存
        if price_range[1] > 5000:  # 高价商品库存较少
            stock = random.randint(5, 50)
        elif price_range[1] > 1000:  # 中等价格商品
            stock = random.randint(20, 200)
        else:  # 低价商品库存较多
            stock = random.randint(50, 500)

        products.append(Product(
            name=name,
            code=code,
            price=price,
            stock=stock
        ))

    Product.objects.bulk_create(products)
    print(f"✅ 生成 {count} 个真实商品完成")

    # 为商品分配分类
    assign_categories_to_products()


def generate_unique_product_code(used_codes):
    """生成唯一商品编码"""
    max_attempts = 100
    for attempt in range(max_attempts):
        code = f"SP{random.randint(10000, 99999)}"
        if code not in used_codes and not Product.objects.filter(code=code).exists():
            return code
    # 如果尝试多次仍然重复，使用时间戳
    return f"SP{int(timezone.now().timestamp())}{random.randint(100, 999)}"


def assign_categories_to_products():
    """为商品分配分类"""
    print("为商品分配分类...")
    categories = list(Category.objects.all())
    products = list(Product.objects.all())

    product_categories = []
    for product in products:
        # 根据商品名称智能分配分类
        assigned_categories = set()
        product_name = product.name.lower()

        # 关键词匹配分类
        category_keywords = {
            '手机通讯': ['iphone', '华为', '小米', 'oppo', 'vivo', '荣耀', '三星', '一加', '红米', '魅族', '中兴'],
            '电脑办公': ['macbook', 'thinkpad', 'matebook', 'xps', 'rog', '暗影精灵', 'surface', '机械革命', '雷蛇',
                         '宏碁', '微星', '神舟'],
            '家用电器': ['空调', '冰箱', '电视', '洗衣机', '抽油烟机', '燃气灶', '破壁机'],
            '数码配件': ['airpods', 'freebuds', 'buds', '充电器', '扩展坞', '键盘', '硬盘', '存储卡', '数据线'],
            '食品饮料': ['可乐', '牛肉面', '酸菜面', '牛奶', '安慕希', '矿泉水', '冰红茶', '凉茶', '饼干', '薯片',
                         '巧克力'],
            '服装鞋帽': ['优衣库', '李宁', '安踏', '耐克', '阿迪达斯', '匡威', 'zara', 'hm', '杰克琼斯', '太平鸟',
                         '森马', '美特斯邦威'],
            '美妆护肤': ['雅诗兰黛', '兰蔻', 'sk-ii', '欧莱雅', '资生堂', '海蓝之谜', '倩碧', '科颜氏', '玉兰油',
                         '完美日记', '花西子', '薇诺娜'],
            '家居用品': ['宜家', '顾家', '索菲亚', '欧派', '九牧', '箭牌', '苏泊尔', '爱仕达', '双立人', '富安娜',
                         '水星', '罗莱'],
            '运动户外': ['篮球鞋', '足球鞋', '羽毛球拍', '跑鞋', '冲锋衣', '登山鞋', '运动水壶', '瑜伽垫', '运动袜',
                         '篮球', '网球拍', '乒乓球拍'],
            '图书文具': ['字典', '词典', '高考', 'kindle', '活页本', '钢笔', '中性笔', '铅笔', '橡皮', '计算器', '文具',
                         '马克笔']
        }

        for category in categories:
            category_name = category.name

            # 直接匹配分类名称关键词
            if category_name in category_keywords:
                for keyword in category_keywords[category_name]:
                    if keyword in product_name:
                        assigned_categories.add(category)
                        break

        # 如果没有匹配到，随机分配1-2个分类
        if not assigned_categories:
            assigned_categories = set(random.sample(categories, random.randint(1, 2)))

        for category in assigned_categories:
            product_categories.append(ProductCategory(
                product=product, category=category
            ))

    ProductCategory.objects.bulk_create(product_categories)
    print(f"分配 {len(product_categories)} 个商品分类关联完成")


def generate_orders_and_items(count=50):
    """生成真实订单和订单明细"""
    print(f"生成 {count} 个真实订单...")
    customers = list(Customer.objects.all())
    products = list(Product.objects.all())
    status_choices = ['待处理', '已发货', '已完成']

    orders_created = 0

    for i in range(count):
        try:
            with transaction.atomic():
                customer = random.choice(customers)
                order_code = f"ORD{timezone.now().strftime('%Y%m%d')}{i + 1:04d}"

                # 订单创建时间在客户注册后随机
                days_since_reg = (timezone.now().date() - customer.reg_date).days
                if days_since_reg > 0:
                    create_days = random.randint(1, days_since_reg)
                else:
                    create_days = 1

                create_time = timezone.make_aware(
                    datetime.combine(
                        customer.reg_date + timedelta(days=create_days),
                        datetime.now().time()
                    )
                )

                # 创建订单
                order = Order.objects.create(
                    order_code=order_code,
                    customer=customer,
                    create_time=create_time,
                    status=random.choice(status_choices),
                    total_amount=Decimal('0.00')
                )

                # 生成订单明细 - 确保每个订单都有商品
                order_products = random.sample(products, random.randint(1, min(4, len(products))))
                order_total = Decimal('0.00')
                items_count = 0

                for product in order_products:
                    # 根据商品价格设置合理购买数量
                    if product.price > Decimal('1000'):
                        quantity = random.randint(1, 2)  # 高价商品购买数量少
                    elif product.price > Decimal('100'):
                        quantity = random.randint(1, 3)  # 中等价格商品
                    else:
                        quantity = random.randint(1, 5)  # 低价商品可以多买

                    unit_price = product.price
                    subtotal = unit_price * quantity
                    order_total += subtotal
                    items_count += quantity

                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=quantity,
                        unit_price=unit_price
                    )

                # 更新订单总金额
                order.total_amount = order_total
                order.save()

                orders_created += 1

                if (i + 1) % 10 == 0:
                    print(f"已生成订单: {i + 1}/{count}")

        except Exception as e:
            print(f"创建订单失败: {e}")
            continue

    print(f"生成 {orders_created} 个真实订单完成")


def print_stats():
    """打印数据统计"""
    print("\n === 真实数据统计 ===")
    print(f"客户数量: {Customer.objects.count()}")
    print(f"分类数量: {Category.objects.count()}")
    print(f"商品数量: {Product.objects.count()}")
    print(f"商品分类关联数量: {ProductCategory.objects.count()}")
    print(f"订单数量: {Order.objects.count()}")
    print(f"订单明细数量: {OrderItem.objects.count()}")

    # 显示订单详情
    print("\n=== 最近5个订单详情 ===")
    recent_orders = Order.objects.all().order_by('-create_time')[:5]
    for order in recent_orders:
        items = OrderItem.objects.filter(order=order)
        items_count = sum(item.quantity for item in items)
        print(f"订单: {order.order_code}")
        print(f"  客户: {order.customer.name} ({order.customer.phone})")
        print(f"  商品数量: {items_count}个")
        print(f"  总金额: ¥{order.total_amount}")
        print(f"  状态: {order.status}")
        print(f"  时间: {order.create_time.strftime('%Y-%m-%d %H:%M')}")
        print("  商品明细:")
        for item in items:
            print(f"    - {item.product.name} x{item.quantity} = ¥{item.unit_price * item.quantity}")
        print()

    # 显示商品示例 - 使用正确的主键字段名
    print("\n=== 商品示例 ===")
    sample_products = Product.objects.all().order_by('?')[:10]  # 随机取10个商品

    for product in sample_products:
        # 使用正确的主键字段名 category_id
        category_ids = ProductCategory.objects.filter(product=product).values_list('category_id', flat=True)
        categories = Category.objects.filter(category_id__in=category_ids)
        category_names = ", ".join([cat.name for cat in categories])
        print(f"商品: {product.name}")
        print(f"  价格: ¥{product.price} | 库存: {product.stock} | 分类: {category_names}")
    print()


if __name__ == "__main__":
    main()