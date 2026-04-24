---
name: media-copilot
description: 全自动媒体下载助手 - 通过 Overseerr 调度 Radarr/Sonarr/qBittorrent/Prowlarr 实现电影电视剧的智能搜索与下载
version: 1.0.0
author: Summer520
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [Media, Automation, Docker, Radarr, Sonarr, Overseerr, qBittorrent, Prowlarr]
    related_skills: [web-extract, terminal]
    requires_toolsets: [web, terminal]
    requires_tools: [web_request, execute_code]
    config:
      - key: media_copilot.overseerr_url
        description: Overseerr 服务地址（含端口）
        default: "http://192.168.3.66:5055"
        prompt: "请输入 Overseerr 地址"
      - key: media_copilot.overseerr_api_key
        description: Overseerr API Key
        default: ""
        prompt: "请输入 Overseerr API Key（设置→服务→API 密钥）"
      - key: media_copilot.radarr_url
        description: Radarr 服务地址
        default: "http://192.168.3.222:7878"
        prompt: "请输入 Radarr 地址"
      - key: media_copilot.radarr_api_key
        description: Radarr API Key
        default: ""
        prompt: "请输入 Radarr API Key"
      - key: media_copilot.radarr-4k_url
        description: Radarr-4K 服务地址
        default: "http://192.168.3.66:7878"
        prompt: "请输入 Radarr-4K 地址"
      - key: media_copilot.radarr-4k_api_key
        description: Radarr-4K API Key
        default: ""
        prompt: "请输入 Radarr-4K API Key"
      - key: media_copilot.sonarr_url
        description: Sonarr 服务地址
        default: "http://192.168.3.222:8989"
        prompt: "请输入 Sonarr 地址"
      - key: media_copilot.sonarr_api_key
        description: Sonarr API Key
        default: ""
        prompt: "请输入 Sonarr API Key"
      - key: media_copilot.sonarr-4k_url
        description: Sonarr-4K 服务地址
        default: "http://192.168.3.66:8989"
        prompt: "请输入 Sonarr-4K 地址"
      - key: media_copilot.sonarr-4k_api_key
        description: Sonarr-4K API Key
        default: ""
        prompt: "请输入 Sonarr-4K API Key"
      - key: media_copilot.qbittorrent_url
        description: qBittorrent WebUI 地址
        default: "http://192.168.3.222:8080"
        prompt: "请输入 qBittorrent WebUI 地址"
      - key: media_copilot.qbittorrent_username
        description: qBittorrent 用户名
        default: "admin"
        prompt: "请输入 qBittorrent 用户名"
      - key: media_copilot.qbittorrent_password
        description: qBittorrent 密码
        default: ""
        prompt: "请输入 qBittorrent 密码"
      - key: media_copilot.prowlarr_url
        description: Prowlarr 服务地址
        default: "http://192.168.3.222:9696"
        prompt: "请输入 Prowlarr 地址"
      - key: media_copilot.prowlarr_api_key
        description: Prowlarr API Key
        default: ""
        prompt: "请输入 Prowlarr API Key"
      - key: media_copilot.default_quality_profile_movie
        description: Radarr 默认质量配置文件
        default: "HD-1080p"
        prompt: "请输入 Radarr 默认电影质量配置名"
      - key: media_copilot.default_quality_profile_movie-4k
        description: Radarr-4K 默认质量配置文件
        default: "Ultra-HD"
        prompt: "请输入 Radarr默认电影质量配置名(如: 4K-2160p)"
      - key: media_copilot.default_quality_profile_series
        description: Sonarr 默认质量配置文件
        default: "HD-1080p"
        prompt: "请输入 Sonarr 默认剧集质量配置名"
      - key: media_copilot.default_quality_profile_series-4k
        description: Sonarr-4K 默认质量配置文件
        default: "Ultra-HD"
        prompt: "请输入 Sonarr默认剧集质量配置名(如: 4K-2160p)"
      - key: media_copilot.default_root_folder_movie
        description: Radarr 默认存储路径
        default: "/movies"
        prompt: "请输入 Radarr 电影默认存储路径"
      - key: media_copilot.default_root_folder_movie_4k
        description: Radarr-4k 默认存储路径
        default: "/movies-4k"
        prompt: "请输入 Radarr-4k 电影默认存储路径"
      - key: media_copilot.default_root_folder_series
        description: Sonarr 默认存储路径
        default: "/tvshows"
        prompt: "请输入 Sonarr 剧集默认存储路径"
      - key: media_copilot.default_root_folder_series_4k
        description: Sonarr-4k 默认存储路径
        default: "/tvshows-4k"
        prompt: "请输入 Sonarr-4k 剧集默认存储路径"
