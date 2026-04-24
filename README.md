# 🎬 Media Copilot - 全自动媒体下载助手
通过 Hermes Channels 接收消息，自动调用 Overseerr/Radarr/Sonarr/qBittorrent/Prowlarr 实现电影电视剧的智能搜索与下载

<p align="center">
  <img src="assets/Media-Copilot-Architecture.png" alt="Media-Copilot-Architecture" width="100%">
</p>

## 📊 架构数据流
```
用户自然语言请求
        ↓
Hermes Agent (192.168.3.66)
        ↓ 加载 media-copilot skill (SKILL.md)
        ↓ 注入配置: config.yaml + .env
        ↓
┌─────────────────────────────────┐
│  🎬 Overseerr (统一请求入口)    │
│  http://192.168.3.66:5055       │
├─────────────────────────────────┤
│  ├─→ 搜索: TMDB/TVDB元数据      │
│  ├─→ 路由: 电影→Radarr, 剧集→Sonarr │
│  └─→ 回调: 状态更新→Hermes反馈  │
└────────┬────────┬──────────────┘
         │        │
         ▼        ▼
┌────────────┐ ┌────────────┐
│ 🔴 Radarr  │ │ 🔵 Sonarr  │
│ 192.168.3.222:7878 │ 192.168.3.222:8989 │
├────────────┤ ├────────────┤
│ • 质量配置  │ │ • 季数管理  │
│ • 路径映射  │ │ • 命名规则  │
│ • 自动搜索  │ │ • 自动搜索  │
└────┬───────┘ └────┬───────┘
     │             │
     ▼             ▼
┌─────────────────────┐
│ ⬇️ qBittorrent     │
│ 192.168.3.222:8080 │
├─────────────────────┤
│ • 种子下载          │
│ • 限速/调度         │
│ • 完成后通知Arr     │
└────────┬────────────┘
         │ 下载完成
         ▼
┌─────────────────────┐
│ 🎬 Radarr/Sonarr后处理 │
├─────────────────────┤
│ • 文件重命名        │
│ • 移动至最终路径    │
│ • 触发Jellyfin扫描  │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ 📺 Jellyfin入库    │
│ 192.168.3.88:8096  │
├─────────────────────┤
│ • 元数据抓取        │
│ • 海报/剧照下载     │
│ • 用户可播放 ✅     │
└────────┬────────────┘
         │
         ▼
[可选] webhook → Hermes → 用户通知
```

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

## 🔐 认证方式

所有 API 均使用 **Header 认证**：
```http
# Radarr/Sonarr/Prowlarr
X-Api-Key: YOUR_API_KEY

# Overseerr
X-Api-Key: YOUR_OVERSEERR_API_KEY

# qBittorrent (先登录获取 Cookie)
POST /api/v2/auth/login
Cookie: SID=xxx
```

## ✨ 项目亮点总结:

```
✅ 完全合规: 遵循Hermes Skill 2.0规范hermes-agent.nousresearch.com和mintlify.com, 支持config配置注入和required_environment_variables安全声明
✅ 架构适配: 支持分布式部署, 开箱即用, 减少配置步骤
✅ 统一入口: 优先通过Overseerr调度, 避免直接操作Arr导致的权限/配置冲突
✅ 模块化脚本: scripts/目录封装各服务操作, 便于维护和扩展(如未来添加Lidarr)
✅ 完整反馈: 内置进度轮询+入库验证+自然语言反馈, 提升用户体验
✅ 错误自愈: 常见陷阱检测+重试策略+用户引导, 降低使用门槛
```
