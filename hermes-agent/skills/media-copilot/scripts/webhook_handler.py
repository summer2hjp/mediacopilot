# webhook_handler.py 示例
@app.post("/webhook/media-status")
async def media_webhook(payload: dict):
    """处理 Overseerr 状态回调"""
    if payload["event"] == "media_approved":
        title = payload["subject"]
        await hermes_channels.send(
            f"🎬 《{title}》请求已批准，开始搜索下载资源..."
        )
    elif payload["event"] == "media_available":
        title = payload["subject"]
        await hermes_channels.send(
            f"✅ 《{title}》下载完成，已整理到媒体库！"
        )
