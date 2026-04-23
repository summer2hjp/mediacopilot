# 🎬 Media Copilot - 完整环境变量配置
# 文件: ~/.hermes/.env
# 用途: Hermes-Agent + Docker 媒体自动化系统
# 安全: 此文件包含敏感信息，请勿提交到版本控制，权限设为 600

# -----------------------------------------------------------------------------
# 🔑 全局基础配置
# -----------------------------------------------------------------------------
# Hermes-Agent 基础
HERMES_AGENT_VERSION=latest
HERMES_CONFIG_DIR=~/.hermes
HERMES_SKILLS_DIR=~/.hermes/skills
HERMES_LOG_LEVEL=INFO
HERMES_API_PORT=8000
HERMES_API_HOST=0.0.0.0

# 系统路径（Mac mini 本地路径 → Docker 容器挂载映射）
MEDIA_ROOT=/Volumes/Media                    # Mac 本地媒体根目录
DOWNLOADS_ROOT=/Volumes/Downloads            # Mac 本地下载根目录
CONFIG_ROOT=~/.hermes/docker/config          # 配置文件存储路径

# Docker 网络配置
DOCKER_NETWORK_NAME=media-net
DOCKER_SUBNET=172.20.0.0/24
DOCKER_GATEWAY=172.20.0.1

# -----------------------------------------------------------------------------
# 🔐 安全与认证（⚠️ 请生成强密码/密钥）
# -----------------------------------------------------------------------------
# Webhook 签名密钥（用于验证回调请求）
WEBHOOK_SECRET=changeme_generate_32_bytes_hex_secret_here

# Hermes API 认证（如果启用）
HERMES_API_KEY=hermes_sk_live_xxxxxxxxxxxxxxxxxxxxxxxx

# 数据库密码（如果使用 PostgreSQL/MySQL 存储状态）
DB_PASSWORD=changeme_strong_db_password

# JWT 密钥（如果启用 API Token 认证）
JWT_SECRET=changeme_jwt_secret_min_32_chars

# -----------------------------------------------------------------------------
# 🎬 Overseerr 配置
# -----------------------------------------------------------------------------
OVERSEERR_ENABLED=true
OVERSEERR_CONTAINER_NAME=overseerr
OVERSEERR_IMAGE=lscr.io/linuxserver/overseerr:latest
OVERSEERR_PORT=5055
OVERSEERR_HOST=0.0.0.0
OVERSEERR_URL=http://overseerr:5055          # Docker 内部访问地址
OVERSEERR_EXTERNAL_URL=http://192.168.1.100:5055  # 浏览器访问地址
OVERSEERR_API_KEY=overseerr_api_key_xxxxxxxxxxxxxxxx

# Overseerr 通知设置
OVERSEERR_WEBHOOK_URL=http://media-webhook:8080/webhook/overseerr
OVERSEERR_WEBHOOK_EVENTS=media_requested,media_approved,media_available,media_failed
OVERSEERR_DEFAULT_USER_ID=1                    # 默认请求用户 ID
OVERSEERR_AUTO_APPROVE=false                   # 是否自动批准请求
OVERSEERR_AUTO_APPROVE_MOVIE=false
OVERSEERR_AUTO_APPROVE_SERIES=false

# -----------------------------------------------------------------------------
# 🎥 Radarr 配置（电影）
# -----------------------------------------------------------------------------
RADARR_ENABLED=true
RADARR_CONTAINER_NAME=radarr
RADARR_IMAGE=lscr.io/linuxserver/radarr:latest
RADARR_PORT=7878
RADARR_HOST=0.0.0.0
RADARR_URL=http://radarr:7878
RADARR_EXTERNAL_URL=http://192.168.1.100:7878
RADARR_API_KEY=radarr_api_key_xxxxxxxxxxxxxxxx

# Radarr 路径配置（容器内路径）
RADARR_CONFIG_DIR=/config
RADARR_MOVIES_ROOT=/movies
RADARR_DOWNLOADS_DIR=/downloads/completed/radarr
RADARR_UNPACKED_DIR=/downloads/unpacked/radarr

# Radarr 质量与配置
RADARR_DEFAULT_QUALITY_PROFILE=HD-1080p
RADARR_DEFAULT_4K_QUALITY_PROFILE=UHD-2160p
RADARR_DEFAULT_LANGUAGE_PROFILE=English
RADARR_DEFAULT_ROOT_FOLDER=/movies
RADARR_SEARCH_ON_ADD=true
RADARR_MONITOR_NEW_MOVIES=true

