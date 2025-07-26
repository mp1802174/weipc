-- WZ项目数据迁移脚本
-- 从现有wechat_articles表迁移到新的统一表结构
-- 版本: 1.0
-- 创建时间: 2025-06-19

-- ============================================================================
-- 数据迁移前的准备工作
-- ============================================================================

-- 1. 备份现有数据
CREATE TABLE `wechat_articles_backup_20250619` AS 
SELECT * FROM `wechat_articles`;

-- 2. 检查现有表结构
DESCRIBE `wechat_articles`;

-- 3. 统计现有数据
SELECT 
    COUNT(*) as total_records,
    COUNT(DISTINCT account_name) as unique_accounts,
    MIN(publish_timestamp) as earliest_article,
    MAX(publish_timestamp) as latest_article,
    MIN(fetched_at) as first_fetch,
    MAX(fetched_at) as last_fetch
FROM `wechat_articles`;

-- ============================================================================
-- 执行数据迁移
-- ============================================================================

-- 1. 迁移基础文章数据
INSERT INTO `articles` (
    `source_type`,
    `source_name`, 
    `title`,
    `article_url`,
    `publish_timestamp`,
    `crawl_status`,
    `content`,
    `content_html`,
    `word_count`,
    `images`,
    `crawl_error`,
    `crawled_at`,
    `fetched_at`,
    `created_at`
)
SELECT 
    'wechat' as source_type,
    `account_name` as source_name,
    `title`,
    `article_url`,
    `publish_timestamp`,
    CASE 
        WHEN `crawl_status` = 1 THEN 'completed'
        WHEN `crawl_status` = 2 THEN 'failed'
        ELSE 'pending'
    END as crawl_status,
    `content`,
    `content` as content_html,  -- 如果没有HTML内容，使用纯文本
    COALESCE(`word_count`, 0) as word_count,
    `images`,
    `error_message` as crawl_error,
    `crawled_at`,
    `fetched_at`,
    `fetched_at` as created_at
FROM `wechat_articles`
WHERE `article_url` IS NOT NULL 
  AND `article_url` != ''
  AND `title` IS NOT NULL 
  AND `title` != '';

-- 2. 处理重复数据（如果存在）
-- 删除重复的URL记录，保留最新的
DELETE a1 FROM `articles` a1
INNER JOIN `articles` a2 
WHERE a1.id < a2.id 
  AND a1.source_type = a2.source_type 
  AND a1.article_url = a2.article_url;

-- 3. 更新字数统计（如果原来为0或NULL）
UPDATE `articles` 
SET `word_count` = CHAR_LENGTH(REGEXP_REPLACE(`content`, '[^\\u4e00-\\u9fa5a-zA-Z0-9]', ''))
WHERE `word_count` = 0 
  AND `content` IS NOT NULL 
  AND `content` != '';

-- ============================================================================
-- 数据验证和修复
-- ============================================================================

-- 1. 验证迁移结果
SELECT 
    '迁移验证' as check_type,
    COUNT(*) as migrated_records,
    COUNT(DISTINCT source_name) as unique_sources,
    SUM(CASE WHEN crawl_status = 'completed' THEN 1 ELSE 0 END) as completed_crawls,
    SUM(CASE WHEN crawl_status = 'pending' THEN 1 ELSE 0 END) as pending_crawls,
    SUM(CASE WHEN crawl_status = 'failed' THEN 1 ELSE 0 END) as failed_crawls
FROM `articles` 
WHERE `source_type` = 'wechat';

-- 2. 检查数据完整性
SELECT 
    '数据完整性检查' as check_type,
    SUM(CASE WHEN title IS NULL OR title = '' THEN 1 ELSE 0 END) as empty_titles,
    SUM(CASE WHEN article_url IS NULL OR article_url = '' THEN 1 ELSE 0 END) as empty_urls,
    SUM(CASE WHEN source_name IS NULL OR source_name = '' THEN 1 ELSE 0 END) as empty_sources,
    SUM(CASE WHEN publish_timestamp IS NULL THEN 1 ELSE 0 END) as null_timestamps
FROM `articles` 
WHERE `source_type` = 'wechat';

