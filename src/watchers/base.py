"""Base watcher interface"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Callable, Awaitable


@dataclass
class LogEvent:
    """Log event data"""
    source: str
    message: str
    timestamp: datetime
    line_number: Optional[int] = None
    matched_pattern: Optional[str] = None


class BaseWatcher(ABC):
    """Abstract base class for log watchers"""
    
    def __init__(self, callback: Callable[[LogEvent], Awaitable[None]]):
        self.callback = callback
        self.running = False
    
    @abstractmethod
    async def start(self):
        """Start watching"""
        pass
    
    @abstractmethod
    async def stop(self):
        """Stop watching"""
        pass