# Radarr Webhook
RADARR_WEBHOOK_URL=http://media-webhook:8080/webhook/radarr
RADARR_WEBHOOK_ON_GRAB=true
RADARR_WEBHOOK_ON_DOWNLOAD=true
RADARR_WEBHOOK_ON_IMPORT=true
RADARR_WEBHOOK_ON_FAILURE=true

# -----------------------------------------------------------------------------
# 📺 Sonarr 配置（电视剧）
# -----------------------------------------------------------------------------
SONARR_ENABLED=true
SONARR_CONTAINER_NAME=sonarr
SONARR_IMAGE=lscr.io/linuxserver/sonarr:latest
SONARR_PORT=8989
SONARR_HOST=0.0.0.0
SONARR_URL=http://sonarr:8989
SONARR_EXTERNAL_URL=http://192.168.1.100:8989
SONARR_API_KEY=sonarr_api_key_xxxxxxxxxxxxxxxx

# Sonarr 路径配置
SONARR_CONFIG_DIR=/config
SONARR_SERIES_ROOT=/tv
SONARR_DOWNLOADS_DIR=/downloads/completed/sonarr
SONARR_UNPACKED_DIR=/downloads/unpacked/sonarr

# Sonarr 质量与配置
SONARR_DEFAULT_QUALITY_PROFILE=HD-1080p
SONARR_DEFAULT_4K_QUALITY_PROFILE=UHD-2160p
SONARR_DEFAULT_LANGUAGE_PROFILE=English
SONARR_DEFAULT_ROOT_FOLDER=/tv
SONARR_SEARCH_ON_ADD=true
SONARR_MONITOR_NEW_SERIES=true
SONARR_SERIES_TYPE=standard  # standard, anime, daily

# Sonarr Webhook
SONARR_WEBHOOK_URL=http://media-webhook:8080/webhook/sonarr
SONARR_WEBHOOK_ON_GRAB=true
SONARR_WEBHOOK_ON_DOWNLOAD=true
SONARR_WEBHOOK_ON_IMPORT=true
SONARR_WEBHOOK_ON_FAILURE=true

# -----------------------------------------------------------------------------
# ⬇️ qBittorrent 配置
# -----------------------------------------------------------------------------
QBITTORRENT_ENABLED=true
QBITTORRENT_CONTAINER_NAME=qbittorrent
QBITTORRENT_IMAGE=lscr.io/linuxserver/qbittorrent:latest
QBITTORRENT_PORT=8080
QBITTORRENT_HOST=0.0.0.0
QBITTORRENT_URL=http://qbittorrent:8080
QBITTORRENT_EXTERNAL_URL=http://192.168.1.100:8080

# qBittorrent 认证
QBITTORRENT_USERNAME=admin
QBITTORRENT_PASSWORD=changeme_strong_qb_password

# qBittorrent 路径配置
QBITTORRENT_CONFIG_DIR=/config
QBITTORRENT_DOWNLOADS_DIR=/downloads
QBITTORRENT_INCOMPLETE_DIR=/downloads/incomplete
QBITTORRENT_WATCH_DIR=/downloads/watch

# qBittorrent 网络设置
QBITTORRENT_BT_PORT=6881
QBITTORRENT_BT_PORT_UDP=6881
QBITTORRENT_MAX_CONNECTIONS=500
QBITTORRENT_MAX_UPLOADS=20
QBITTORRENT_GLOBAL_UPLOAD_LIMIT=0      # 0 = 无限制 (KB/s)
QBITTORRENT_GLOBAL_DOWNLOAD_LIMIT=0

# qBittorrent 分类（用于 Radarr/Sonarr 自动导入）
QBITTORRENT_CATEGORY_MOVIES=movies
QBITTORRENT_CATEGORY_SERIES=tv
QBITTORRENT_CATEGORY_ANIME=anime

# qBittorrent 通知脚本（需挂载脚本文件）
QBITTORRENT_ON_COMPLETE_SCRIPT=/config/scripts/qb-notify.sh
QBITTORRENT_ON_COMPLETE_ENABLED=true

