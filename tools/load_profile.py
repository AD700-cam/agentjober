import os
import json

_PROFILE_CACHE = {}
_PROFILE_MTIMES = {}

def load_profile(profile_path="data/master_profile.json"):
    """Loads candidate profile details from JSON, automatically resolving relative paths and caching results."""
    global _PROFILE_CACHE, _PROFILE_MTIMES
    if not os.path.exists(profile_path):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        resolved_path = os.path.join(base_dir, "data", "master_profile.json")
    else:
        resolved_path = os.path.abspath(profile_path)
        
    if not os.path.exists(resolved_path):
        raise FileNotFoundError(f"Profile file not found at {profile_path} or {resolved_path}")
        
    try:
        mtime = os.path.getmtime(resolved_path)
        if resolved_path in _PROFILE_CACHE and _PROFILE_MTIMES.get(resolved_path) == mtime:
            return _PROFILE_CACHE[resolved_path]
            
        with open(resolved_path, "r", encoding="utf-8") as file:
            data = json.load(file)
            _PROFILE_CACHE[resolved_path] = data
            _PROFILE_MTIMES[resolved_path] = mtime
            return data
    except Exception as e:
        if resolved_path in _PROFILE_CACHE:
            return _PROFILE_CACHE[resolved_path]
        raise e
