#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Media Copilot - Media Search: 统一搜索入口 (优先 Overseerr,  fallback 到 Arr)
"""

__version__ = "1.0.0"

import os
import logging
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from enum import Enum

from .api_client import OverseerrClient, ArrClient, ServiceType, create_client, load_env_config, APIResponse
from .arr_manager import ArrManager, MediaType, create_arr_manager

logger = logging.getLogger("media-copilot.search")

class SearchSource(Enum):
    OVERSEERR = "overseerr"
    RADARR = "radarr"
    SONARR = "sonarr"
    PROWLARR = "prowlarr"

@dataclass
class SearchResult:
    title: str
    media_type: str  # "movie" or "tv"
    source: SearchSource
    tmdb_id: Optional[int] = None
    tvdb_id: Optional[int] = None
    year: Optional[int] = None
    overview: Optional[str] = None
    poster: Optional[str] = None
    quality_hints: List[str] = None
    raw_data: Optional[Dict] = None
    
    def __post_init__(self):
        if self.quality_hints is None:
            self.quality_hints = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if k != "raw_data"}

class MediaSearch:
    def __init__(self, overseerr_url: Optional[str] = None, overseerr_key: Optional[str] = None,
                 arr_manager: Optional[ArrManager] = None):
        self.overseerr = None
        if overseerr_url and overseerr_key:
            self.overseerr = OverseerrClient(overseerr_url, overseerr_key)
            logger.info(f"✅ Search: Overseerr enabled")
        self.arr = arr_manager or create_arr_manager()
    
    @classmethod
    def from_env(cls, prefix: str = "MEDIA_COPILOT") -> "MediaSearch":
        overseerr_url = os.getenv(f"{prefix}_OVERSEERR_URL")
        overseerr_key = os.getenv(f"{prefix}_OVERSEERR_API_KEY") or os.getenv("MEDIA_COPILOT_OVERSEERR_API_KEY")
        return cls(overseerr_url, overseerr_key)
    
    def search(self, query: str, media_type: Optional[str] = None, 
               quality_hint: Optional[str] = None, limit: int = 10) -> List[SearchResult]:
        """
        统一搜索: 优先 Overseerr, 失败则 fallback 到对应 Arr 实例
        """
        results = []
        
        # 1. 尝试 Overseerr (统一入口)
        if self.overseerr:
            try:
                mt = media_type if media_type in ["movie", "tv"] else "movie"
                resp = self.overseerr.search(query, media_type=mt, language="zh-CN")
                if resp.success and resp.data:
                    items = resp.data.get("results", []) if isinstance(resp.data, dict) else resp.data
                    for item in items[:limit]:
                        if not isinstance(item, dict): continue
                        results.append(self._parse_overseerr_result(item, mt))
                    if results:
                        logger.info(f"🔍 Found {len(results)} results from Overseerr")
                        return self._filter_by_quality(results, quality_hint)
            except Exception as e:
                logger.warning(f"⚠️ Overseerr search failed: {e}, falling back to Arr")
        
        # 2. Fallback 到 Arr 实例搜索
        mt = MediaType.MOVIE if (not media_type or media_type == "movie") else MediaType.SERIES
        req = type('obj', (object,), {'media_type': mt, 'title': query, 'quality_hint': quality_hint})
        resp = self.arr.search_media(req)  # type: ignore
        if resp.success and resp.data:
            items = resp.data if isinstance(resp.data, list) else (resp.data.get("records", []) if isinstance(resp.data, dict) else [])
            for item in items[:limit]:
                if not isinstance(item, dict): continue
                results.append(self._parse_arr_result(item, mt))
        
        logger.info(f"🔍 Found {len(results)} results from Arr fallback")
        return self._filter_by_quality(results, quality_hint)
    
    def _parse_overseerr_result(self, item: Dict, media_type: str) -> SearchResult:
        return SearchResult(
            title=item.get("title") or item.get("name", "Unknown"),
            media_type=media_type,
            source=SearchSource.OVERSEERR,
            tmdb_id=item.get("id") if media_type == "movie" else None,
            tvdb_id=item.get("tvdbId") if media_type == "tv" else None,
            year=item.get("releaseDate", "")[:4] if item.get("releaseDate") else None,
            overview=item.get("overview"),
            poster=item.get("posterPath"),
            quality_hints=self._extract_quality_hints(item),
            raw_data=item
        )
    
    def _parse_arr_result(self, item: Dict, media_type: MediaType) -> SearchResult:
        mt_str = "movie" if media_type == MediaType.MOVIE else "tv"
        return SearchResult(
            title=item.get("title") or item.get("seriesName", "Unknown"),
            media_type=mt_str,
            source=SearchSource.RADARR if media_type == MediaType.MOVIE else SearchSource.SONARR,
            tmdb_id=item.get("tmdbId") if media_type == MediaType.MOVIE else None,
            tvdb_id=item.get("tvdbId") if media_type == MediaType.SERIES else None,
            year=item.get("year"),
            overview=item.get("overview"),
            poster=item.get("images", [{}])[0].get("url") if item.get("images") else None,
            quality_hints=[item.get("qualityProfileName", "")] if item.get("qualityProfileName") else [],
            raw_data=item
        )
    
    def _extract_quality_hints(self, item: Dict) -> List[str]:
        hints = []
        # Overseerr 可能包含质量信息
        if item.get("mediaInfo"):
            mi = item["mediaInfo"]
            if mi.get("video_4k"): hints.append("4k")
            if mi.get("video_hd"): hints.append("1080p")
        return hints
    
    def _filter_by_quality(self, results: List[SearchResult], quality_hint: Optional[str]) -> List[SearchResult]:
        if not quality_hint:
            return results
        q = quality_hint.lower()
        if q in ["4k", "uhd", "2160p"]:
            return [r for r in results if any(h in ["4k", "uhd", "2160p"] for h in r.quality_hints)] or results
        return results
    
    def get_media_details(self, media_type: str, media_id: int) -> Optional[Dict[str, Any]]:
        """获取媒体详情 (优先 Overseerr)"""
        if self.overseerr:
            resp = self.overseerr.get_media(media_type, media_id)
            if resp.success:
                return resp.data
        return None
    
    def close(self):
        if self.overseerr: self.overseerr.close()
        self.arr.close()
    
    def __enter__(self): return self
    def __exit__(self, *args): self.close(); return False

def create_media_search(prefix: str = "MEDIA_COPILOT") -> MediaSearch:
    return MediaSearch.from_env(prefix)
