-- 扩展wechat_articles表结构，添加内容存储和AI处理字段
-- 执行前请备份数据库

-- 添加内容字段
ALTER TABLE `wechat_articles` 
ADD COLUMN `content` LONGTEXT COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '文章完整内容' AFTER `source_type`;

-- 添加AI处理字段
ALTER TABLE `wechat_articles` 
ADD COLUMN `ai_title` VARCHAR(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'AI改写后的标题' AFTER `content`;

ALTER TABLE `wechat_articles` 
ADD COLUMN `ai_content` LONGTEXT COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'AI改写后的内容' AFTER `ai_title`;

-- 添加图片信息字段
ALTER TABLE `wechat_articles` 
ADD COLUMN `images` JSON DEFAULT NULL COMMENT '文章图片信息(JSON格式)' AFTER `ai_content`;

-- 添加采集状态字段
ALTER TABLE `wechat_articles` 
ADD COLUMN `crawl_status` TINYINT(1) DEFAULT 0 COMMENT '采集状态: 0-未采集, 1-已采集, 2-采集失败' AFTER `images`;

-- 添加错误信息字段
ALTER TABLE `wechat_articles` 
ADD COLUMN `error_message` TEXT COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '采集错误信息' AFTER `crawl_status`;

-- 添加站点类型字段
ALTER TABLE `wechat_articles` 
ADD COLUMN `site_name` VARCHAR(100) COLLATE utf8mb4_unicode_ci DEFAULT 'wechat' COMMENT '站点名称' AFTER `error_message`;

-- 添加字数统计字段
ALTER TABLE `wechat_articles` 
ADD COLUMN `word_count` INT DEFAULT 0 COMMENT '文章字数' AFTER `site_name`;

-- 添加采集完成时间字段
ALTER TABLE `wechat_articles` 
ADD COLUMN `crawled_at` TIMESTAMP NULL DEFAULT NULL COMMENT '内容采集完成时间' AFTER `word_count`;

-- 添加索引优化查询性能
CREATE INDEX `idx_crawl_status` ON `wechat_articles` (`crawl_status`);
CREATE INDEX `idx_site_name` ON `wechat_articles` (`site_name`);
CREATE INDEX `idx_crawled_at` ON `wechat_articles` (`crawled_at`);

-- 查看表结构
DESCRIBE `wechat_articles`;
