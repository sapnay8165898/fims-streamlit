import os
import threading
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
#from modules.hashing import hash_file  # noqa  -- fix import
from modules.hasher import hash_file
from modules.alerts import log_change
from modules.utils import now_iso


class _Handler(FileSystemEventHandler):
    def __init__(self, extensions=None, exclude_dirs=None):
        self.extensions = set(e.lower() for e in extensions) if extensions else None
        self.exclude_dirs = set(exclude_dirs or [])

    def _skip(self, path):
        if any(f"{os.sep}{d}{os.sep}" in path for d in self.exclude_dirs):
            return True
        if self.extensions:
            return os.path.splitext(path)[1].lower() not in self.extensions
        return False

    def on_created(self, event):
        if event.is_directory or self._skip(event.src_path):
            return
        log_change({'timestamp': now_iso(), 'change_type': 'added',
                    'path': event.src_path,
                    'hash': hash_file(event.src_path)})

    def on_modified(self, event):
        if event.is_directory or self._skip(event.src_path):
            return
        log_change({'timestamp': now_iso(), 'change_type': 'modified',
                    'path': event.src_path,
                    'new_hash': hash_file(event.src_path)})

    def on_deleted(self, event):
        if event.is_directory or self._skip(event.src_path):
            return
        log_change({'timestamp': now_iso(), 'change_type': 'deleted',
                    'path': event.src_path})


class Watcher:
    def __init__(self):
        self.observer = None
        self.thread = None
        self.watching = False

    def start(self, path, extensions=None, exclude_dirs=None):
        if self.watching:
            return False
        handler = _Handler(extensions, exclude_dirs)
        self.observer = Observer()
        self.observer.schedule(handler, path, recursive=True)
        self.observer.start()
        self.watching = True
        return True

    def stop(self):
        if self.observer:
            self.observer.stop()
            self.observer.join(timeout=2)
        self.watching = False