required_environment_variables:
  - name: MEDIA_COPILOT_OVERSEERR_API_KEY
    prompt: "Overseerr API Key"
    help: "在 Overseerr 设置→服务→API 密钥中生成"
    required_for: "Overseerr API 调用"
  - name: MEDIA_COPILOT_RADARR_API_KEY
    prompt: "Radarr API Key"
    help: "在 Radarr 设置→常规→API 密钥中查看"
    required_for: "Radarr API 调用"
  - name: MEDIA_COPILOT_RADARR_4K_API_KEY
    prompt: "Radarr-4K API Key"
    help: "在 Radarr-4K 设置→常规→API 密钥中查看"
    required_for: "Radarr-4K API 调用"
  - name: MEDIA_COPILOT_SONARR_API_KEY
    prompt: "Sonarr API Key"
    help: "在 Sonarr 设置→常规→API 密钥中查看"
    required_for: "Sonarr API 调用"
  - name: MEDIA_COPILOT_SONARR_4K_API_KEY
    prompt: "Sonarr-4K API Key"
    help: "在 Sonarr 设置→常规→API 密钥中查看"
    required_for: "Sonarr-4K API 调用"
  - name: MEDIA_COPILOT_PROWLARR_API_KEY
    prompt: "Prowlarr API Key"
    help: "在 Prowlarr 设置→常规→API 密钥中查看"
    required_for: "Prowlarr API 调用"
---

# 🎬 Media Copilot - 全自动媒体下载助手

> 通过 Hermes Channels 接收消息，自动调用 Overseerr/Radarr/Sonarr/qBittorrent/Prowlarr 实现电影电视剧的智能搜索与下载

## 🎯 何时使用此技能

- 当用户通过 Hermes Channels 发送以下类型的消息包含以下意图时**自动激活**：

| 用户意图 | 示例消息 |
|---------|---------|
| 🔍 搜索媒体 | "搜索《奥本海默》4K版本" / "find Dune Part Two 4k" |
| ➕ 请求下载 | "下载电影《沙丘2》" / "add movie Dune: Part Two" |
| 📺 追剧订阅 | "追《龙之家族》第二季" / "subscribe to House of the Dragon S2" |
| 📋 查看队列 | "查看下载进度" / "check download queue" |
| ⏸️ 下载控制 | "暂停所有下载" / "pause all downloads" |
| ✅ 入库检查 | "《星际穿越》入库了吗？" / "is Interstellar available in Jellyfin?" |

## ⚡ 快速参考
| 操作 | 服务 | 端点 | 认证方式 |
|-----|------|-------|---------|
| 🔍 搜索电影 | Overseerr | `GET /api/v1/search?query={q}&type=movie` | `X-Api-Key: $OVERSEERR_KEY` |
| 🔍 搜索剧集 | Overseerr | `GET /api/v1/search?query={q}&type=tv` | `X-Api-Key: $OVERSEERR_KEY` |
| ➕ 提交请求 | Overseerr | `POST /api/v1/request` | `X-Api-Key: $OVERSEERR_KEY` |
| 🎬 添加电影(直连) | Radarr | `POST /api/v3/movie` | `X-Api-Key: $RADARR_KEY` |
| 📺 添加剧集(直连) | Sonarr | `POST /api/v3/series` | `X-Api-Key: $SONARR_KEY` |
| 🎬 添加4K电影(直连) | Radarr-4k | `POST /api/v3/movie` | `X-Api-Key: $RADARR_4K_KEY` |
| 📺 添加4K剧集(直连) | Sonarr-4k | `POST /api/v3/series` | `X-Api-Key: $SONARR_4K_KEY` |
| 📋 查看队列 | Radarr/Sonarr | `GET /api/v3/queue` | `X-Api-Key: $KEY` |
| ⬇️ 获取种子列表 | qBittorrent | `GET /api/v2/torrents/info` | `Cookie: SID=$SESSION` |
| ⏸️ 暂停下载 | qBittorrent | `POST /api/v2/torrents/pause` | `Cookie: SID=$SESSION` |
| ✅ 验证入库 | Jellyfin | `GET /Items?SearchTerm={title}` | `X-Emby-Token: $JELLYFIN_KEY` |

### 🔐 认证方式

```bash
# 🎬 Overseerr / Radarr / Sonarr / Prowlarr: Header认证
curl -H "X-Api-Key: ${API_KEY}" "http://192.168.3.66:5055/api/v1/..."

# ⬇️ qBittorrent: Cookie认证(需先登录)
# 1. 登录获取Session
curl -X POST "http://192.168.3.222:8080/api/v2/auth/login" \
  -d "username=${USER}&password=${PASS}" -c cookies.txt

# 2. 使用Cookie调用其他接口
curl -b cookies.txt "http://192.168.3.222:8080/api/v2/torrents/info"

# 📺 Jellyfin: Token认证
curl -H "X-Emby-Token: ${JELLYFIN_KEY}" "http://192.168.3.88:8096/..."
