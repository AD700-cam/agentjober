import os
import json

def load_profile(profile_path="data/master_profile.json"):
    """Loads candidate profile details from JSON, automatically resolving relative paths."""
    if not os.path.exists(profile_path):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        profile_path = os.path.join(base_dir, "data", "master_profile.json")
        
    with open(profile_path, "r", encoding="utf-8") as file:
        return json.load(file)
