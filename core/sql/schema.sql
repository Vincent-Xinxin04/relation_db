-- 1. 客户表（customer）- 无外键依赖，优先创建
CREATE TABLE `customer` (
  `customer_id` INT NOT NULL AUTO_INCREMENT COMMENT '客户ID',
  `name` VARCHAR(100) NOT NULL COMMENT '客户姓名',
  `phone` VARCHAR(20) NOT NULL COMMENT '手机号',
  `address` VARCHAR(255) NOT NULL COMMENT '地址',
  `reg_date` DATE NOT NULL COMMENT '注册日期',
  PRIMARY KEY (`customer_id`),
  UNIQUE KEY `phone` (`phone`),  -- 对应 phone 字段的 unique=True
  INDEX `idx_customer_phone` (`phone`)  -- 对应 Meta 中的索引配置
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='客户表';


-- 2. 商品分类表（category）- 无外键依赖
CREATE TABLE `category` (
  `category_id` INT NOT NULL AUTO_INCREMENT COMMENT '分类ID',
  `name` VARCHAR(50) NOT NULL COMMENT '分类名称',
  `description` TEXT NULL COMMENT '分类描述',  -- 对应 null=True, blank=True
  PRIMARY KEY (`category_id`),
  UNIQUE KEY `name` (`name`)  -- 对应 name 字段的 unique=True
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品分类表';


-- 3. 商品表（product）- 无外键依赖
CREATE TABLE `product` (
  `product_id` INT NOT NULL AUTO_INCREMENT COMMENT '商品ID',
  `name` VARCHAR(100) NOT NULL COMMENT '商品名称',
  `code` VARCHAR(50) NOT NULL COMMENT '商品编码',
  `price` DECIMAL(10, 2) NOT NULL COMMENT '单价',
  `stock` INT NOT NULL DEFAULT 0 COMMENT '库存数量',  -- 对应 default=0
  PRIMARY KEY (`product_id`),
  UNIQUE KEY `code` (`code`),  -- 对应 code 字段的 unique=True
  INDEX `idx_product_code` (`code`)  -- 对应 Meta 中的索引配置
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品表';


-- 4. 商品-分类中间表（product_category）- 依赖 product 和 category
CREATE TABLE `product_category` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT '关联ID',
  `product_id` INT NOT NULL COMMENT '商品',  -- 关联 Product 表
  `category_id` INT NOT NULL COMMENT '分类',  -- 关联 Category 表
  PRIMARY KEY (`id`),
  -- 对应 Meta 中的 unique 约束：uk_prod_cat（product + category 组合唯一）
  UNIQUE KEY `uk_prod_cat` (`product_id`, `category_id`),
  -- 外键：product_id 关联 Product，删除商品时同步删除关联记录（CASCADE）
  CONSTRAINT `product_category_product_id_fk`
    FOREIGN KEY (`product_id`)
    REFERENCES `product` (`product_id`)
    ON DELETE CASCADE,
  -- 外键：category_id 关联 Category，删除分类时同步删除关联记录（CASCADE）
  CONSTRAINT `product_category_category_id_fk`
    FOREIGN KEY (`category_id`)
    REFERENCES `category` (`category_id`)
    ON DELETE CASCADE,
  -- 优化查询的索引（可选，因外键会自动创建索引，此处为显式对齐 Model 逻辑）
  INDEX `product_category_category_id_idx` (`category_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品-分类关联表';


-- 5. 订单表（shop_order）- 依赖 customer，避开 order 关键字
CREATE TABLE `shop_order` (
  `order_id` INT NOT NULL AUTO_INCREMENT COMMENT '订单ID',
  `order_code` VARCHAR(50) NOT NULL COMMENT '订单编号',
  `customer_id` INT NOT NULL COMMENT '客户',  -- 关联 Customer 表
  `create_time` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '创建时间',  -- 对应 auto_now_add=True
  `status` VARCHAR(10) NOT NULL COMMENT '订单状态（待处理/已发货/已完成）',
  `total_amount` DECIMAL(12, 2) NOT NULL COMMENT '订单总金额',
  PRIMARY KEY (`order_id`),
  UNIQUE KEY `order_code` (`order_code`),  -- 对应 order_code 字段的 unique=True
  -- 对应 Meta 中的索引配置
  INDEX `idx_order_code` (`order_code`),
  INDEX `idx_order_status` (`status`),
  -- 外键：customer_id 关联 Customer，禁止删除关联客户（PROTECT）
  CONSTRAINT `shop_order_customer_id_fk`
    FOREIGN KEY (`customer_id`)
    REFERENCES `customer` (`customer_id`)
    ON DELETE PROTECT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='订单表';


-- 6. 订单明细表（shop_order_item）- 依赖 shop_order 和 product
CREATE TABLE `shop_order_item` (
  `item_id` INT NOT NULL AUTO_INCREMENT COMMENT '明细ID',
  `order_id` INT NOT NULL COMMENT '订单',  -- 关联 shop_order 表
  `product_id` INT NOT NULL COMMENT '商品',  -- 关联 Product 表
  `quantity` INT NOT NULL COMMENT '购买数量',
  `unit_price` DECIMAL(10, 2) NOT NULL COMMENT '单价',
  PRIMARY KEY (`item_id`),
  -- 对应 Meta 中的复合索引：idx_order_item（order + product）
  INDEX `idx_order_item` (`order_id`, `product_id`),
  -- 外键：order_id 关联 shop_order，删除订单时同步删除明细（CASCADE）
  CONSTRAINT `shop_order_item_order_id_fk`
    FOREIGN KEY (`order_id`)
    REFERENCES `shop_order` (`order_id`)
    ON DELETE CASCADE,
  -- 外键：product_id 关联 Product，禁止删除关联商品（PROTECT）
  CONSTRAINT `shop_order_item_product_id_fk`
    FOREIGN KEY (`product_id`)
    REFERENCES `product` (`product_id`)
    ON DELETE PROTECT,
  -- 优化查询的索引（可选，因外键会自动创建索引）
  INDEX `shop_order_item_product_id_idx` (`product_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='订单明细表';


-- 7. 访问性能日志表（access_logs）- 依赖 Django 内置 auth_user 表
CREATE TABLE `access_logs` (
  `log_id` INT NOT NULL AUTO_INCREMENT COMMENT '日志ID',
  `user_id` INT NULL COMMENT '访问用户',  -- 关联 auth_user 表（可空）
  `path` VARCHAR(255) NOT NULL COMMENT '访问路径',
  `start_time` DATETIME(6) NOT NULL COMMENT '开始时间',
  `end_time` DATETIME(6) NOT NULL COMMENT '结束时间',
  `duration` FLOAT NOT NULL COMMENT '访问耗时（秒）',
  `ip` VARCHAR(50) NOT NULL COMMENT '访问IP',
  PRIMARY KEY (`log_id`),
  -- 对应 Meta 中的复合索引：idx_log_user（user + start_time）
  INDEX `idx_log_user` (`user_id`, `start_time`),
  -- 外键：user_id 关联 auth_user，删除用户时设为 NULL（SET_NULL）
  CONSTRAINT `access_logs_user_id_fk`
    FOREIGN KEY (`user_id`)
    REFERENCES `auth_user` (`id`)
    ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='访问性能日志表';