---
name: media-copilot
description: 全自动媒体下载助手 - 通过 Overseerr 调度 Radarr/Sonarr/qBittorrent/Prowlarr 实现电影电视剧的智能搜索与下载
version: 1.0.0
author: Your Name
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
        default: "http://localhost:5055"
        prompt: "请输入 Overseerr 地址（如：http://192.168.1.100:5055）"
      - key: media_copilot.overseerr_api_key
        description: Overseerr API Key
        default: ""
        prompt: "请输入 Overseerr API Key（设置→服务→API 密钥）"
      - key: media_copilot.radarr_url
        description: Radarr 服务地址
        default: "http://localhost:7878"
        prompt: "请输入 Radarr 地址"
      - key: media_copilot.radarr_api_key
        description: Radarr API Key
        default: ""
        prompt: "请输入 Radarr API Key"
      - key: media_copilot.sonarr_url
        description: Sonarr 服务地址
        default: "http://localhost:8989"
        prompt: "请输入 Sonarr 地址"
      - key: media_copilot.sonarr_api_key
        description: Sonarr API Key
        default: ""
        prompt: "请输入 Sonarr API Key"
      - key: media_copilot.qbittorrent_url
        description: qBittorrent WebUI 地址
        default: "http://localhost:8080"
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
        default: "http://localhost:9696"
        prompt: "请输入 Prowlarr 地址"
      - key: media_copilot.prowlarr_api_key
        description: Prowlarr API Key
        default: ""
        prompt: "请输入 Prowlarr API Key"
      - key: media_copilot.default_quality_profile_movie
        description: Radarr 默认质量配置文件
        default: "HD-1080p"
        prompt: "请输入 Radarr 默认电影质量配置名"
      - key: media_copilot.default_quality_profile_series
        description: Sonarr 默认质量配置文件
        default: "HD-1080p"
        prompt: "请输入 Sonarr 默认剧集质量配置名"
      - key: media_copilot.default_root_folder_movie
        description: Radarr 默认存储路径
        default: "/media/movies"
        prompt: "请输入 Radarr 电影默认存储路径"
      - key: media_copilot.default_root_folder_series
        description: Sonarr 默认存储路径
        default: "/media/tv"
        prompt: "请输入 Sonarr 剧集默认存储路径"
required_environment_variables:
  - name: MEDIA_COPILOT_OVERSEERR_API_KEY
    prompt: "Overseerr API Key"
    help: "在 Overseerr 设置→服务→API 密钥中生成"
    required_for: "Overseerr API 调用"
  - name: MEDIA_COPILOT_RADARR_API_KEY
    prompt: "Radarr API Key"
    help: "在 Radarr 设置→常规→API 密钥中查看"
    required_for: "Radarr API 调用"
  - name: MEDIA_COPILOT_SONARR_API_KEY
    prompt: "Sonarr API Key"
    help: "在 Sonarr 设置→常规→API 密钥中查看"
    required_for: "Sonarr API 调用"
  - name: MEDIA_COPILOT_PROWLARR_API_KEY
    prompt: "Prowlarr API Key"
    help: "在 Prowlarr 设置→常规→API 密钥中查看"
    required_for: "Prowlarr API 调用"
---

# 🎬 Media Copilot - 全自动媒体下载助手

> 通过 Hermes Channels 接收消息，自动调用 Overseerr/Radarr/Sonarr/qBittorrent/Prowlarr 实现电影电视剧的智能搜索与下载

## 🎯 何时使用此技能

当用户通过 Hermes Channels 发送以下类型的消息时，自动加载本技能：
- "下载电影《奥本海默》" / "add movie Oppenheimer"
- "追剧《权力的游戏》" / "subscribe to Game of Thrones"
- "搜索 4K 版本的《沙丘2》" / "search Dune Part Two 4K"
- "查看下载队列" / "check download queue"
- "暂停所有下载" / "pause all downloads"

## ⚡ 快速参考

| 操作 | Overseerr API | Radarr API [[29]] | Sonarr API | qBittorrent API [[52]] |
|------|--------------|-------------------|------------|------------------------|
| 搜索电影 | `GET /api/v1/search` | `GET /api/v3/movie/lookup` | - | - |
| 添加电影 | `POST /api/v1/request` | `POST /api/v3/movie` | - | - |
| 搜索剧集 | `GET /api/v1/search` | - | `GET /api/v3/series/lookup` | - |
| 添加剧集 | `POST /api/v1/request` | - | `POST /api/v3/series` | - |
| 查看队列 | - | `GET /api/v3/queue` | `GET /api/v3/queue` | `GET /api/v2/torrents/info` |
| 暂停下载 | - | - | - | `POST /api/v2/torrents/pause` |
| 手动搜索 | - | `POST /api/v3/command` (name: `MoviesSearch`) | `POST /api/v3/command` (name: `SeriesSearch`) | `POST /api/v2/torrents/reannounce` |

### 🔐 认证方式

所有 API 均使用 **Header 认证**：
```http
# Radarr/Sonarr/Prowlarr
X-Api-Key: YOUR_API_KEY

# Overseerr
X-Api-Key: YOUR_OVERSEERR_API_KEY

# qBittorrent (先登录获取 Cookie)
POST /api/v2/auth/login
Cookie: SID=xxx
