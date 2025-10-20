CREATE TABLE `customer` (
  `customer_id` INT NOT NULL AUTO_INCREMENT COMMENT '客户ID',
  `name` VARCHAR(100) NOT NULL COMMENT '客户姓名',
  `phone` VARCHAR(20) NOT NULL COMMENT '手机号',
  `address` VARCHAR(255) NOT NULL COMMENT '地址',
  `reg_date` DATE NOT NULL COMMENT '注册日期',
  PRIMARY KEY (`customer_id`),
  UNIQUE KEY `phone` (`phone`),
  INDEX `idx_customer_phone` (`phone`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='客户表';



CREATE TABLE `category` (
  `category_id` INT NOT NULL AUTO_INCREMENT COMMENT '分类ID',
  `name` VARCHAR(50) NOT NULL COMMENT '分类名称',
  `description` TEXT NULL COMMENT '分类描述',
  PRIMARY KEY (`category_id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品分类表';


-- 3. 商品表（product）- 无外键依赖
CREATE TABLE `product` (
  `product_id` INT NOT NULL AUTO_INCREMENT COMMENT '商品ID',
  `name` VARCHAR(100) NOT NULL COMMENT '商品名称',
  `code` VARCHAR(50) NOT NULL COMMENT '商品编码',
  `price` DECIMAL(10, 2) NOT NULL COMMENT '单价',
  `stock` INT NOT NULL DEFAULT 0 COMMENT '库存数量',
  PRIMARY KEY (`product_id`),
  UNIQUE KEY `code` (`code`),
  INDEX `idx_product_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品表';



CREATE TABLE `product_category` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT '关联ID',
  `product_id` INT NOT NULL COMMENT '商品',
  `category_id` INT NOT NULL COMMENT '分类',
  PRIMARY KEY (`id`),

  UNIQUE KEY `uk_prod_cat` (`product_id`, `category_id`),

  CONSTRAINT `product_category_product_id_fk`
    FOREIGN KEY (`product_id`)
    REFERENCES `product` (`product_id`)
    ON DELETE CASCADE,

  CONSTRAINT `product_category_category_id_fk`
    FOREIGN KEY (`category_id`)
    REFERENCES `category` (`category_id`)
    ON DELETE CASCADE,

  INDEX `product_category_category_id_idx` (`category_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品-分类关联表';


CREATE TABLE `shop_order` (
  `order_id` INT NOT NULL AUTO_INCREMENT COMMENT '订单ID',
  `order_code` VARCHAR(50) NOT NULL COMMENT '订单编号',
  `customer_id` INT NOT NULL COMMENT '客户',  -- 关联 Customer 表
  `create_time` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '创建时间',
  `status` VARCHAR(10) NOT NULL COMMENT '订单状态（待处理/已发货/已完成）',
  `total_amount` DECIMAL(12, 2) NOT NULL COMMENT '订单总金额',
  PRIMARY KEY (`order_id`),
  UNIQUE KEY `order_code` (`order_code`),
  INDEX `idx_order_code` (`order_code`),
  INDEX `idx_order_status` (`status`),
  CONSTRAINT `shop_order_customer_id_fk`
    FOREIGN KEY (`customer_id`)
    REFERENCES `customer` (`customer_id`)
    ON DELETE RESTRICT  -- 修复：将PROTECT改为MySQL支持的RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='订单表';


CREATE TABLE `shop_order_item` (
  `item_id` INT NOT NULL AUTO_INCREMENT COMMENT '明细ID',
  `order_id` INT NOT NULL COMMENT '订单',
  `product_id` INT NOT NULL COMMENT '商品',
  `quantity` INT NOT NULL COMMENT '购买数量',
  `unit_price` DECIMAL(10, 2) NOT NULL COMMENT '单价',
  PRIMARY KEY (`item_id`),

  INDEX `idx_order_item` (`order_id`, `product_id`),

  CONSTRAINT `shop_order_item_order_id_fk`
    FOREIGN KEY (`order_id`)
    REFERENCES `shop_order` (`order_id`)
    ON DELETE CASCADE,

  CONSTRAINT `shop_order_item_product_id_fk`
    FOREIGN KEY (`product_id`)
    REFERENCES `product` (`product_id`)
    ON DELETE RESTRICT,  -- 修复：将PROTECT改为MySQL支持的RESTRICT

  INDEX `shop_order_item_product_id_idx` (`product_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='订单明细表';



CREATE TABLE `access_logs` (
  `log_id` INT NOT NULL AUTO_INCREMENT COMMENT '日志ID',
  `user_id` INT NULL COMMENT '访问用户',
  `path` VARCHAR(255) NOT NULL COMMENT '访问路径',
  `start_time` DATETIME(6) NOT NULL COMMENT '开始时间',
  `end_time` DATETIME(6) NOT NULL COMMENT '结束时间',
  `duration` FLOAT NOT NULL COMMENT '访问耗时（秒）',
  `ip` VARCHAR(50) NOT NULL COMMENT '访问IP',
  PRIMARY KEY (`log_id`),

  INDEX `idx_log_user` (`user_id`, `start_time`),

  CONSTRAINT `access_logs_user_id_fk`
    FOREIGN KEY (`user_id`)
    REFERENCES `auth_user` (`id`)  -- 注意：需确保`auth_user`表已创建
    ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='访问性能日志表';