# -----------------------------------------------------------------------------
# 🔍 Prowlarr 配置（索引器管理）
# -----------------------------------------------------------------------------
PROWLARR_ENABLED=true
PROWLARR_CONTAINER_NAME=prowlarr
PROWLARR_IMAGE=lscr.io/linuxserver/prowlarr:latest
PROWLARR_PORT=9696
PROWLARR_HOST=0.0.0.0
PROWLARR_URL=http://prowlarr:9696
PROWLARR_EXTERNAL_URL=http://192.168.1.100:9696
PROWLARR_API_KEY=prowlarr_api_key_xxxxxxxxxxxxxxxx

# Prowlarr 同步设置
PROWLARR_SYNC_TO_RADARR=true
PROWLARR_SYNC_TO_SONARR=true
PROWLARR_SYNC_INTERVAL=6h

# Prowlarr 索引器（示例，实际通过 UI 配置）
# PROWLARR_INDEXERS=1337x,nyaa,torrentleech,privatetracker1

# -----------------------------------------------------------------------------
# 🎯 Hermes-Agent media-copilot Skill 配置
# -----------------------------------------------------------------------------
# Skill 启用
SKILL_MEDIA_COPILOT_ENABLED=true
SKILL_MEDIA_COPILOT_VERSION=1.0.0

# API 地址（Hermes-Agent 调用各服务时使用）
MEDIA_COPILOT_OVERSEERR_URL=${OVERSEERR_URL}
MEDIA_COPILOT_OVERSEERR_API_KEY=${OVERSEERR_API_KEY}
MEDIA_COPILOT_RADARR_URL=${RADARR_URL}
MEDIA_COPILOT_RADARR_API_KEY=${RADARR_API_KEY}
MEDIA_COPILOT_SONARR_URL=${SONARR_URL}
MEDIA_COPILOT_SONARR_API_KEY=${SONARR_API_KEY}
MEDIA_COPILOT_QBITTORRENT_URL=${QBITTORRENT_URL}
MEDIA_COPILOT_QBITTORRENT_USERNAME=${QBITTORRENT_USERNAME}
MEDIA_COPILOT_QBITTORRENT_PASSWORD=${QBITTORRENT_PASSWORD}
MEDIA_COPILOT_PROWLARR_URL=${PROWLARR_URL}
MEDIA_COPILOT_PROWLARR_API_KEY=${PROWLARR_API_KEY}

# 默认下载配置
MEDIA_COPILOT_DEFAULT_QUALITY_MOVIE=HD-1080p
MEDIA_COPILOT_DEFAULT_QUALITY_SERIES=HD-1080p
MEDIA_COPILOT_DEFAULT_QUALITY_4K_MOVIE=UHD-2160p
MEDIA_COPILOT_DEFAULT_QUALITY_4K_SERIES=UHD-2160p
MEDIA_COPILOT_DEFAULT_ROOT_MOVIE=/movies
MEDIA_COPILOT_DEFAULT_ROOT_SERIES=/tv
MEDIA_COPILOT_DEFAULT_LANGUAGE=en
MEDIA_COPILOT_SEARCH_ON_REQUEST=true

# 通知设置
MEDIA_COPILOT_NOTIFY_CHANNEL=telegram
MEDIA_COPILOT_NOTIFY_ON_REQUEST=true
MEDIA_COPILOT_NOTIFY_ON_GRAB=true
MEDIA_COPILOT_NOTIFY_ON_DOWNLOAD_START=true
MEDIA_COPILOT_NOTIFY_ON_DOWNLOAD_COMPLETE=true
MEDIA_COPILOT_NOTIFY_ON_IMPORT=true
MEDIA_COPILOT_NOTIFY_ON_FAILURE=true
MEDIA_COPILOT_NOTIFY_TEMPLATE=default  # 或 custom

# TMDB/TVDB API（用于媒体搜索）
TMDB_API_KEY=tmdb_api_key_xxxxxxxxxxxxxxxx
TVDB_API_KEY=tvdb_api_key_xxxxxxxxxxxxxxxx
TVDB_PIN=optional_tvdb_pin

# -----------------------------------------------------------------------------
# 📡 Hermes Channels 通知配置
# -----------------------------------------------------------------------------
# Telegram（推荐）
HERMES_CHANNEL_TELEGRAM_ENABLED=true
HERMES_CHANNEL_TELEGRAM_BOT_TOKEN=telegram_bot_token_xxxxxxxxxxxxxxxx
HERMES_CHANNEL_TELEGRAM_CHAT_ID=-1001234567890

