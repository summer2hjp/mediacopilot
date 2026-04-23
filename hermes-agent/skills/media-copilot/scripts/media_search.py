#!/usr/bin/env python3
"""使用 TMDB/TVDB API 搜索媒体信息，返回标准化结果"""

import argparse
import requests
import sys

def search_movie(query: str, year: int = None, api_key: str = None):
    """搜索电影"""
    url = "https://api.themoviedb.org/3/search/movie"
    params = {
        "api_key": api_key or "demo_key",  # 建议配置正式 key
        "query": query,
        "language": "zh-CN"
    }
    if year:
        params["year"] = year
    
    resp = requests.get(url, params=params)
    if resp.status_code == 200:
        results = resp.json().get("results", [])
        # 返回最匹配的结果
        if results:
            best = results[0]
            print(f"TMDB_ID:{best['id']}")
            print(f"TITLE:{best['title']}")
            print(f"YEAR:{best.get('release_date', '')[:4]}")
            print(f"OVERVIEW:{best.get('overview', '')[:200]}")
            return best
    return None

def search_series(query: str, year: int = None, api_key: str = None):
    """搜索电视剧（使用 TVDB 或 TMDB）"""
    # 类似实现...
    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", choices=["movie", "series"], required=True)
    parser.add_argument("--query", required=True)
    parser.add_argument("--year", type=int)
    parser.add_argument("--tmdb-api-key", default=None)
    args = parser.parse_args()
    
    if args.type == "movie":
        result = search_movie(args.query, args.year, args.tmdb_api_key)
    else:
        result = search_series(args.query, args.year, args.tmdb_api_key)
    
    if not result:
        print("ERROR: No results found", file=sys.stderr)
        sys.exit(1)
