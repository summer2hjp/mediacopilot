#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Media Copilot - Arr Manager: 多实例 Radarr/Sonarr 管理 (支持 4K 分流)
"""

__version__ = "1.0.0"

import os
import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Dict, List, Tuple, Any

from .api_client import (
    APIResponse, APIError, ServiceType, create_client, load_env_config,
    RadarrClient, Radarr4KClient, SonarrClient, Sonarr4KClient
)

logger = logging.getLogger("media-copilot.arr")

class MediaType(Enum):
    MOVIE = "movie"
    SERIES = "series"

class InstanceRole(Enum):
    PRIMARY = auto()
    SECONDARY = auto()
    SPECIALIZED = auto()

@dataclass
class ArrInstanceConfig:
    name: str
    service_type: ServiceType
    url: str
    api_key_env: str
    quality_profile: str
    root_folder: str
    tags: List[str] = field(default_factory=list)
    is_4k: bool = False
    role: InstanceRole = InstanceRole.PRIMARY
    priority: int = 100
    enabled: bool = True
    timeout: int = 30
    verify_ssl: bool = True
    
    @property
    def api_key(self) -> Optional[str]:
        return os.getenv(self.api_key_env)
    
    def matches_quality(self, quality_hint: Optional[str]) -> bool:
        if not quality_hint:
            return not self.is_4k
        q = quality_hint.lower().strip()
        if self.is_4k:
            return q in ["4k", "uhd", "2160p", "ultra-hd"]
        return q not in ["4k", "uhd", "2160p", "ultra-hd"]
    
    def to_client_config(self) -> Dict[str, Any]:
        return {"url": self.url, "api_key": self.api_key, "timeout": self.timeout, "verify_ssl": self.verify_ssl}

@dataclass
class MediaRequest:
    media_type: MediaType
    title: str
    tmdb_id: Optional[int] = None
    tvdb_id: Optional[int] = None
    quality_hint: Optional[str] = None
    seasons: Optional[List[int]] = None
    auto_search: bool = True
    monitored: bool = True
    
    @property
    def media_id(self) -> Optional[int]:
        return self.tmdb_id if self.media_type == MediaType.MOVIE else self.tvdb_id
    
    def __str__(self) -> str:
        q = f" [{self.quality_hint.upper()}]" if self.quality_hint else ""
        return f"{self.media_type.value}: {self.title}{q}"

class ArrManager:
    def __init__(self, instances: List[ArrInstanceConfig]):
        self.instances = {cfg.name: cfg for cfg in instances if cfg.enabled}
        self._clients: Dict[str, Any] = {}
        self._profile_cache: Dict[str, Dict[str, int]] = {}
        logger.info(f"✅ ArrManager: {len(self.instances)} instances loaded")
    
    @classmethod
    def from_env(cls, prefix: str = "MEDIA_COPILOT") -> "ArrManager":
        instances = []
        # Radarr
        if os.getenv(f"{prefix}_RADARR_URL"):
            instances.append(ArrInstanceConfig(
                name="radarr_1080p", service_type=ServiceType.RADARR,
                url=os.getenv(f"{prefix}_RADARR_URL"),
                api_key_env=f"{prefix}_RADARR_API_KEY",
                quality_profile=os.getenv(f"{prefix}_DEFAULT_QUALITY_PROFILE_MOVIE", "HD-1080p"),
                root_folder=os.getenv(f"{prefix}_DEFAULT_ROOT_FOLDER_MOVIE", "/movies"),
                tags=["1080p", "hd", "default"], is_4k=False, role=InstanceRole.PRIMARY, priority=100
            ))
        if os.getenv(f"{prefix}_RADARR_4K_URL"):
            instances.append(ArrInstanceConfig(
                name="radarr_4k", service_type=ServiceType.RADARR_4K,
                url=os.getenv(f"{prefix}_RADARR_4K_URL"),
                api_key_env=f"{prefix}_RADARR_4K_API_KEY",
                quality_profile=os.getenv(f"{prefix}_DEFAULT_QUALITY_PROFILE_MOVIE_4K", "Ultra-HD"),
                root_folder=os.getenv(f"{prefix}_DEFAULT_ROOT_FOLDER_MOVIE", "/movies"),
                tags=["4k", "uhd", "2160p"], is_4k=True, role=InstanceRole.SPECIALIZED, priority=50
            ))
        # Sonarr
        if os.getenv(f"{prefix}_SONARR_URL"):
            instances.append(ArrInstanceConfig(
                name="sonarr_1080p", service_type=ServiceType.SONARR,
                url=os.getenv(f"{prefix}_SONARR_URL"),
                api_key_env=f"{prefix}_SONARR_API_KEY",
                quality_profile=os.getenv(f"{prefix}_DEFAULT_QUALITY_PROFILE_SERIES", "HD-1080p"),
                root_folder=os.getenv(f"{prefix}_DEFAULT_ROOT_FOLDER_SERIES", "/tvshows"),
                tags=["1080p", "hd", "default"], is_4k=False, role=InstanceRole.PRIMARY, priority=100
            ))
        if os.getenv(f"{prefix}_SONARR_4K_URL"):
            instances.append(ArrInstanceConfig(
                name="sonarr_4k", service_type=ServiceType.SONARR_4K,
                url=os.getenv(f"{prefix}_SONARR_4K_URL"),
                api_key_env=f"{prefix}_SONARR_4K_API_KEY",
                quality_profile=os.getenv(f"{prefix}_DEFAULT_QUALITY_PROFILE_SERIES_4K", "Ultra-HD"),
                root_folder=os.getenv(f"{prefix}_DEFAULT_ROOT_FOLDER_SERIES", "/tvshows"),
                tags=["4k", "uhd", "2160p"], is_4k=True, role=InstanceRole.SPECIALIZED, priority=50
            ))
        return cls(instances)
    
    def _get_client(self, cfg: ArrInstanceConfig) -> Any:
        if cfg.name not in self._clients:
            self._clients[cfg.name] = create_client(cfg.service_type, cfg.to_client_config())
        return self._clients[cfg.name]
    
    def _get_quality_id(self, cfg: ArrInstanceConfig, profile_name: str) -> Optional[int]:
        if cfg.name in self._profile_cache and profile_name in self._profile_cache[cfg.name]:
            return self._profile_cache[cfg.name][profile_name]
        try:
            resp = self._get_client(cfg).get_quality_profiles()
            if resp.success and isinstance(resp.data, list):
                profiles = {p["name"]: p["id"] for p in resp.data if "name" in p and "id" in p}
                self._profile_cache[cfg.name] = profiles
                if profile_name in profiles:
                    return profiles[profile_name]
                return next(iter(profiles.values()), None)
        except Exception as e:
            logger.error(f"❌ Failed to get quality profiles for {cfg.name}: {e}")
        return None
    
    def _select_instance(self, request: MediaRequest) -> Optional[ArrInstanceConfig]:
        candidates = [c for c in self.instances.values() 
                     if c.service_type in [ServiceType.RADARR, ServiceType.RADARR_4K] if request.media_type == MediaType.MOVIE
                     else c.service_type in [ServiceType.SONARR, ServiceType.SONARR_4K] if request.media_type == MediaType.SERIES
                     else False]
        candidates = [c for c in candidates if c.matches_quality(request.quality_hint)]
        if not candidates and request.quality_hint:
            request.quality_hint = None
            return self._select_instance(request)
        if not candidates:
            return None
        role_order = {InstanceRole.SPECIALIZED: 0, InstanceRole.PRIMARY: 1, InstanceRole.SECONDARY: 2}
        candidates.sort(key=lambda c: (role_order[c.role], c.priority, c.name))
        return candidates[0]
    
    def add_media(self, request: MediaRequest, instance_override: Optional[str] = None) -> Tuple[bool, Optional[Dict], Optional[str]]:
        cfg = self.instances.get(instance_override) if instance_override else self._select_instance(request)
        if not cfg:
            return False, None, "No suitable instance found"
        
        quality_id = self._get_quality_id(cfg, cfg.quality_profile)
        if not quality_id:
            return False, None, f"Quality profile '{cfg.quality_profile}' not found"
        
        client = self._get_client(cfg)
        try:
            if cfg.service_type in [ServiceType.RADARR, ServiceType.RADARR_4K] and request.media_type == MediaType.MOVIE:
                if not request.tmdb_id:
                    return False, None, "TMDB ID required"
                resp = client.add_movie(tmdb_id=request.tmdb_id, title=request.title,
                                       quality_profile_id=quality_id, root_folder_path=cfg.root_folder,
                                       monitored=request.monitored, search_now=request.auto_search)
            elif cfg.service_type in [ServiceType.SONARR, ServiceType.SONARR_4K] and request.media_type == MediaType.SERIES:
                if not request.tvdb_id:
                    return False, None, "TVDB ID required"
                resp = client.add_series(tvdb_id=request.tvdb_id, title=request.title,
                                        quality_profile_id=quality_id, root_folder_path=cfg.root_folder,
                                        seasons=request.seasons, monitored=request.monitored, search_now=request.auto_search)
            else:
                return False, None, f"Type mismatch: {request.media_type.value} for {cfg.service_type.value}"
            
            if resp.success:
                logger.info(f"✅ Added {request} to {cfg.name}")
                return True, resp.data, None
            return False, None, f"API error: {resp.error}"
        except Exception as e:
            logger.exception(f"❌ Exception adding {request}")
            return False, None, f"Exception: {e}"
    
    def search_media(self, request: MediaRequest, instance_name: Optional[str] = None) -> APIResponse:
        if instance_name:
            cfg = self.instances.get(instance_name)
            if not cfg:
                return APIResponse(success=False, error=APIError(f"Unknown instance: {instance_name}"))
        else:
            candidates = [c for c in self.instances.values()
                         if (c.service_type in [ServiceType.RADARR, ServiceType.RADARR_4K] if request.media_type == MediaType.MOVIE
                             else c.service_type in [ServiceType.SONARR, ServiceType.SONARR_4K])]
            if not candidates:
                return APIResponse(success=False, error=APIError("No instances available"))
            cfg = min(candidates, key=lambda c: c.priority)
        return self._get_client(cfg).lookup(request.title)
    
    def get_queue(self, service_type: ServiceType, include_4k: bool = True, page: int = 1, page_size: int = 50) -> Dict[str, Any]:
        results = {"instances": {}, "total_items": 0, "items": []}
        for cfg in self.instances.values():
            if cfg.service_type != service_type and (not include_4k or cfg.is_4k):
                continue
            try:
                resp = self._get_client(cfg).get_queue(page=page, page_size=page_size)
                if resp.success and resp.data:
                    items = resp.data.get("records", []) if isinstance(resp.data, dict) else resp.data
                    for item in items:
                        if isinstance(item, dict):
                            item["_instance"] = cfg.name
                            item["_is_4k"] = cfg.is_4k
                    results["instances"][cfg.name] = {"count": len(items), "is_4k": cfg.is_4k}
                    results["items"].extend(items)
                    results["total_items"] += len(items)
            except Exception as e:
                logger.warning(f"⚠️ Queue error for {cfg.name}: {e}")
                results["instances"][cfg.name] = {"error": str(e)}
        results["items"].sort(key=lambda x: self.instances.get(x.get("_instance"), ArrInstanceConfig("", ServiceType.RADARR, "", "", "", "")).priority)
        return results
    
    def trigger_search(self, media_type: MediaType, media_ids: List[int], instance_name: Optional[str] = None) -> Dict[str, Any]:
        results = {"success": [], "failed": []}
        instances = [self.instances[instance_name]] if instance_name and instance_name in self.instances else \
                   [c for c in self.instances.values() if (c.service_type in [ServiceType.RADARR, ServiceType.RADARR_4K] if media_type == MediaType.MOVIE else c.service_type in [ServiceType.SONARR, ServiceType.SONARR_4K])]
        for cfg in instances:
            try:
                cmd = "MoviesSearch" if media_type == MediaType.MOVIE else "SeriesSearch"
                resp = self._get_client(cfg).trigger_search(cmd, media_ids)
                if resp.success:
                    results["success"].append({"instance": cfg.name, "command_id": resp.data.get("id") if isinstance(resp.data, dict) else None})
                else:
                    results["failed"].append({"instance": cfg.name, "error": str(resp.error)})
            except Exception as e:
                results["failed"].append({"instance": cfg.name, "error": str(e)})
        return results
    
    def get_system_status(self, instance_name: Optional[str] = None) -> Dict[str, Any]:
        results = {}
        instances = [self.instances[instance_name]] if instance_name and instance_name in self.instances else self.instances.values()
        for cfg in instances:
            try:
                resp = self._get_client(cfg).get_system_status()
                results[cfg.name] = {"status": "online" if resp.success else "offline",
                                    "version": resp.data.get("version") if resp.success and isinstance(resp.data, dict) else None,
                                    "error": str(resp.error) if resp.error else None}
            except Exception as e:
                results[cfg.name] = {"status": "error", "error": str(e)}
        return results
    
    def close(self):
        for c in self._clients.values():
            c.close()
        self._clients.clear()
    
    def __enter__(self): return self
    def __exit__(self, *args): self.close(); return False

def create_arr_manager(prefix: str = "MEDIA_COPILOT") -> ArrManager:
    return ArrManager.from_env(prefix)