# Discord
HERMES_CHANNEL_DISCORD_ENABLED=false
HERMES_CHANNEL_DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/xxx/xxx

# Email（备用）
HERMES_CHANNEL_EMAIL_ENABLED=false
HERMES_CHANNEL_EMAIL_SMTP_HOST=smtp.gmail.com
HERMES_CHANNEL_EMAIL_SMTP_PORT=587
HERMES_CHANNEL_EMAIL_SMTP_USER=your_email@gmail.com
HERMES_CHANNEL_EMAIL_SMTP_PASSWORD=your_app_password
HERMES_CHANNEL_EMAIL_FROM=your_email@gmail.com
HERMES_CHANNEL_EMAIL_TO=recipient@example.com

# 默认通知渠道
HERMES_DEFAULT_CHANNEL=telegram

# -----------------------------------------------------------------------------
# 🔄 Webhook Handler 配置
# -----------------------------------------------------------------------------
WEBHOOK_HANDLER_ENABLED=true
WEBHOOK_HANDLER_PORT=8080
WEBHOOK_HANDLER_HOST=0.0.0.0
WEBHOOK_HANDLER_URL=http://media-webhook:8080

# 签名验证
WEBHOOK_HANDLER_SECRET=${WEBHOOK_SECRET}
WEBHOOK_HANDLER_VERIFY_SIGNATURE=true

# 通知转发
WEBHOOK_HANDLER_HERMES_API_URL=http://hermes-agent:8000
WEBHOOK_HANDLER_HERMES_API_KEY=${HERMES_API_KEY}
WEBHOOK_HANDLER_DEFAULT_CHANNEL=${HERMES_DEFAULT_CHANNEL}

# 日志
WEBHOOK_HANDLER_LOG_LEVEL=INFO
WEBHOOK_HANDLER_LOG_FILE=/app/logs/webhook.log

# -----------------------------------------------------------------------------
# 🗄️ 可选：数据库配置（用于状态持久化）
# -----------------------------------------------------------------------------
# PostgreSQL（推荐）
DB_TYPE=postgresql
DB_HOST=postgres
DB_PORT=5432
DB_NAME=media_copilot
DB_USER=media_user
DB_PASSWORD=${DB_PASSWORD}
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# 或 SQLite（轻量级，开发用）
# DB_TYPE=sqlite
# DB_PATH=/app/data/media_copilot.db

# -----------------------------------------------------------------------------
# 🌐 反向代理配置（Nginx/Caddy）
# -----------------------------------------------------------------------------
# 如果使用 Nginx 反向代理暴露服务
NGINX_ENABLED=true
NGINX_PORT=443
NGINX_SSL_CERT_PATH=/etc/nginx/ssl/cert.pem
NGINX_SSL_KEY_PATH=/etc/nginx/ssl/key.pem
NGINX_DOMAIN=media.yourdomain.com

# Basic Auth（可选额外保护）
NGINX_BASIC_AUTH_ENABLED=false
NGINX_BASIC_AUTH_USER=admin
NGINX_BASIC_AUTH_PASSWORD=changeme_basic_auth_password

# -----------------------------------------------------------------------------
# 🧪 开发与调试配置
# -----------------------------------------------------------------------------
# 日志级别
LOG_LEVEL=INFO
LOG_FORMAT=json  # 或 text
LOG_FILE_ROTATION_DAYS=7

# 调试模式
DEBUG_MODE=false
HERMES_DEBUG_TOOLS_ENABLED=false

# 测试模式（不实际调用 API）
MEDIA_COPILOT_DRY_RUN=false
WEBHOOK_HANDLER_DRY_RUN=false

# -----------------------------------------------------------------------------
# 📦 Docker Compose 特定变量
# -----------------------------------------------------------------------------
# 用户/组权限（避免权限问题）
PUID=501          # Mac 用户的 UID (运行 `id -u` 查看)
PGID=20           # Mac 用户的 GID (运行 `id -g` 查看)
TZ=Asia/Shanghai  # 时区

# 资源限制（可选）
DOCKER_MEM_LIMIT=4g
DOCKER_CPU_LIMIT=2.0

# 卷挂载前缀（统一路径管理）
VOLUME_PREFIX=${CONFIG_ROOT}
