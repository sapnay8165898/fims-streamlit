import os
import json
import hashlib
from datetime import datetime

def ensure_dirs():
    for d in ['data', 'data/baselines', 'logs']:
        os.makedirs(d, exist_ok=True)

def human_size(nbytes):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if nbytes < 1024:
            return f"{nbytes:.1f} {unit}"
        nbytes /= 1024
    return f"{nbytes:.1f} PB"

def now_iso():
    return datetime.now().isoformat(timespec='seconds')