#!/bin/bash
# 哪吒家庭 - Docker 部署脚本
# 用途：快速检查环境并启动服务

set -e

echo "======================================"
echo "  哪吒家庭 - Docker 部署脚本"
echo "======================================"
echo ""

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ 错误：未检测到 Docker，请先安装 Docker"
    echo "安装指南：https://docs.docker.com/engine/install/"
    exit 1
fi

# 检查 Docker Compose 是否安装
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    echo "❌ 错误：未检测到 Docker Compose，请先安装"
    exit 1
fi

echo "✅ Docker 环境检查通过"
echo ""

fail() {
    echo "❌ 错误：$1"
    exit 1
}

is_placeholder_value() {
    local value="$1"

    case "$value" in
        ""|请修改*|your-*|*"your-domain.com"*|*"your-email@example.com"*|*"example.com"*|changeme|change_me|CHANGE_ME|password|dev_secret_key_change_in_production|nezha_dev_password)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

require_production_env() {
    if [ ! -f .env ]; then
        fail "未找到 .env 文件，请先复制 .env.example 并填写生产配置"
    fi

    if [ -f .env.example ] && cmp -s .env .env.example; then
        fail ".env 仍与 .env.example 完全相同，不能直接用于生产部署"
    fi

    set -a
    # shellcheck disable=SC1091
    source .env
    set +a

    local required_vars=(
        POSTGRES_PASSWORD
        REDIS_PASSWORD
        SECRET_KEY
        DOMAIN
        ADMIN_EMAIL
        ALLOWED_ORIGINS
    )

    local var_name
    local value
    for var_name in "${required_vars[@]}"; do
        value="${!var_name}"
        if is_placeholder_value "$value"; then
            fail "请在 .env 文件中设置有效的 ${var_name}，不要使用模板占位值"
        fi
    done

    if [ ${#POSTGRES_PASSWORD} -lt 16 ]; then
        fail "POSTGRES_PASSWORD 至少需要 16 个字符"
    fi

    if [ ${#REDIS_PASSWORD} -lt 16 ]; then
        fail "REDIS_PASSWORD 至少需要 16 个字符"
    fi

    if [ ${#SECRET_KEY} -lt 32 ]; then
        fail "SECRET_KEY 至少需要 32 个字符，可运行：openssl rand -hex 32"
    fi

    if [[ "$DOMAIN" == http://* ]] || [[ "$DOMAIN" == https://* ]] || [[ "$DOMAIN" == */* ]]; then
        fail "DOMAIN 只填写域名本身，不要包含 http/https 前缀或路径"
    fi

    if [[ ! "$ADMIN_EMAIL" =~ ^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$ ]]; then
        fail "ADMIN_EMAIL 需要是有效邮箱地址"
    fi

    if [[ "$ALLOWED_ORIGINS" != http://* ]] && [[ "$ALLOWED_ORIGINS" != https://* ]]; then
        fail "ALLOWED_ORIGINS 需要填写完整来源，例如：https://family.example.net"
    fi
}

# 检查 .env 文件
if [ ! -f .env ]; then
    echo "⚠️  未找到 .env 文件，正在从模板创建..."
    cp .env.example .env
    echo "✅ 已创建 .env 文件"
    echo ""
    echo "⚠️  重要：请编辑 .env 文件，修改以下配置："
    echo "   - POSTGRES_PASSWORD（数据库密码）"
    echo "   - REDIS_PASSWORD（Redis 密码）"
    echo "   - SECRET_KEY（JWT 密钥，运行：openssl rand -hex 32）"
    echo "   - DOMAIN（生产环境域名）"
    echo "   - ADMIN_EMAIL（管理员邮箱）"
    echo ""
    read -p "按回车键继续（确认已修改 .env 文件）..."
fi

# 选择环境
echo "请选择部署环境："
echo "1) 开发环境（development）"
echo "2) 生产环境（production）"
read -p "请输入选项 [1-2]: " env_choice

case $env_choice in
    1)
        echo ""
        echo "📦 启动开发环境..."
        $COMPOSE_CMD up -d
        echo ""
        echo "✅ 开发环境启动成功！"
        echo ""
        echo "访问地址："
        echo "  - 前端：http://localhost:8080"
        echo "  - 后端 API：http://localhost:8080/api/v1"
        echo "  - API 文档：http://localhost:8000/api/docs"
        echo ""
        echo "查看日志：$COMPOSE_CMD logs -f"
        ;;
    2)
        echo ""
        echo "📦 启动生产环境..."

        require_production_env

        $COMPOSE_CMD -f docker-compose.prod.yml up -d
        echo ""
        echo "✅ 生产环境启动成功！"
        echo ""
        echo "访问地址："
        echo "  - https://$DOMAIN"
        echo ""
        echo "初始化管理员：$COMPOSE_CMD -f docker-compose.prod.yml exec backend python init_admin.py"
        echo "查看日志：$COMPOSE_CMD -f docker-compose.prod.yml logs -f"
        ;;
    *)
        echo "❌ 无效选项"
        exit 1
        ;;
esac

echo ""
echo "其他命令："
echo "  - 停止服务：$COMPOSE_CMD down"
echo "  - 查看状态：$COMPOSE_CMD ps"
echo "  - 重启服务：$COMPOSE_CMD restart"
echo ""
