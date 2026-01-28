"""Watcher manager"""
from typing import List, Callable, Awaitable
from .base import BaseWatcher, LogEvent
from .file_watcher import FileWatcher
from ..utils.config import WatcherConfig
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class WatcherManager:
    """Manage multiple watchers"""
    
    def __init__(self, callback: Callable[[LogEvent], Awaitable[None]]):
        self.callback = callback
        self.watchers: List[BaseWatcher] = []
    
    def add_watcher_from_config(self, config: WatcherConfig):
        """Add watcher from configuration"""
        if not config.enabled:
            logger.info(f"Skipping disabled watcher: {config.path}")
            return
        
        if config.type == "file":
            watcher = FileWatcher(
                file_path=config.path,
                patterns=config.patterns,
                callback=self.callback
            )
            self.watchers.append(watcher)
            logger.info(f"Added file watcher: {config.path}")
        else:
            logger.warning(f"Unknown watcher type: {config.type}")
    
    async def start_all(self):
        """Start all watchers"""
        for watcher in self.watchers:
            await watcher.start()
        logger.info(f"Started {len(self.watchers)} watchers")
    
    async def stop_all(self):
        """Stop all watchers"""
        for watcher in self.watchers:
            await watcher.stop()
        logger.info("Stopped all watchers")
