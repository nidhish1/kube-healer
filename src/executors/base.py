"""Base executor interface"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime


@dataclass
class ExecutionResult:
    """Result of action execution"""
    success: bool
    message: str
    output: Optional[str] = None
    duration_seconds: Optional[float] = None
    error: Optional[str] = None


class BaseExecutor(ABC):
    """Abstract base class for action executors"""
    
    def __init__(self, dry_run: bool = False, max_retries: int = 3):
        self.dry_run = dry_run
        self.max_retries = max_retries
    
    @abstractmethod
    async def execute(self, parameters: Dict[str, Any]) -> ExecutionResult:
        """Execute the action"""
        pass
    
    async def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate parameters before execution"""
        return True
    
    async def can_execute(self) -> bool:
        """Check if execution is safe to proceed"""
        return True