-- 3. 修复可能的数据问题
-- 修复空的发布时间
UPDATE `articles` 
SET `publish_timestamp` = `fetched_at`
WHERE `publish_timestamp` IS NULL 
  AND `fetched_at` IS NOT NULL
  AND `source_type` = 'wechat';

-- 修复空的来源名称
UPDATE `articles` 
SET `source_name` = '未知公众号'
WHERE (`source_name` IS NULL OR `source_name` = '')
  AND `source_type` = 'wechat';

-- ============================================================================
-- 创建迁移后的索引优化
-- ============================================================================

-- 分析表以优化查询性能
ANALYZE TABLE `articles`;
ANALYZE TABLE `publish_tasks`;
ANALYZE TABLE `system_config`;

-- ============================================================================
-- 迁移验证查询
-- ============================================================================

-- 对比迁移前后的数据统计
SELECT 
    'wechat_articles原表' as table_name,
    COUNT(*) as record_count,
    COUNT(DISTINCT account_name) as unique_accounts
FROM `wechat_articles`

UNION ALL

SELECT 
    'articles新表(微信)' as table_name,
    COUNT(*) as record_count,
    COUNT(DISTINCT source_name) as unique_sources
FROM `articles` 
WHERE `source_type` = 'wechat';

-- 检查URL唯一性
SELECT 
    article_url,
    COUNT(*) as duplicate_count
FROM `articles` 
WHERE `source_type` = 'wechat'
GROUP BY article_url 
HAVING COUNT(*) > 1
LIMIT 10;

-- 检查最近的文章
SELECT 
    source_name,
    title,
    article_url,
    publish_timestamp,
    crawl_status,
    fetched_at
FROM `articles` 
WHERE `source_type` = 'wechat'
ORDER BY `fetched_at` DESC 
LIMIT 10;

-- ============================================================================
-- 清理和优化建议
-- ============================================================================

-- 1. 如果迁移成功，可以考虑重命名原表（而不是删除）
-- RENAME TABLE `wechat_articles` TO `wechat_articles_deprecated_20250619`;

-- 2. 创建同义词视图以保持向后兼容性
CREATE VIEW `wechat_articles_view` AS
SELECT 
    id,
    source_name as account_name,
    title,
    article_url,
    publish_timestamp,
    CASE 
        WHEN crawl_status = 'completed' THEN 1
        WHEN crawl_status = 'failed' THEN 2
        ELSE 0
    END as crawl_status,
    content,
    word_count,
    images,
    crawl_error as error_message,
    'wechat' as site_name,
    crawled_at,
    fetched_at
FROM `articles` 
WHERE `source_type` = 'wechat';

-- 3. 更新统计信息
UPDATE `system_config` 
SET `config_value` = JSON_OBJECT(
    'last_migration', NOW(),
    'migrated_records', (SELECT COUNT(*) FROM `articles` WHERE `source_type` = 'wechat'),
    'migration_version', '1.0'
)
WHERE `config_key` = 'system.migration_status'
ON DUPLICATE KEY INSERT (`config_key`, `config_value`, `config_type`, `description`) 
VALUES ('system.migration_status', JSON_OBJECT(
    'last_migration', NOW(),
    'migrated_records', (SELECT COUNT(*) FROM `articles` WHERE `source_type` = 'wechat'),
    'migration_version', '1.0'
), 'system', '数据迁移状态记录');

-- ============================================================================
-- 迁移完成报告
-- ============================================================================

SELECT 
    '=== 数据迁移完成报告 ===' as report_section,
    '' as details

UNION ALL

SELECT 
    '原表记录数',
    CAST(COUNT(*) AS CHAR) as details
FROM `wechat_articles`

UNION ALL

SELECT 
    '新表记录数',
    CAST(COUNT(*) AS CHAR) as details
FROM `articles` 
WHERE `source_type` = 'wechat'

UNION ALL

SELECT 
    '迁移完成时间',
    NOW() as details

UNION ALL

SELECT 
    '建议下一步',
    '1. 测试应用程序功能 2. 更新代码使用新表 3. 备份原表后删除' as details;
