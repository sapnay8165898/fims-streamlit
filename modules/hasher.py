import os
import hashlib
import stat
from datetime import datetime
from modules.utils import human_size, now_iso

CHUNK = 65536  # 64 KB read chunks (efficient for large files)

def hash_file(path, algo='sha256'):
    """Return hex digest of a file, or None on error."""
    try:
        h = hashlib.new(algo)
        with open(path, 'rb') as f:
            while True:
                chunk = f.read(CHUNK)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()
    except (PermissionError, FileNotFoundError, OSError):
        return None

def file_metadata(path, algo='sha256'):
    """Collect hash + metadata for one file."""
    try:
        st = os.stat(path)
        return {
            'path': os.path.abspath(path),
            'size': st.st_size,
            'size_human': human_size(st.st_size),
            'mtime': datetime.fromtimestamp(st.st_mtime).isoformat(timespec='seconds'),
            'ctime': datetime.fromtimestamp(st.st_ctime).isoformat(timespec='seconds'),
            'mode': oct(stat.S_IMODE(st.st_mode)),
            'uid': st.st_uid,
            'gid': st.st_gid,
            'hash': hash_file(path, algo),
            'algo': algo,
            'scanned_at': now_iso(),
        }
    except (PermissionError, FileNotFoundError, OSError):
        return None

def scan_directory(root, algo='sha256', extensions=None, max_size_mb=None,
                   exclude_dirs=None, progress_callback=None):
    """
    Walk a directory and return {abs_path: metadata}.
    extensions: list like ['.txt', '.conf'] or None for all
    exclude_dirs: list of folder names to skip (e.g. ['node_modules', '.git'])
    """
    exclude_dirs = set(exclude_dirs or [])
    extensions = set(e.lower() for e in extensions) if extensions else None
    max_bytes = max_size_mb * 1024 * 1024 if max_size_mb else None

    results = {}
    files = []

    # First, gather list of files (so progress bar knows total)
    for dirpath, dirnames, filenames in os.walk(root):
        # prune excluded dirs
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        for name in filenames:
            files.append(os.path.join(dirpath, name))

    total = len(files)
    for i, full in enumerate(files):
        if extensions:
            ext = os.path.splitext(full)[1].lower()
            if ext not in extensions:
                continue
        if max_bytes:
            try:
                if os.path.getsize(full) > max_bytes:
                    continue
            except OSError:
                continue

        meta = file_metadata(full, algo)
        if meta:
            results[meta['path']] = meta

        if progress_callback and (i % 25 == 0 or i == total - 1):
            progress_callback(i + 1, total)

    return results