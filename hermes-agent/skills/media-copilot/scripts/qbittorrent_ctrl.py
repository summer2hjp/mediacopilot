#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Media Copilot - qBittorrent Controller: 下载任务管理
"""

__version__ = "1.0.0"

import os
import logging
from typing import Optional, Dict, List, Any, Union
from dataclasses import dataclass
from datetime import datetime

from .api_client import QbittorrentClient, APIResponse, ServiceType, create_client, load_env_config

logger = logging.getLogger("media-copilot.qbittorrent")

@dataclass
class TorrentInfo:
    hash: str
    name: str
    progress: float  # 0.0 - 1.0
    state: str       # downloading, stalled, uploading, paused, etc.
    size: int
    downloaded: int
    uploaded: int
    download_speed: int
    upload_speed: int
    eta: int         # seconds
    category: Optional[str] = None
    tags: Optional[str] = None
    added_on: Optional[int] = None
    
    @property
    def progress_percent(self) -> str:
        return f"{self.progress * 100:.1f}%"
    
    @property
    def eta_formatted(self) -> str:
        if self.eta <= 0: return "∞"
        if self.eta < 60: return f"{self.eta}s"
        if self.eta < 3600: return f"{self.eta//60}m"
        return f"{self.eta//3600}h{(self.eta%3600)//60}m"
    
    @property
    def download_speed_formatted(self) -> str:
        return self._format_speed(self.download_speed)
    
    @property
    def size_formatted(self) -> str:
        return self._format_size(self.size)
    
    @staticmethod
    def _format_size(bytes_: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_ < 1024:
                return f"{bytes_:.1f}{unit}"
            bytes_ /= 1024
        return f"{bytes_:.1f}PB"
    
    @staticmethod
    def _format_speed(bytes_per_sec: int) -> str:
        if bytes_per_sec == 0: return "0 B/s"
        for unit in ['B/s', 'KB/s', 'MB/s', 'GB/s']:
            if bytes_per_sec < 1024:
                return f"{bytes_per_sec:.1f}{unit}"
            bytes_per_sec /= 1024
        return f"{bytes_per_sec:.1f}GB/s"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "hash": self.hash, "name": self.name, "progress": self.progress_percent,
            "state": self.state, "size": self.size_formatted, "downloaded": self._format_size(self.downloaded),
            "speed": self.download_speed_formatted, "eta": self.eta_formatted,
            "category": self.category, "tags": self.tags
        }

class QbittorrentCtrl:
    def __init__(self, base_url: str, username: str, password: str, 
                 timeout: int = 30, verify_ssl: bool = True):
        self.client = QbittorrentClient(base_url, username, password, timeout=timeout, verify_ssl=verify_ssl)
        logger.info(f"✅ QbittorrentCtrl: {base_url}")
    
    @classmethod
    def from_env(cls, prefix: str = "MEDIA_COPILOT") -> Optional["QbittorrentCtrl"]:
        url = os.getenv(f"{prefix}_QBITTORRENT_URL")
        user = os.getenv(f"{prefix}_QBITTORRENT_USERNAME", "admin")
        pwd = os.getenv(f"{prefix}_QBITTORRENT_PASSWORD")
        if not url or not pwd:
            logger.error("❌ qBittorrent config missing")
            return None
        return cls(url, user, pwd)
    
    def get_torrents(self, hashes: Optional[Union[str, List[str]]] = None,
                     category: Optional[str] = None, state: Optional[str] = None) -> List[TorrentInfo]:
        """获取种子列表"""
        resp = self.client.get_torrents(hashes=hashes, category=category, state=state)
        if not resp.success or not resp.data:
            return []
        items = resp.data if isinstance(resp.data, list) else resp.data.get("torrents", [])
        return [self._parse_torrent(t) for t in items if isinstance(t, dict)]
    
    def _parse_torrent(self, data: Dict) -> TorrentInfo:
        return TorrentInfo(
            hash=data.get("hash", ""),
            name=data.get("name", "Unknown"),
            progress=data.get("progress", 0),
            state=data.get("state", "unknown"),
            size=data.get("size", 0),
            downloaded=data.get("downloaded", 0),
            uploaded=data.get("uploaded", 0),
            download_speed=data.get("dlspeed", 0),
            upload_speed=data.get("upspeed", 0),
            eta=data.get("eta", -1),
            category=data.get("category"),
            tags=data.get("tags"),
            added_on=data.get("added_on")
        )
    
    def pause(self, hashes: Union[str, List[str]]) -> APIResponse:
        """暂停下载"""
        return self.client.pause_torrents(hashes)
    
    def resume(self, hashes: Union[str, List[str]]) -> APIResponse:
        """恢复下载"""
        return self.client.resume_torrents(hashes)
    
    def delete(self, hashes: Union[str, List[str]], delete_files: bool = False) -> APIResponse:
        """删除种子"""
        return self.client.delete_torrents(hashes, delete_files=delete_files)
    
    def pause_all(self) -> APIResponse:
        """暂停所有下载"""
        torrents = self.get_torrents(state="downloading")
        if not torrents:
            return APIResponse(success=True, data={"message": "No active downloads"})
        hashes = [t.hash for t in torrents]
        return self.pause(hashes)
    
    def resume_all(self) -> APIResponse:
        """恢复所有暂停"""
        torrents = self.get_torrents(state="pausedDL")
        if not torrents:
            return APIResponse(success=True, data={"message": "No paused downloads"})
        hashes = [t.hash for t in torrents]
        return self.resume(hashes)
    
    def get_transfer_info(self) -> Dict[str, Any]:
        """获取全局传输统计"""
        resp = self.client.get_transfer_info()
        if resp.success and isinstance(resp.data, dict):
            return {
                "download_speed": self._format_speed(resp.data.get("dl_info_speed", 0)),
                "upload_speed": self._format_speed(resp.data.get("up_info_speed", 0)),
                "downloaded_today": self._format_size(resp.data.get("dl_info_data", 0)),
                "uploaded_today": self._format_size(resp.data.get("up_info_data", 0)),
                "free_space": self._format_size(resp.data.get("free_space_on_disk", 0)) if "free_space_on_disk" in resp.data else "N/A"
            }
        return {}
    
    def find_by_media(self, title: str, category: Optional[str] = None) -> Optional[TorrentInfo]:
        """根据媒体标题查找相关种子"""
        torrents = self.get_torrents(category=category)
        title_lower = title.lower()
        for t in torrents:
            if title_lower in t.name.lower():
                return t
        return None
    
    def wait_for_completion(self, torrent_hash: str, timeout_minutes: int = 120, 
                           poll_interval: int = 30) -> Dict[str, Any]:
        """
        轮询等待种子下载完成
        返回: {"completed": bool, "torrent": TorrentInfo|None, "elapsed_seconds": int}
        """
        import time
        start = time.time()
        max_wait = timeout_minutes * 60
        
        while time.time() - start < max_wait:
            torrents = self.get_torrents(hashes=torrent_hash)
            if not torrents:
                return {"completed": False, "torrent": None, "elapsed_seconds": int(time.time()-start), "error": "Torrent not found"}
            
            t = torrents[0]
            if t.progress >= 1.0 and t.state in ["uploading", "pausedUP", "stoppedUP"]:
                elapsed = int(time.time() - start)
                logger.info(f"✅ {t.name} completed after {elapsed}s")
                return {"completed": True, "torrent": t, "elapsed_seconds": elapsed}
            
            logger.debug(f"⏳ {t.name}: {t.progress_percent} ({t.state})")
            time.sleep(poll_interval)
        
        return {"completed": False, "torrent": self.get_torrents(hashes=torrent_hash)[0] if self.get_torrents(hashes=torrent_hash) else None, 
                "elapsed_seconds": int(time.time()-start), "timeout": True}
    
    def health_check(self) -> bool:
        """检查 qBittorrent 服务状态"""
        return self.client.health_check("/api/v2/app/version")
    
    @staticmethod
    def _format_size(bytes_: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_ < 1024:
                return f"{bytes_:.1f}{unit}"
            bytes_ /= 1024
        return f"{bytes_:.1f}PB"
    
    @staticmethod
    def _format_speed(bps: int) -> str:
        if bps == 0: return "0 B/s"
        for unit in ['B/s', 'KB/s', 'MB/s', 'GB/s']:
            if bps < 1024:
                return f"{bps:.1f}{unit}"
            bps /= 1024
        return f"{bps:.1f}GB/s"
    
    def close(self):
        self.client.close()
    
    def __enter__(self): return self
    def __exit__(self, *args): self.close(); return False

def create_qbittorrent_ctrl(prefix: str = "MEDIA_COPILOT") -> Optional[QbittorrentCtrl]:
    return QbittorrentCtrl.from_env(prefix)
