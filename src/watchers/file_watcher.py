"""File-based log watcher using watchdog"""
import os
import re
import asyncio
from datetime import datetime
from typing import List, Callable, Awaitable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent
from .base import BaseWatcher, LogEvent
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class FileWatcher(BaseWatcher):
    """Watch log files for pattern matches"""
    
    def __init__(self, file_path: str, patterns: List[str], 
                 callback: Callable[[LogEvent], Awaitable[None]]):
        super().__init__(callback)
        self.file_path = file_path
        self.patterns = [re.compile(p) for p in patterns]
        self.observer = None
        self.last_position = 0
        self.loop = None
    
    async def start(self):
        """Start watching file"""
        self.running = True
        self.loop = asyncio.get_event_loop()
        
        # Create file if it doesn't exist
        if not os.path.exists(self.file_path):
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            open(self.file_path, 'a').close()
            logger.info(f"Created log file: {self.file_path}")
        
        # Get initial file size
        self.last_position = os.path.getsize(self.file_path)
        
        # Setup watchdog observer
        event_handler = FileWatcherHandler(self)
        self.observer = Observer()
        self.observer.schedule(event_handler, os.path.dirname(self.file_path), recursive=False)
        self.observer.start()
        
        logger.info(f"Started watching: {self.file_path}")
    
    async def stop(self):
        """Stop watching"""
        self.running = False
        if self.observer:
            self.observer.stop()
            self.observer.join()
        logger.info(f"Stopped watching: {self.file_path}")
    
    async def _read_new_lines(self):
        """Read new lines from file"""
        try:
            if not os.path.exists(self.file_path):
                return
            
            current_size = os.path.getsize(self.file_path)
            
            if current_size < self.last_position:
                # File was truncated
                self.last_position = 0
            
            if current_size == self.last_position:
                return
            
            with open(self.file_path, 'r') as f:
                f.seek(self.last_position)
                new_lines = f.readlines()
                self.last_position = f.tell()
            
            # Process new lines
            for line_num, line in enumerate(new_lines, start=1):
                line = line.strip()
                if not line:
                    continue
                
                # Check patterns
                for pattern in self.patterns:
                    if pattern.search(line):
                        event = LogEvent(
                            source=self.file_path,
                            message=line,
                            timestamp=datetime.utcnow(),
                            matched_pattern=pattern.pattern
                        )
                        await self.callback(event)
                        break
        
        except Exception as e:
            logger.error(f"Error reading file: {e}")


class FileWatcherHandler(FileSystemEventHandler):
    """Watchdog event handler"""
    
    def __init__(self, file_watcher: FileWatcher):
        self.file_watcher = file_watcher
    
    def on_modified(self, event):
        """Handle file modification"""
        if isinstance(event, FileModifiedEvent) and event.src_path == self.file_watcher.file_path:
            if self.file_watcher.running and self.file_watcher.loop:
                # Schedule the async task in the main event loop
                asyncio.run_coroutine_threadsafe(
                    self.file_watcher._read_new_lines(),
                    self.file_watcher.loop
                )
