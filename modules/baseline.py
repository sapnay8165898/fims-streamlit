import os
import json
from datetime import datetime
from modules.utils import ensure_dirs, now_iso

BASELINE_DIR = 'data/baselines'

def save_baseline(files, name='default'):
    ensure_dirs()
    os.makedirs(BASELINE_DIR, exist_ok=True)
    payload = {
        'name': name,
        'created_at': now_iso(),
        'file_count': len(files),
        'files': files,
    }
    path = os.path.join(BASELINE_DIR, f"{name}.json")
    with open(path, 'w') as f:
        json.dump(payload, f, indent=2)
    return path

def load_baseline(name='default'):
    path = os.path.join(BASELINE_DIR, f"{name}.json")
    if not os.path.exists(path):
        return None
    with open(path, 'r') as f:
        return json.load(f)

def list_baselines():
    ensure_dirs()
    os.makedirs(BASELINE_DIR, exist_ok=True)
    names = []
    for fn in os.listdir(BASELINE_DIR):
        if fn.endswith('.json'):
            names.append(fn[:-5])
    return sorted(names)

def delete_baseline(name):
    path = os.path.join(BASELINE_DIR, f"{name}.json")
    if os.path.exists(path):
        os.remove(path)
        return True
    return False

def diff_baseline(old_files, new_files):
    """
    Compare two {path: metadata} dicts.
    Returns dict with added / modified / deleted / permission_changed.
    """
    old_paths = set(old_files.keys())
    new_paths = set(new_files.keys())

    added = [new_files[p] for p in (new_paths - old_paths)]

    deleted = [old_files[p] for p in (old_paths - new_paths)]

    modified = []
    permission_changed = []
    for p in (old_paths & new_paths):
        o = old_files[p]
        n = new_files[p]
        if o.get('hash') != n.get('hash'):
            modified.append({
                'path': p,
                'old_hash': o.get('hash'),
                'new_hash': n.get('hash'),
                'old_mtime': o.get('mtime'),
                'new_mtime': n.get('mtime'),
                'old_size': o.get('size_human'),
                'new_size': n.get('size_human'),
            })
        elif o.get('mode') != n.get('mode') or o.get('uid') != n.get('uid'):
            permission_changed.append({
                'path': p,
                'old_mode': o.get('mode'),
                'new_mode': n.get('mode'),
                'old_uid': o.get('uid'),
                'new_uid': n.get('uid'),
            })

    return {
        'added': added,
        'modified': modified,
        'deleted': deleted,
        'permission_changed': permission_changed,
        'scanned_at': now_iso(),
    }