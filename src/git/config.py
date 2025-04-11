import yaml
from typing import Dict

def load_config(config_path: str = "config.yaml") -> Dict:
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        return {"folders": ["."]}  # Default to current directory 