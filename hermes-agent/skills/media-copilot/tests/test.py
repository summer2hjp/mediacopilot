# 在 Hermes skill 中调用
from scripts import overseerr_ops, arr_manager, qbittorrent_ctrl, jellyfin_checker

# 1. 搜索并请求 4K 电影
with overseerr_ops.create_overseerr_ops() as ops:
    result = ops.auto_request("Dune Part Two", is4k=True)
    if result.success:
        print(f"✅ Request submitted: ID #{result.request_id}")

# 2. 查看下载队列
with qbittorrent_ctrl.create_qbittorrent_ctrl() as qb:
    torrents = qb.get_torrents(state="downloading")
    for t in torrents:
        print(f"📥 {t.name}: {t.progress_percent} @ {t.download_speed_formatted}")

# 3. 检查入库状态
with jellyfin_checker.create_jellyfin_checker() as jf:
    if jf and jf.is_available("Dune: Part Two", year=2024, item_type="Movie"):
        print("🎬 Already in Jellyfin library!")

# 4. 多实例添加 (通过 arr_manager)
with arr_manager.create_arr_manager() as am:
    req = arr_manager.MediaRequest(
        media_type=arr_manager.MediaType.MOVIE,
        title="Oppenheimer",
        tmdb_id=872585,
        quality_hint="1080p"  # 自动路由到 radarr_1080p
    )
    success, data, error = am.add_media(req)
    print(f"{'✅' if success else '❌'} {error or data}")
