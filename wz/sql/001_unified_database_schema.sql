-- WZ项目统一数据库架构设计
-- 版本: 1.0
-- 创建时间: 2025-06-19
-- 说明: 整合所有模块的数据库需求，支持多站点内容管理和发布

-- ============================================================================
-- 1. 统一文章管理表 (替代原wechat_articles表)
-- ============================================================================

CREATE TABLE `articles` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '文章唯一ID',
  
  -- 来源信息
  `source_type` ENUM('wechat', 'linux_do', 'nodeseek', 'external') NOT NULL COMMENT '来源类型',
  `source_name` VARCHAR(255) NOT NULL COMMENT '来源名称（公众号名/网站名）',
  `source_id` VARCHAR(255) DEFAULT NULL COMMENT '来源平台的文章ID',
  
  -- 基本信息
  `title` VARCHAR(512) NOT NULL COMMENT '文章标题',
  `article_url` VARCHAR(1024) NOT NULL COMMENT '文章原始链接',
  `author` VARCHAR(255) DEFAULT NULL COMMENT '作者',
  `publish_timestamp` DATETIME DEFAULT NULL COMMENT '文章发布时间',
  
  -- 采集状态
  `crawl_status` ENUM('pending', 'crawling', 'completed', 'failed', 'skipped') DEFAULT 'pending' COMMENT '采集状态',
  `crawl_attempts` INT UNSIGNED DEFAULT 0 COMMENT '采集尝试次数',
  `crawl_error` TEXT DEFAULT NULL COMMENT '采集错误信息',
  `crawled_at` TIMESTAMP NULL DEFAULT NULL COMMENT '采集完成时间',
  
  -- 内容信息
  `content` LONGTEXT DEFAULT NULL COMMENT '文章纯文本内容',
  `content_html` LONGTEXT DEFAULT NULL COMMENT '文章HTML内容',
  `word_count` INT UNSIGNED DEFAULT 0 COMMENT '文章字数',
  `images` JSON DEFAULT NULL COMMENT '文章图片信息',
  `links` JSON DEFAULT NULL COMMENT '文章链接信息',
  `tags` JSON DEFAULT NULL COMMENT '文章标签',
  
  -- AI处理字段
  `ai_title` VARCHAR(512) DEFAULT NULL COMMENT 'AI改写后的标题',
  `ai_content` LONGTEXT DEFAULT NULL COMMENT 'AI改写后的内容',
  `ai_summary` TEXT DEFAULT NULL COMMENT 'AI生成的摘要',
  
  -- 发布状态 (JSON格式存储各平台状态)
  `publish_status` JSON DEFAULT NULL COMMENT '发布状态: {"8wf_net": "completed", "00077_top": "pending"}',
  
  -- 元数据
  `fetched_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '链接获取时间',
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最后更新时间',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_source_url` (`source_type`, `article_url`(255)),
  INDEX `idx_source_type` (`source_type`),
  INDEX `idx_source_name` (`source_name`),
  INDEX `idx_crawl_status` (`crawl_status`),
  INDEX `idx_publish_timestamp` (`publish_timestamp`),
  INDEX `idx_crawled_at` (`crawled_at`),
  INDEX `idx_fetched_at` (`fetched_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='统一文章管理表';

-- ============================================================================
-- 2. 发布任务管理表
-- ============================================================================

CREATE TABLE `publish_tasks` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '任务ID',
  `article_id` BIGINT UNSIGNED NOT NULL COMMENT '关联文章ID',
  
  -- 发布目标
  `target_platform` ENUM('8wf_net', '00077_top', '1rmb_net') NOT NULL COMMENT '目标平台',
  `target_forum_id` VARCHAR(100) DEFAULT NULL COMMENT '目标版块ID',
  `target_category` VARCHAR(255) DEFAULT NULL COMMENT '目标分类',
  
  -- 任务状态
  `status` ENUM('pending', 'processing', 'completed', 'failed', 'cancelled') DEFAULT 'pending' COMMENT '任务状态',
  `priority` TINYINT UNSIGNED DEFAULT 5 COMMENT '优先级(1-10, 数字越小优先级越高)',
  `attempts` INT UNSIGNED DEFAULT 0 COMMENT '尝试次数',
  `max_attempts` INT UNSIGNED DEFAULT 3 COMMENT '最大尝试次数',
  
  -- 发布结果
  `published_url` VARCHAR(1024) DEFAULT NULL COMMENT '发布后的URL',
  `published_id` VARCHAR(255) DEFAULT NULL COMMENT '发布后的帖子ID',
  `error_message` TEXT DEFAULT NULL COMMENT '错误信息',
  `response_data` JSON DEFAULT NULL COMMENT '发布响应数据',
  
  -- 内容定制
  `custom_title` VARCHAR(512) DEFAULT NULL COMMENT '自定义标题',
  `custom_content` LONGTEXT DEFAULT NULL COMMENT '自定义内容',
  `publish_config` JSON DEFAULT NULL COMMENT '发布配置',
  
  -- 时间信息
  `scheduled_at` TIMESTAMP NULL DEFAULT NULL COMMENT '计划发布时间',
  `started_at` TIMESTAMP NULL DEFAULT NULL COMMENT '开始处理时间',
  `completed_at` TIMESTAMP NULL DEFAULT NULL COMMENT '完成时间',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  
  PRIMARY KEY (`id`),
  FOREIGN KEY (`article_id`) REFERENCES `articles`(`id`) ON DELETE CASCADE,
  INDEX `idx_article_id` (`article_id`),
  INDEX `idx_target_platform` (`target_platform`),
  INDEX `idx_status` (`status`),
  INDEX `idx_priority` (`priority`),
  INDEX `idx_scheduled_at` (`scheduled_at`),
  INDEX `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='发布任务管理表';

-- ============================================================================
-- 3. 系统配置管理表
-- ============================================================================

CREATE TABLE `system_config` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '配置ID',
  `config_key` VARCHAR(100) NOT NULL COMMENT '配置键',
  `config_value` JSON NOT NULL COMMENT '配置值',
  `config_type` ENUM('system', 'crawler', 'publisher', 'auth', 'user') DEFAULT 'system' COMMENT '配置类型',
  `description` TEXT DEFAULT NULL COMMENT '配置描述',
  `is_active` BOOLEAN DEFAULT TRUE COMMENT '是否启用',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_config_key` (`config_key`),
  INDEX `idx_config_type` (`config_type`),
  INDEX `idx_is_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统配置管理表';

-- ============================================================================
-- 4. 认证信息管理表
-- ============================================================================

CREATE TABLE `auth_credentials` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '凭证ID',
  `platform` VARCHAR(50) NOT NULL COMMENT '平台名称',
  `credential_type` ENUM('cookie', 'token', 'api_key', 'username_password') NOT NULL COMMENT '凭证类型',
  `credential_data` JSON NOT NULL COMMENT '凭证数据(加密存储)',
  `expires_at` TIMESTAMP NULL DEFAULT NULL COMMENT '过期时间',
  `is_active` BOOLEAN DEFAULT TRUE COMMENT '是否有效',
  `last_used_at` TIMESTAMP NULL DEFAULT NULL COMMENT '最后使用时间',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_platform_type` (`platform`, `credential_type`),
  INDEX `idx_platform` (`platform`),
  INDEX `idx_expires_at` (`expires_at`),
  INDEX `idx_is_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='认证信息管理表';

-- ============================================================================
-- 5. 操作日志表
-- ============================================================================

CREATE TABLE `operation_logs` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '日志ID',
  `operation_type` ENUM('crawl', 'publish', 'auth', 'config', 'system') NOT NULL COMMENT '操作类型',
  `operation_action` VARCHAR(100) NOT NULL COMMENT '操作动作',
  `target_type` VARCHAR(50) DEFAULT NULL COMMENT '目标类型',
  `target_id` VARCHAR(255) DEFAULT NULL COMMENT '目标ID',
  `user_id` VARCHAR(100) DEFAULT 'system' COMMENT '操作用户',
  `status` ENUM('success', 'failed', 'warning') NOT NULL COMMENT '操作状态',
  `message` TEXT DEFAULT NULL COMMENT '操作消息',
  `details` JSON DEFAULT NULL COMMENT '详细信息',
  `duration_ms` INT UNSIGNED DEFAULT NULL COMMENT '操作耗时(毫秒)',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  
  PRIMARY KEY (`id`),
  INDEX `idx_operation_type` (`operation_type`),
  INDEX `idx_operation_action` (`operation_action`),
  INDEX `idx_target_type_id` (`target_type`, `target_id`),
  INDEX `idx_status` (`status`),
  INDEX `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='操作日志表';

-- ============================================================================
-- 6. 初始化配置数据
-- ============================================================================

-- 插入默认系统配置
INSERT INTO `system_config` (`config_key`, `config_value`, `config_type`, `description`) VALUES
('database.connection', '{"host": "140.238.201.162", "port": 3306, "database": "cj", "charset": "utf8mb4"}', 'system', '数据库连接配置'),
('crawler.wechat.enabled', 'true', 'crawler', '是否启用微信公众号采集'),
('crawler.wechat.batch_size', '10', 'crawler', '微信公众号批量采集数量'),
('crawler.cfcj.enabled', 'true', 'crawler', '是否启用CFCJ内容采集'),
('crawler.cfcj.retry_times', '3', 'crawler', 'CFCJ采集重试次数'),
('publisher.8wf_net.enabled', 'false', 'publisher', '是否启用8wf.net发布'),
('publisher.00077_top.enabled', 'false', 'publisher', '是否启用00077.top发布'),
('publisher.1rmb_net.enabled', 'false', 'publisher', '是否启用1rmb.net发布'),
('system.auto_crawl_interval', '3600', 'system', '自动采集间隔(秒)'),
('system.auto_publish_enabled', 'false', 'system', '是否启用自动发布');

-- ============================================================================
-- 7. 创建视图简化查询
-- ============================================================================

-- 文章状态概览视图
CREATE VIEW `v_article_status` AS
SELECT 
    source_type,
    source_name,
    COUNT(*) as total_articles,
    SUM(CASE WHEN crawl_status = 'completed' THEN 1 ELSE 0 END) as crawled_articles,
    SUM(CASE WHEN crawl_status = 'pending' THEN 1 ELSE 0 END) as pending_articles,
    SUM(CASE WHEN crawl_status = 'failed' THEN 1 ELSE 0 END) as failed_articles,
    MAX(fetched_at) as last_fetch_time,
    MAX(crawled_at) as last_crawl_time
FROM articles 
GROUP BY source_type, source_name;

-- 发布任务状态视图
CREATE VIEW `v_publish_status` AS
SELECT 
    target_platform,
    COUNT(*) as total_tasks,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_tasks,
    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_tasks,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_tasks,
    AVG(attempts) as avg_attempts
FROM publish_tasks 
GROUP BY target_platform;
