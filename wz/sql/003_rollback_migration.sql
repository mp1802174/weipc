-- WZ项目数据库迁移回滚脚本
-- 用于在迁移出现问题时恢复到原始状态
-- 版本: 1.0
-- 创建时间: 2025-06-19
-- 警告: 执行此脚本将删除新表结构并恢复原始数据

-- ============================================================================
-- 回滚前的安全检查
-- ============================================================================

-- 1. 检查备份表是否存在
SELECT 
    TABLE_NAME,
    TABLE_ROWS,
    CREATE_TIME
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_SCHEMA = DATABASE() 
  AND TABLE_NAME LIKE 'wechat_articles_backup_%'
ORDER BY CREATE_TIME DESC;

-- 2. 显示当前新表的数据统计
SELECT 
    '新表数据统计' as info_type,
    COUNT(*) as total_records,
    COUNT(DISTINCT source_name) as unique_sources,
    MIN(created_at) as earliest_record,
    MAX(created_at) as latest_record
FROM `articles` 
WHERE `source_type` = 'wechat';

-- ============================================================================
-- 执行回滚操作
-- ============================================================================

-- 注意: 以下操作需要手动确认执行，请根据实际情况修改备份表名

-- 1. 删除新创建的表（请谨慎执行）
-- DROP TABLE IF EXISTS `articles`;
-- DROP TABLE IF EXISTS `publish_tasks`;
-- DROP TABLE IF EXISTS `system_config`;
-- DROP TABLE IF EXISTS `auth_credentials`;
-- DROP TABLE IF EXISTS `operation_logs`;

-- 2. 删除创建的视图
-- DROP VIEW IF EXISTS `v_article_status`;
-- DROP VIEW IF EXISTS `v_publish_status`;
-- DROP VIEW IF EXISTS `wechat_articles_view`;

-- 3. 恢复原始表（请替换为实际的备份表名）
-- 示例: 如果备份表名为 wechat_articles_backup_20250619_143000
-- RENAME TABLE `wechat_articles_backup_20250619_143000` TO `wechat_articles`;

-- ============================================================================
-- 回滚脚本模板（需要手动执行）
-- ============================================================================

/*
-- 步骤1: 确认备份表名
SHOW TABLES LIKE 'wechat_articles_backup_%';

-- 步骤2: 删除新表（请确认后执行）
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `publish_tasks`;
DROP TABLE IF EXISTS `articles`;
DROP TABLE IF EXISTS `system_config`;
DROP TABLE IF EXISTS `auth_credentials`;
DROP TABLE IF EXISTS `operation_logs`;

DROP VIEW IF EXISTS `v_article_status`;
DROP VIEW IF EXISTS `v_publish_status`;
DROP VIEW IF EXISTS `wechat_articles_view`;

SET FOREIGN_KEY_CHECKS = 1;

-- 步骤3: 恢复原始表（请替换实际备份表名）
-- RENAME TABLE `wechat_articles_backup_YYYYMMDD_HHMMSS` TO `wechat_articles`;

-- 步骤4: 验证恢复结果
SELECT 
    COUNT(*) as total_records,
    COUNT(DISTINCT account_name) as unique_accounts,
    MIN(publish_timestamp) as earliest_article,
    MAX(publish_timestamp) as latest_article
FROM `wechat_articles`;
*/

-- ============================================================================
-- 自动回滚脚本生成器
-- ============================================================================

-- 生成回滚命令（需要复制执行）
SELECT CONCAT(
    'RENAME TABLE `', 
    TABLE_NAME, 
    '` TO `wechat_articles`;'
) as rollback_command
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_SCHEMA = DATABASE() 
  AND TABLE_NAME LIKE 'wechat_articles_backup_%'
ORDER BY CREATE_TIME DESC 
LIMIT 1;

-- ============================================================================
-- 数据完整性验证查询
-- ============================================================================

-- 在回滚后执行以下查询验证数据完整性

