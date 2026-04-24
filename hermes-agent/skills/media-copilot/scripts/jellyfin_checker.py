#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Media Copilot - Jellyfin Checker: 媒体入库状态验证
"""

__version__ = "1.0.0"

import os
import logging
from typing import Optional, Dict, List, Any
from dataclasses import dataclass

from .api_client import JellyfinClient, APIResponse, ServiceType, create_client, load_env_config

logger = logging.getLogger("media-copilot.jellyfin")

@dataclass
class MediaItem:
    title: str
    item_id: str
    item_type: str
    year: Optional[int] = None
    path: Optional[str] = None
    date_added: Optional[str] = None
    resolution: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}

class JellyfinChecker:
    def __init__(self, base_url: str, api_key: str, timeout: int = 30, verify_ssl: bool = True):
        self.client = JellyfinClient(base_url, api_key, timeout=timeout, verify_ssl=verify_ssl)
        logger.info(f"✅ JellyfinChecker: {base_url}")
    
    @classmethod
    def from_env(cls, prefix: str = "MEDIA_COPILOT") -> Optional["JellyfinChecker"]:
        url = os.getenv(f"{prefix}_JELLYFIN_URL")
        key = os.getenv(f"{prefix}_JELLYFIN_API_KEY") or os.getenv("MEDIA_COPILOT_JELLYFIN_API_KEY")
        if not url or not key:
            logger.warning("⚠️ Jellyfin config not found, checker disabled")
            return None
        return cls(url, key)
    
    def search(self, query: str, item_type: Optional[str] = None, limit: int = 20) -> List[MediaItem]:
        resp = self.client.search_items(query, item_type=item_type, limit=limit)
        if not resp.success or not resp.data:
            return []
        items = resp.data.get("Items", []) if isinstance(resp.data, dict) else resp.data
        results = []
        for item in items:
            if not isinstance(item, dict):
                continue
            results.append(MediaItem(
                title=item.get("Name") or item.get("title", "Unknown"),
                item_id=item.get("Id", ""),
                item_type=item.get("Type", "Unknown"),
                year=item.get("ProductionYear") or item.get("year"),
                path=item.get("Path"),
                date_added=item.get("DateCreated"),
                resolution=self._extract_resolution(item.get("MediaSources", [{}])[0] if item.get("MediaSources") else {})
            ))
        return results
    
    def _extract_resolution(self, media_source: Dict) -> Optional[str]:
        if not media_source:
            return None
        width = media_source.get("Width")
        if width:
            if width >= 3840: return "4K"
            if width >= 1920: return "1080p"
            if width >= 1280: return "720p"
        return None
    
    def find_by_title(self, title: str, year: Optional[int] = None, item_type: Optional[str] = None) -> Optional[MediaItem]:
        """精确查找: 标题 + 年份匹配"""
        items = self.search(title, item_type=item_type, limit=50)
        for item in items:
            if item.year == year or (year is None and item.title.lower() == title.lower()):
                return item
        return None
    
    def is_available(self, title: str, year: Optional[int] = None, item_type: Optional[str] = None) -> bool:
        """检查媒体是否已入库"""
        return self.find_by_title(title, year, item_type) is not None
    
    def get_item_details(self, item_id: str) -> Optional[Dict[str, Any]]:
        """获取项目详细信息"""
        resp = self.client.get_item(item_id)
        if resp.success and isinstance(resp.data, dict):
            return resp.data
        return None
    
    def refresh_library(self, item_id: Optional[str] = None) -> bool:
        """触发媒体库刷新"""
        resp = self.client.refresh_library(item_id)
        return resp.success
    
    def check_download_completion(self, title: str, expected_type: str = "Movie", 
                                timeout_minutes: int = 60, poll_interval: int = 30) -> Dict[str, Any]:
        """
        轮询检查下载完成并入库
        返回: {"available": bool, "item": MediaItem|None, "elapsed_seconds": int}
        """
        import time
        start = time.time()
        max_wait = timeout_minutes * 60
        
        while time.time() - start < max_wait:
            item = self.find_by_title(title, item_type=expected_type)
            if item:
                elapsed = int(time.time() - start)
                logger.info(f"✅ {title} available after {elapsed}s")
                return {"available": True, "item": item, "elapsed_seconds": elapsed}
            logger.debug(f"⏳ Waiting for {title}... ({int(time.time()-start)}s)")
            time.sleep(poll_interval)
        
        return {"available": False, "item": None, "elapsed_seconds": int(time.time()-start), "timeout": True}
    
    def close(self):
        self.client.close()
    
    def __enter__(self): return self
    def __exit__(self, *args): self.close(); return False

def create_jellyfin_checker(prefix: str = "MEDIA_COPILOT") -> Optional[JellyfinChecker]:
    return JellyfinChecker.from_env(prefix)
