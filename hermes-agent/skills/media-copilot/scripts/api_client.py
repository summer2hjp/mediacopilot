#!/usr/bin/env python3
"""统一封装各服务的 API 调用，处理认证、重试、错误"""

import requests
import json
from typing import Optional, Dict, List

class MediaAPI:
    def __init__(self, config: Dict):
        self.overseerr_url = config['overseerr_url']
        self.overseerr_key = config['overseerr_api_key']
        self.radarr_url = config['radarr_url']
        self.radarr_key = config['radarr_api_key']
        self.sonarr_url = config['sonarr_url']
        self.sonarr_key = config['sonarr_api_key']
        self.qb_url = config['qbittorrent_url']
        self.qb_user = config['qbittorrent_username']
        self.qb_pass = config['qbittorrent_password']
        self.prowlarr_url = config['prowlarr_url']
        self.prowlarr_key = config['prowlarr_api_key']
    
    def request_movie(self, tmdb_id: int, is4k: bool = False, 
                      quality_profile: str = None, root_folder: str = None) -> Dict:
        """通过 Overseerr 提交电影请求"""
        payload = {
            "mediaType": "movie",
            "mediaId": tmdb_id,
            "is4k": is4k
        }
        if quality_profile:
            payload["profileId"] = self._get_profile_id('radarr', quality_profile)
        if root_folder:
            payload["rootFolder"] = root_folder
        
        return self._post(f"{self.overseerr_url}/api/v1/request", payload, 
                         headers={"X-Api-Key": self.overseerr_key})
    
    def search_radarr(self, query: str, year: int = None) -> List[Dict]:
        """在 Radarr 中搜索电影"""
        params = {"term": query}
        if year:
            params["year"] = year
        return self._get(f"{self.radarr_url}/api/v3/movie/lookup", 
                        params=params, 
                        headers={"X-Api-Key": self.radarr_key})
    
    def add_to_radarr(self, tmdb_id: int, title: str, quality_profile: str,
                      root_folder: str, monitored: bool = True) -> Dict:
        """直接添加电影到 Radarr（绕过 Overseerr）"""
        payload = {
            "title": title,
            "tmdbId": tmdb_id,
            "qualityProfileId": self._get_profile_id('radarr', quality_profile),
            "rootFolderPath": root_folder,
            "monitored": monitored,
            "searchForMovie": True,  # 添加后立即搜索
            "addOptions": {
                "searchForMovie": True
            }
        }
        return self._post(f"{self.radarr_url}/api/v3/movie", payload,
                         headers={"X-Api-Key": self.radarr_key})
    
    def get_download_queue(self, service: str = 'radarr') -> List[Dict]:
        """获取下载队列"""
        url = f"{self.radarr_url if service=='radarr' else self.sonarr_url}/api/v3/queue"
        key = self.radarr_key if service=='radarr' else self.sonarr_key
        return self._get(url, params={"includeUnknownMovieItems": "true"},
                        headers={"X-Api-Key": key})
    
    def pause_qbittorrent_torrent(self, torrent_hash: str) -> bool:
        """暂停 qBittorrent 中的特定种子"""
        # 先登录获取 cookie
        session = requests.Session()
        login_data = {"username": self.qb_user, "password": self.qb_pass}
        session.post(f"{self.qb_url}/api/v2/auth/login", data=login_data)
        
        # 暂停种子
        resp = session.post(f"{self.qb_url}/api/v2/torrents/pause", 
                           data={"hashes": torrent_hash})
        return resp.status_code == 200
    
    def _get(self, url: str, params: Dict = None, headers: Dict = None) -> Dict:
        """通用 GET 请求"""
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            return {"error": str(e), "status": getattr(e.response, 'status_code', None)}
    
    def _post(self, url: str, data: Dict, headers: Dict = None) -> Dict:
        """通用 POST 请求"""
        try:
            resp = requests.post(url, json=data, headers=headers, timeout=60)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            return {"error": str(e), "status": getattr(e.response, 'status_code', None)}
    
    def _get_profile_id(self, service: str, profile_name: str) -> Optional[int]:
        """根据质量配置名称获取 ID"""
        # 实现缓存逻辑，避免重复查询
        pass
