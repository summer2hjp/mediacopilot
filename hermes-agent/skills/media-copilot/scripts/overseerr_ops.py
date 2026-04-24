#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Media Copilot - Overseerr Ops: Overseerr API 操作封装
"""

__version__ = "1.0.0"

import os
import logging
from typing import Optional, Dict, List, Any
from dataclasses import dataclass

from .api_client import OverseerrClient, APIResponse, load_env_config

logger = logging.getLogger("media-copilot.overseerr")

@dataclass
class RequestResult:
    success: bool
    request_id: Optional[int] = None
    media_id: Optional[int] = None
    status: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}

class OverseerrOps:
    def __init__(self, base_url: str, api_key: str, timeout: int = 30, verify_ssl: bool = True):
        self.client = OverseerrClient(base_url, api_key, timeout=timeout, verify_ssl=verify_ssl)
        logger.info(f"✅ OverseerrOps: {base_url}")
    
    @classmethod
    def from_env(cls, prefix: str = "MEDIA_COPILOT") -> Optional["OverseerrOps"]:
        url = os.getenv(f"{prefix}_OVERSEERR_URL")
        key = os.getenv(f"{prefix}_OVERSEERR_API_KEY") or os.getenv("MEDIA_COPILOT_OVERSEERR_API_KEY")
        if not url or not key:
            logger.error("❌ Overseerr config missing")
            return None
        return cls(url, key)
    
    def search(self, query: str, media_type: str = "movie", page: int = 1, 
               language: str = "zh-CN") -> APIResponse:
        """搜索媒体"""
        return self.client.search(query, media_type=media_type, page=page, language=language)
    
    def get_media_info(self, media_type: str, media_id: int) -> APIResponse:
        """获取媒体详情"""
        return self.client.get_media(media_type, media_id)
    
    def request_movie(self, tmdb_id: int, is4k: bool = False, user_id: str = "1") -> RequestResult:
        """请求电影"""
        resp = self.client.request_media("movie", tmdb_id, is4k=is4k, user_id=user_id)
        return self._parse_request_response(resp, "movie", tmdb_id)
    
    def request_series(self, tmdb_id: int, seasons: Optional[List[int]] = None, 
                       is4k: bool = False, user_id: str = "1") -> RequestResult:
        """请求剧集"""
        resp = self.client.request_media("tv", tmdb_id, is4k=is4k, seasons=seasons, user_id=user_id)
        return self._parse_request_response(resp, "tv", tmdb_id)
    
    def _parse_request_response(self, resp: APIResponse, media_type: str, media_id: int) -> RequestResult:
        if resp.success and isinstance(resp.data, dict):
            return RequestResult(
                success=True,
                request_id=resp.data.get("id"),
                media_id=media_id,
                status=resp.data.get("status"),
                message=f"{media_type.title()} request submitted"
            )
        # 检查是否重复请求
        if resp.status_code == 409 or (resp.data and "already" in str(resp.data).lower()):
            return RequestResult(success=True, media_id=media_id, status="PENDING", 
                               message="Request already exists")
        return RequestResult(success=False, media_id=media_id, error=str(resp.error) if resp.error else "Unknown error")
    
    def get_requests(self, status: Optional[str] = None, take: int = 20) -> APIResponse:
        """获取请求列表"""
        return self.client.get_requests(status=status, take=take)
    
    def get_request_status(self, request_id: int) -> APIResponse:
        """获取单个请求状态"""
        # Overseerr API: GET /api/v1/request/{requestId}
        return self.client.get(f"/api/v1/request/{request_id}")
    
    def check_media_availability(self, media_type: str, media_id: int) -> Dict[str, Any]:
        """
        检查媒体在各实例的可用性
        返回: {"overseerr": {...}, "radarr": {...}, "sonarr": {...}}
        """
        result = {"overseerr": None, "radarr": None, "sonarr": None}
        
        # 1. Overseerr 状态
        resp = self.client.get_media(media_type, media_id)
        if resp.success and isinstance(resp.data, dict):
            result["overseerr"] = {
                "status": resp.data.get("status"),
                "mediaAddedAt": resp.data.get("mediaAddedAt"),
                "is4k": resp.data.get("is4k") if media_type == "movie" else None
            }
        
        # 2. 检查 Radarr/Sonarr (需要额外配置, 此处简化)
        # 实际使用中可通过 arr_manager 查询
        
        return result
    
    def auto_request(self, query: str, is4k: bool = False, seasons: Optional[List[int]] = None) -> RequestResult:
        """
        智能请求: 搜索 + 自动提交
        1. 搜索媒体
        2. 取第一个结果
        3. 提交请求
        """
        # 搜索
        mt = "tv" if seasons is not None else "movie"
        search_resp = self.search(query, media_type=mt)
        if not search_resp.success or not search_resp.data:
            return RequestResult(success=False, error="Search failed or no results")
        
        results = search_resp.data.get("results", []) if isinstance(search_resp.data, dict) else search_resp.data
        if not results:
            return RequestResult(success=False, error="No results found")
        
        # 取第一个
        item = results[0]
        media_id = item.get("id")
        if not media_id:
            return RequestResult(success=False, error="Invalid result: no media ID")
        
        # 提交请求
        if mt == "movie":
            return self.request_movie(media_id, is4k=is4k)
        else:
            return self.request_series(media_id, seasons=seasons, is4k=is4k)
    
    def health_check(self) -> bool:
        """检查 Overseerr 服务状态"""
        return self.client.health_check("/api/v1/status")
    
    def close(self):
        self.client.close()
    
    def __enter__(self): return self
    def __exit__(self, *args): self.close(); return False

def create_overseerr_ops(prefix: str = "MEDIA_COPILOT") -> Optional[OverseerrOps]:
    return OverseerrOps.from_env(prefix)
