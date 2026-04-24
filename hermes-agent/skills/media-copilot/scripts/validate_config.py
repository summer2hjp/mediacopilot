#!/usr/bin/env python3
"""配置验证工具"""
import os, sys, yaml
from pathlib import Path

REQUIRED_KEYS = [
    "overseerr_url", "radarr_url", "sonarr_url", 
    "qbittorrent_url", "jellyfin_url",
    "default_quality_profile_movie", "default_quality_profile_series",
    "default_quality_profile_movie_4k", "default_quality_profile_series_4k",
    "default_root_folder_movie", "default_root_folder_series",
  "default_root_folder_movie_4k", "default_root_folder_series_4k"
]

def validate_config(config_path: str) -> bool:
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        
        mc = config.get("skills", {}).get("config", {}).get("media-copilot", {})
        
        missing = [k for k in REQUIRED_KEYS if k not in mc]
        if missing:
            print(f"❌ Missing required keys: {missing}")
            return False
        
        # 检查URL格式
        for key in mc:
            if key.endswith("_url") and mc[key]:
                if not mc[key].startswith("http"):
                    print(f"❌ Invalid URL format for {key}: {mc[key]}")
                    return False
        
        print("✅ Configuration valid!")
        return True
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "~/.hermes/config.yaml"
    sys.exit(0 if validate_config(Path(path).expanduser()) else 1)
