import os
import json
from modules.utils import ensure_dirs

ALERTS_FILE = 'data/changes.json'
LOG_FILE = 'logs/fims.log'

def _load():
    ensure_dirs()
    if not os.path.exists(ALERTS_FILE):
        return []
    try:
        with open(ALERTS_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def _save(alerts):
    ensure_dirs()
    with open(ALERTS_FILE, 'w') as f:
        json.dump(alerts[-2000:], f, indent=2)

def log_change(entry):
    ensure_dirs()
    alerts = _load()
    alerts.append(entry)
    _save(alerts)

    # Also append to plain-text log
    os.makedirs('logs', exist_ok=True)
    line = (f"[{entry.get('timestamp')}] {entry.get('change_type').upper():20s} "
            f"{entry.get('path')}\n")
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(line)

def load_alerts():
    return _load()

def clear_alerts():
    _save([])
    if os.path.exists(LOG_FILE):
        open(LOG_FILE, 'w').close()

def record_diff(diff_result):
    """Turn a diff dict into individual alert entries."""
    ts = diff_result['scanned_at']
    count = 0
    for f in diff_result['added']:
        log_change({'timestamp': ts, 'change_type': 'added',
                    'path': f['path'], 'hash': f.get('hash'),
                    'size': f.get('size_human')})
        count += 1
    for f in diff_result['modified']:
        log_change({'timestamp': ts, 'change_type': 'modified',
                    'path': f['path'], 'old_hash': f.get('old_hash'),
                    'new_hash': f.get('new_hash')})
        count += 1
    for f in diff_result['deleted']:
        log_change({'timestamp': ts, 'change_type': 'deleted',
                    'path': f['path']})
        count += 1
    for f in diff_result['permission_changed']:
        log_change({'timestamp': ts, 'change_type': 'permission',
                    'path': f['path'],
                    'old_mode': f.get('old_mode'), 'new_mode': f.get('new_mode')})
        count += 1
    return count