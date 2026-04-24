#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Media Copilot - 统一API客户端模块
支持: Overseerr, Radarr, Sonarr, qBittorrent, Jellyfin, Prowlarr
特性: 多认证方式 | 指数退避重试 | 结构化日志 | 类型安全
"""

__version__ = "1.0.0"

import os
import time
import json
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Union, List, TypeVar, Generic
from urllib.parse import urljoin, urlparse
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum, auto
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ============================================================================
# 📋 配置与常量
# ============================================================================

DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_BACKOFF_FACTOR = 0.5
RETRY_STATUSES = [429, 500, 502, 503, 504]

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s"

class ServiceType(Enum):
    OVERSEERR = "overseerr"
    RADARR = "radarr"
    RADARR_4K = "radarr_4k"
    SONARR = "sonarr"
    SONARR_4K = "sonarr_4k"
    PROWLARR = "prowlarr"
    QBITTORRENT = "qbittorrent"
    JELLYFIN = "jellyfin"

class AuthType(Enum):
    HEADER_API_KEY = auto()
    HEADER_TOKEN = auto()
    COOKIE_SESSION = auto()
    NONE = auto()

# ============================================================================
# 🪵 日志系统
# ============================================================================

def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(level)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(handler)
    return logger

logger = setup_logger("media-copilot.api")

# ============================================================================
# ⚠️ 自定义异常
# ============================================================================

class APIError(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None,
                 response_body: Optional[str] = None, service: Optional[str] = None):
        self.message = message
        self.status_code = status_code
        self.response_body = response_body
        self.service = service
        self.timestamp = datetime.now()
        super().__init__(self.message)
    
    def __str__(self):
        parts = [f"[{self.service or 'API'}] {self.message}"]
        if self.status_code:
            parts.append(f"(HTTP {self.status_code})")
        return " ".join(parts)

class AuthenticationError(APIError): pass
class RateLimitError(APIError):
    def __init__(self, message: str, retry_after: Optional[int] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after
class ServiceUnavailableError(APIError): pass

# ============================================================================
# 📦 响应封装
# ============================================================================

T = TypeVar('T')

@dataclass
class APIResponse(Generic[T]):
    success: bool
    data: Optional[T] = None
    error: Optional[APIError] = None
    status_code: Optional[int] = None
    headers: Dict[str, str] = field(default_factory=dict)
    request_time: float = 0.0
    retries: int = 0
    
    def raise_for_error(self):
        if self.error:
            raise self.error
        return self
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "error": str(self.error) if self.error else None,
            "status_code": self.status_code,
            "request_time_ms": f"{self.request_time*1000:.1f}",
            "retries": self.retries
        }

# ============================================================================
# 🔧 基础客户端
# ============================================================================

class BaseAPIClient(ABC):
    def __init__(
        self, base_url: str, service_type: ServiceType, auth_type: AuthType,
        api_key: Optional[str] = None, username: Optional[str] = None,
        password: Optional[str] = None, timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES, verify_ssl: bool = True
    ):
        self.base_url = base_url.rstrip('/')
        self.service_type = service_type
        self.auth_type = auth_type
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self._session = self._create_session(max_retries)
        self._auth_headers: Dict[str, str] = {}
        self._cookie_jar = requests.cookies.RequestsCookieJar()
        self._setup_auth(api_key, username, password)
        logger.info(f"✅ {service_type.value.upper()} client: {self.base_url}")
    
    def _create_session(self, max_retries: int) -> requests.Session:
        session = requests.Session()
        retry = Retry(total=max_retries, backoff_factor=RETRY_BACKOFF_FACTOR,
                     status_forcelist=RETRY_STATUSES,
                     allowed_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
                     raise_on_status=False)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update({
            "User-Agent": f"MediaCopilot/{__version__} (Hermes-Agent)",
            "Accept": "application/json",
            "Content-Type": "application/json"
        })
        return session
    
    def _setup_auth(self, api_key: Optional[str], username: Optional[str], password: Optional[str]):
        if self.auth_type == AuthType.HEADER_API_KEY and api_key:
            self._auth_headers["X-Api-Key"] = api_key
        elif self.auth_type == AuthType.HEADER_TOKEN and api_key:
            self._auth_headers["X-Emby-Token"] = api_key
        elif self.auth_type == AuthType.COOKIE_SESSION and username and password:
            self._login_qbittorrent(username, password)
    
    def _login_qbittorrent(self, username: str, password: str):
        login_url = urljoin(self.base_url, "/api/v2/auth/login")
        try:
            resp = self._session.post(login_url, data={"username": username, "password": password},
                                     timeout=self.timeout, verify=self.verify_ssl)
            if resp.status_code == 200 and resp.text.strip() == "Ok.":
                logger.debug(f"🔑 qBittorrent session acquired")
            else:
                raise AuthenticationError("qBittorrent login failed", status_code=resp.status_code,
                                        response_body=resp.text, service=self.service_type.value)
        except requests.RequestException as e:
            raise AuthenticationError(f"qBittorrent connection error: {e}", service=self.service_type.value) from e
    
    def _build_url(self, endpoint: str) -> str:
        if endpoint.startswith("http"):
            return endpoint
        return urljoin(self.base_url, endpoint.lstrip('/'))
    
    def _log_request(self, method: str, url: str, kwargs: Dict[str, Any]):
        safe = kwargs.copy()
        if "headers" in safe:
            safe["headers"] = {k: ("***" if any(x in k.lower() for x in ["key","token","pass"]) else v)
                             for k,v in safe["headers"].items()}
        if "json" in safe and logger.level > logging.DEBUG:
            safe["json"] = "{...}"
        logger.debug(f"📤 {method} {url} | {safe.get('params')} | {safe.get('json')}")
    
    def _log_response(self, resp: requests.Response, duration: float):
        status = "🟢" if 200 <= resp.status_code < 300 else "🟡" if resp.status_code < 400 else "🔴"
        logger.debug(f"📥 {status} {resp.status_code} | {duration*1000:.1f}ms | {resp.url}")
    
    def _handle_error(self, resp: requests.Response) -> Optional[APIError]:
        if 200 <= resp.status_code < 300:
            return None
        msg = f"Request failed: {resp.reason}"
        try:
            d = resp.json()
            if isinstance(d, dict):
                msg = d.get("message") or d.get("error") or msg
        except: pass
        if resp.status_code == 401:
            return AuthenticationError(msg, status_code=401, response_body=resp.text, service=self.service_type.value)
        elif resp.status_code == 429:
            retry = int(resp.headers.get("Retry-After", 60))
            return RateLimitError(msg, retry_after=retry, status_code=429, response_body=resp.text, service=self.service_type.value)
        elif resp.status_code >= 500:
            return ServiceUnavailableError(msg, status_code=resp.status_code, response_body=resp.text, service=self.service_type.value)
        return APIError(msg, status_code=resp.status_code, response_body=resp.text, service=self.service_type.value)
    
    def _request(self, method: str, endpoint: str, params: Optional[Dict] = None,
                 json: Optional[Dict] = None, data: Optional[Union[Dict,str]] = None,
                 headers: Optional[Dict] = None, timeout: Optional[int] = None,
                 retry_count: int = 0) -> APIResponse:
        url = self._build_url(endpoint)
        timeout = timeout or self.timeout
        start = time.time()
        req_headers = {**self._auth_headers, **(headers or {})}
        self._log_request(method, url, {"params": params, "json": json, "headers": req_headers})
        
        try:
            resp = self._session.request(method.upper(), url, params=params, json=json, data=data,
                                        headers=req_headers, cookies=self._cookie_jar,
                                        timeout=timeout, verify=self.verify_ssl)
            duration = time.time() - start
            self._log_response(resp, duration)
            error = self._handle_error(resp)
            
            if error and isinstance(error, (RateLimitError, ServiceUnavailableError)) and retry_count < MAX_RETRIES:
                wait = RETRY_BACKOFF_FACTOR * (2 ** retry_count)
                if isinstance(error, RateLimitError) and error.retry_after:
                    wait = error.retry_after
                logger.warning(f"⏳ Retry {retry_count+1}/{MAX_RETRIES} after {wait}s: {error.message}")
                time.sleep(wait)
                return self._request(method, endpoint, params, json, data, headers, timeout, retry_count + 1)
            
            if error:
                return APIResponse(success=False, error=error, status_code=resp.status_code,
                                 headers=dict(resp.headers), request_time=duration, retries=retry_count)
            
            try:
                result = resp.json() if resp.content else None
            except json.JSONDecodeError:
                result = resp.text
            
            return APIResponse(success=True, data=result, status_code=resp.status_code,
                             headers=dict(resp.headers), request_time=duration, retries=retry_count)
            
        except requests.Timeout:
            return APIResponse(success=False, error=APIError(f"Timeout after {timeout}s", service=self.service_type.value),
                             request_time=time.time()-start, retries=retry_count)
        except requests.ConnectionError as e:
            return APIResponse(success=False, error=ServiceUnavailableError(f"Connection: {e}", service=self.service_type.value),
                             request_time=time.time()-start, retries=retry_count)
        except Exception as e:
            logger.exception(f"❌ Unexpected error")
            return APIResponse(success=False, error=APIError(f"Error: {e}", service=self.service_type.value),
                             request_time=time.time()-start, retries=retry_count)
    
    def get(self, endpoint: str, params: Optional[Dict] = None, **kwargs) -> APIResponse:
        return self._request("GET", endpoint, params=params, **kwargs)
    
    def post(self, endpoint: str, json: Optional[Dict] = None, data: Optional[Dict] = None, **kwargs) -> APIResponse:
        return self._request("POST", endpoint, json=json, data=data, **kwargs)
    
    def put(self, endpoint: str, json: Optional[Dict] = None, **kwargs) -> APIResponse:
        return self._request("PUT", endpoint, json=json, **kwargs)
    
    def delete(self, endpoint: str, **kwargs) -> APIResponse:
        return self._request("DELETE", endpoint, **kwargs)
    
    def health_check(self, endpoint: str = "/") -> bool:
        try:
            r = self._request("GET", endpoint, timeout=10)
            return r.success and r.status_code in [200, 204]
        except: return False
    
    def close(self):
        self._session.close()
    
    def __enter__(self): return self
    def __exit__(self, *args): self.close(); return False

# ============================================================================
# 🎬 服务专用客户端
# ============================================================================

class OverseerrClient(BaseAPIClient):
    def __init__(self, base_url: str, api_key: str, **kwargs):
        super().__init__(base_url, ServiceType.OVERSEERR, AuthType.HEADER_API_KEY, api_key=api_key, **kwargs)
    
    def search(self, query: str, media_type: str = "movie", page: int = 1, language: str = "zh-CN") -> APIResponse:
        return self.get("/api/v1/search", params={"query": query, "type": media_type, "page": page, "language": language})
    
    def get_media(self, media_type: str, media_id: int) -> APIResponse:
        return self.get(f"/api/v1/{media_type}/{media_id}")
    
    def request_media(self, media_type: str, media_id: int, is4k: bool = False,
                      seasons: Optional[List[int]] = None, user_id: str = "1") -> APIResponse:
        payload = {"mediaType": media_type, "mediaId": media_id, "is4k": is4k, "userId": int(user_id) if user_id.isdigit() else 1}
        if media_type == "tv" and seasons:
            payload["seasons"] = seasons
        return self.post("/api/v1/request", json=payload)
    
    def get_requests(self, status: Optional[str] = None, take: int = 20) -> APIResponse:
        params = {"take": take}
        if status: params["filter"] = status
        return self.get("/api/v1/request", params=params)

class ArrClient(BaseAPIClient):
    def __init__(self, base_url: str, api_key: str, service_type: ServiceType, **kwargs):
        super().__init__(base_url, service_type, AuthType.HEADER_API_KEY, api_key=api_key, **kwargs)
    
    def lookup(self, term: str) -> APIResponse:
        endpoint = "/api/v3/movie/lookup" if self.service_type in [ServiceType.RADARR, ServiceType.RADARR_4K] else "/api/v3/series/lookup"
        return self.get(endpoint, params={"term": term})
    
    def get_quality_profiles(self) -> APIResponse:
        return self.get("/api/v3/qualityprofile")
    
    def get_root_folders(self) -> APIResponse:
        return self.get("/api/v3/rootfolder")
    
    def get_queue(self, page: int = 1, page_size: int = 50) -> APIResponse:
        return self.get("/api/v3/queue", params={"page": page, "pageSize": page_size})
    
    def get_system_status(self) -> APIResponse:
        return self.get("/api/v3/system/status")
    
    def trigger_search(self, command: str, ids: List[int]) -> APIResponse:
        key = "movieIds" if command == "MoviesSearch" else "seriesIds"
        return self.post("/api/v3/command", json={"name": command, key: ids})

class RadarrClient(ArrClient):
    def __init__(self, base_url: str, api_key: str, **kwargs):
        super().__init__(base_url, api_key, ServiceType.RADARR, **kwargs)
    
    def add_movie(self, tmdb_id: int, title: str, quality_profile_id: int,
                  root_folder_path: str, monitored: bool = True, search_now: bool = True) -> APIResponse:
        return self.post("/api/v3/movie", json={
            "title": title, "tmdbId": tmdb_id, "qualityProfileId": quality_profile_id,
            "rootFolderPath": root_folder_path, "monitored": monitored,
            "addOptions": {"searchForMovie": search_now}
        })
    
    def get_movie(self, movie_id: int) -> APIResponse:
        return self.get(f"/api/v3/movie/{movie_id}")

class Radarr4KClient(RadarrClient):
    def __init__(self, base_url: str, api_key: str, **kwargs):
        super().__init__(base_url, api_key, **kwargs)
        self.service_type = ServiceType.RADARR_4K

class SonarrClient(ArrClient):
    def __init__(self, base_url: str, api_key: str, **kwargs):
        super().__init__(base_url, api_key, ServiceType.SONARR, **kwargs)
    
    def add_series(self, tvdb_id: int, title: str, quality_profile_id: int,
                   root_folder_path: str, seasons: Optional[List[int]] = None,
                   monitored: bool = True, search_now: bool = True) -> APIResponse:
        season_list = [{"seasonNumber": s, "monitored": True} for s in (seasons or [])]
        return self.post("/api/v3/series", json={
            "title": title, "tvdbId": tvdb_id, "qualityProfileId": quality_profile_id,
            "rootFolderPath": root_folder_path, "monitored": monitored,
            "seasons": season_list, "addOptions": {"searchForMissingEpisodes": search_now}
        })
    
    def get_series(self, series_id: int) -> APIResponse:
        return self.get(f"/api/v3/series/{series_id}")

class Sonarr4KClient(SonarrClient):
    def __init__(self, base_url: str, api_key: str, **kwargs):
        super().__init__(base_url, api_key, **kwargs)
        self.service_type = ServiceType.SONARR_4K

class ProwlarrClient(ArrClient):
    def __init__(self, base_url: str, api_key: str, **kwargs):
        super().__init__(base_url, api_key, ServiceType.PROWLARR, **kwargs)
    
    def search(self, query: str, categories: Optional[List[int]] = None, limit: int = 100) -> APIResponse:
        params = {"query": query, "limit": limit}
        if categories: params["categories"] = ",".join(map(str, categories))
        return self.get("/api/v1/search", params=params)
    
    def get_indexers(self) -> APIResponse:
        return self.get("/api/v1/indexer")

class QbittorrentClient(BaseAPIClient):
    def __init__(self, base_url: str, username: str, password: str, **kwargs):
        super().__init__(base_url, ServiceType.QBITTORRENT, AuthType.COOKIE_SESSION,
                        username=username, password=password, **kwargs)
    
    def _setup_auth(self, api_key, username, password):
        if username and password:
            self._login_qbittorrent(username, password)
    
    def get_torrents(self, hashes: Optional[Union[str, List[str]]] = None,
                     category: Optional[str] = None, state: Optional[str] = None) -> APIResponse:
        params = {}
        if hashes: params["hashes"] = "|".join(hashes) if isinstance(hashes, list) else hashes
        if category: params["category"] = category
        if state: params["state"] = state
        return self.get("/api/v2/torrents/info", params=params)
    
    def pause_torrents(self, hashes: Union[str, List[str]]) -> APIResponse:
        return self.post("/api/v2/torrents/pause", data={"hashes": "|".join(hashes) if isinstance(hashes, list) else hashes})
    
    def resume_torrents(self, hashes: Union[str, List[str]]) -> APIResponse:
        return self.post("/api/v2/torrents/resume", data={"hashes": "|".join(hashes) if isinstance(hashes, list) else hashes})
    
    def delete_torrents(self, hashes: Union[str, List[str]], delete_files: bool = False) -> APIResponse:
        return self.post("/api/v2/torrents/delete",
                        data={"hashes": "|".join(hashes) if isinstance(hashes, list) else hashes,
                              "deleteFiles": str(delete_files).lower()})
    
    def get_transfer_info(self) -> APIResponse:
        return self.get("/api/v2/transfer/info")

class JellyfinClient(BaseAPIClient):
    def __init__(self, base_url: str, api_key: str, **kwargs):
        super().__init__(base_url, ServiceType.JELLYFIN, AuthType.HEADER_TOKEN, api_key=api_key, **kwargs)
    
    def search_items(self, query: str, item_type: Optional[str] = None, limit: int = 20) -> APIResponse:
        params = {"SearchTerm": query, "Limit": limit, "Recursive": True}
        if item_type: params["IncludeItemTypes"] = item_type
        return self.get("/Items", params=params)
    
    def get_item(self, item_id: str) -> APIResponse:
        return self.get(f"/Users/me/Items/{item_id}")
    
    def refresh_library(self, item_id: Optional[str] = None) -> APIResponse:
        endpoint = f"/Items/{item_id}/Refresh" if item_id else "/Library/Refresh"
        return self.post(endpoint, params={"Recursive": True})

# ============================================================================
# 🏭 工厂函数
# ============================================================================

def create_client(service: ServiceType, config: Dict[str, Any]) -> BaseAPIClient:
    common = {"base_url": config["url"], "timeout": config.get("timeout", DEFAULT_TIMEOUT),
              "verify_ssl": config.get("verify_ssl", True)}
    if service == ServiceType.OVERSEERR:
        return OverseerrClient(api_key=config["api_key"], **common)
    elif service == ServiceType.RADARR:
        return RadarrClient(api_key=config["api_key"], **common)
    elif service == ServiceType.RADARR_4K:
        return Radarr4KClient(api_key=config["api_key"], **common)
    elif service == ServiceType.SONARR:
        return SonarrClient(api_key=config["api_key"], **common)
    elif service == ServiceType.SONARR_4K:
        return Sonarr4KClient(api_key=config["api_key"], **common)
    elif service == ServiceType.PROWLARR:
        return ProwlarrClient(api_key=config["api_key"], **common)
    elif service == ServiceType.QBITTORRENT:
        return QbittorrentClient(username=config.get("username","admin"), password=config["password"], **common)
    elif service == ServiceType.JELLYFIN:
        return JellyfinClient(api_key=config["api_key"], **common)
    raise ValueError(f"Unsupported: {service}")

def load_env_config(prefix: str = "MEDIA_COPILOT") -> Dict[str, Dict[str, Any]]:
    config = {}
    services = [
        ("OVERSEERR", ServiceType.OVERSEERR, True),
        ("RADARR", ServiceType.RADARR, True), ("RADARR_4K", ServiceType.RADARR_4K, True),
        ("SONARR", ServiceType.SONARR, True), ("SONARR_4K", ServiceType.SONARR_4K, True),
        ("PROWLARR", ServiceType.PROWLARR, True),
        ("QBITTORRENT", ServiceType.QBITTORRENT, False),
        ("JELLYFIN", ServiceType.JELLYFIN, True)
    ]
    for svc_key, svc_type, use_api_key in services:
        url = os.getenv(f"{prefix}_{svc_key}_URL")
        if not url: continue
        cfg = {"url": url}
        if use_api_key:
            key = os.getenv(f"{prefix}_{svc_key}_API_KEY")
            if key: cfg["api_key"] = key
        elif svc_type == ServiceType.QBITTORRENT:
            cfg["username"] = os.getenv(f"{prefix}_{svc_key}_USERNAME", "admin")
            cfg["password"] = os.getenv(f"{prefix}_{svc_key}_PASSWORD")
        if "api_key" in cfg or "password" in cfg:
            config[svc_key.lower()] = cfg
            logger.info(f"📦 Loaded {svc_key}: {url}")
    return config
