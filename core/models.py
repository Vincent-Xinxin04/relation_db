# core/models.py
from django.db import models
from django.contrib.auth.models import User


class Customer(models.Model):
    """客户表（无修改）"""
    customer_id = models.AutoField(primary_key=True, verbose_name="客户ID")
    name = models.CharField(max_length=100, verbose_name="客户姓名")
    phone = models.CharField(max_length=20, unique=True, verbose_name="手机号")
    address = models.CharField(max_length=255, verbose_name="地址")
    reg_date = models.DateField(verbose_name="注册日期")

    class Meta:
        db_table = "customer"  # 不变
        verbose_name = "客户"
        verbose_name_plural = "客户"
        indexes = [models.Index(fields=["phone"], name="idx_customer_phone")]

    def __str__(self):
        return f"{self.name}（{self.phone}）"


class Category(models.Model):
    """商品分类表（无修改）"""
    category_id = models.AutoField(primary_key=True, verbose_name="分类ID")
    name = models.CharField(max_length=50, unique=True, verbose_name="分类名称")
    description = models.TextField(null=True, blank=True, verbose_name="分类描述")

    class Meta:
        db_table = "category"  # 不变
        verbose_name = "商品分类"
        verbose_name_plural = "商品分类"

    def __str__(self):
        return self.name


class Product(models.Model):
    """商品表（无修改）"""
    product_id = models.AutoField(primary_key=True, verbose_name="商品ID")
    name = models.CharField(max_length=100, verbose_name="商品名称")
    code = models.CharField(max_length=50, unique=True, verbose_name="商品编码")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="单价")
    stock = models.IntegerField(default=0, verbose_name="库存数量")
    categories = models.ManyToManyField(
        Category,
        through="ProductCategory",
        through_fields=("product", "category"),
        verbose_name="关联分类"
    )

    class Meta:
        db_table = "product"  # 不变
        verbose_name = "商品"
        verbose_name_plural = "商品"
        indexes = [models.Index(fields=["code"], name="idx_product_code")]

    def __str__(self):
        return f"{self.name}（{self.code}）"


class ProductCategory(models.Model):
    """商品-分类中间表（无修改）"""
    id = models.AutoField(primary_key=True, verbose_name="关联ID")
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="product_categories",
        verbose_name="商品"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="product_categories",
        verbose_name="分类"
    )

    class Meta:
        db_table = "product_category"  # 不变
        verbose_name = "商品-分类关联"
        verbose_name_plural = "商品-分类关联"
        constraints = [models.UniqueConstraint(fields=["product", "category"], name="uk_prod_cat")]

    def __str__(self):
        return f"{self.product.name} - {self.category.name}"


class Order(models.Model):
    """订单表（关键修改：db_table改为orders，外键关联不变）"""
    ORDER_STATUS = (("待处理", "待处理"), ("已发货", "已发货"), ("已完成", "已完成"))
    order_id = models.AutoField(primary_key=True, verbose_name="订单ID")
    order_code = models.CharField(max_length=50, unique=True, verbose_name="订单编号")
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name="orders",
        verbose_name="客户"
    )
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    status = models.CharField(max_length=10, choices=ORDER_STATUS, verbose_name="订单状态")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="订单总金额")

    class Meta:
        db_table = "shop_order"  # 关键：避开关键字 order
        verbose_name = "订单"
        verbose_name_plural = "订单"
        indexes = [
            models.Index(fields=["order_code"], name="idx_order_code"),
            models.Index(fields=["status"], name="idx_order_status"),
        ]

    def __str__(self):
        return f"{self.order_code}（{self.status}）"


class OrderItem(models.Model):
    """订单明细表（关键修改：db_table改为order_items，外键指向Order）"""
    item_id = models.AutoField(primary_key=True, verbose_name="明细ID")
    order = models.ForeignKey(
        Order,  # 关联修改后的Order模型（对应orders表）
        on_delete=models.CASCADE,
        related_name="order_items",
        verbose_name="订单"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        verbose_name="商品"
    )
    quantity = models.IntegerField(verbose_name="购买数量")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="单价")

    class Meta:
        db_table = "shop_order_item"     # 同步修改明细表
        verbose_name = "订单明细"
        verbose_name_plural = "订单明细"
        indexes = [models.Index(fields=["order", "product"], name="idx_order_item")]

    def __str__(self):
        return f"{self.order.order_code} - {self.product.name}（{self.quantity}件）"


class AccessLog(models.Model):
    """访问日志表（无修改）"""
    log_id = models.AutoField(primary_key=True, verbose_name="日志ID")
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="access_logs",
        verbose_name="访问用户"
    )
    path = models.CharField(max_length=255, verbose_name="访问路径")
    start_time = models.DateTimeField(verbose_name="开始时间")
    end_time = models.DateTimeField(verbose_name="结束时间")
    duration = models.FloatField(verbose_name="访问耗时（秒）")
    ip = models.CharField(max_length=50, verbose_name="访问IP")

    class Meta:
        db_table = "access_logs"  # 不变
        verbose_name = "访问日志"
        verbose_name_plural = "访问日志"
        indexes = [models.Index(fields=["user", "start_time"], name="idx_log_user")]

    def __str__(self):
        return f"{self.user.username if self.user else '匿名用户'} - {self.path}（{self.duration}s）"