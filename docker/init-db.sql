-- 哪吒家庭 - 数据库初始化脚本
-- 用途：创建数据库扩展和初始配置

-- 启用 UUID 扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 启用 pgcrypto 扩展（用于密码哈希）
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 设置时区
SET timezone = 'Asia/Shanghai';

-- 创建更新时间戳函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 输出初始化信息
DO $$
BEGIN
    RAISE NOTICE '数据库初始化完成';
    RAISE NOTICE '已启用扩展: uuid-ossp, pgcrypto';
    RAISE NOTICE '已创建函数: update_updated_at_column()';
END $$;