-- 1. 基本统计
/*
SELECT 
    '回滚后验证' as check_type,
    COUNT(*) as total_records,
    COUNT(DISTINCT account_name) as unique_accounts,
    COUNT(CASE WHEN title IS NOT NULL AND title != '' THEN 1 END) as valid_titles,
    COUNT(CASE WHEN article_url IS NOT NULL AND article_url != '' THEN 1 END) as valid_urls
FROM `wechat_articles`;
*/

-- 2. 检查数据类型
/*
DESCRIBE `wechat_articles`;
*/

-- 3. 检查最新记录
/*
SELECT 
    account_name,
    title,
    article_url,
    publish_timestamp,
    fetched_at
FROM `wechat_articles`
ORDER BY fetched_at DESC
LIMIT 10;
*/

-- ============================================================================
-- 清理临时文件和日志
-- ============================================================================

-- 在确认回滚成功后，可以清理相关文件
-- 1. 删除迁移日志文件
-- 2. 删除备份表（如果确认不再需要）
-- 3. 重置应用程序配置

-- 删除多余的备份表（保留最新的一个）
/*
-- 查看所有备份表
SELECT 
    TABLE_NAME,
    CREATE_TIME,
    TABLE_ROWS
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_SCHEMA = DATABASE() 
  AND TABLE_NAME LIKE 'wechat_articles_backup_%'
ORDER BY CREATE_TIME DESC;

-- 删除旧的备份表（请手动确认）
-- DROP TABLE `wechat_articles_backup_old1`;
-- DROP TABLE `wechat_articles_backup_old2`;
*/

-- ============================================================================
-- 回滚完成检查清单
-- ============================================================================

/*
回滚完成后请检查以下项目:

□ 1. wechat_articles表已恢复
□ 2. 数据记录数正确
□ 3. 表结构正确
□ 4. 应用程序可以正常连接
□ 5. 所有功能正常工作
□ 6. 新表已被删除
□ 7. 备份表已保留
□ 8. 日志文件已保存

如果以上检查都通过，回滚操作成功完成。
*/

-- ============================================================================
-- 紧急恢复命令（一键执行）
-- ============================================================================

-- 如果需要紧急回滚，可以使用以下存储过程
DELIMITER //

CREATE PROCEDURE EmergencyRollback()
BEGIN
    DECLARE backup_table_name VARCHAR(255);
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- 查找最新的备份表
    SELECT TABLE_NAME INTO backup_table_name
    FROM INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_SCHEMA = DATABASE() 
      AND TABLE_NAME LIKE 'wechat_articles_backup_%'
    ORDER BY CREATE_TIME DESC 
    LIMIT 1;
    
    IF backup_table_name IS NOT NULL THEN
        -- 删除新表
        SET FOREIGN_KEY_CHECKS = 0;
        
        DROP TABLE IF EXISTS `publish_tasks`;
        DROP TABLE IF EXISTS `articles`;
        DROP TABLE IF EXISTS `system_config`;
        DROP TABLE IF EXISTS `auth_credentials`;
        DROP TABLE IF EXISTS `operation_logs`;
        
        DROP VIEW IF EXISTS `v_article_status`;
        DROP VIEW IF EXISTS `v_publish_status`;
        DROP VIEW IF EXISTS `wechat_articles_view`;
        
        SET FOREIGN_KEY_CHECKS = 1;
        
        -- 恢复备份表
        SET @sql = CONCAT('RENAME TABLE `', backup_table_name, '` TO `wechat_articles`');
        PREPARE stmt FROM @sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
        
        SELECT CONCAT('回滚成功，已从 ', backup_table_name, ' 恢复数据') as result;
    ELSE
        SELECT '错误：未找到备份表' as result;
        ROLLBACK;
    END IF;
    
    COMMIT;
END //

DELIMITER ;

-- 使用方法：
-- CALL EmergencyRollback();

-- 清理存储过程（在确认不需要后执行）
-- DROP PROCEDURE IF EXISTS EmergencyRollback;
