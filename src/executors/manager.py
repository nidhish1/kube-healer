"""Executor manager"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from .base import BaseExecutor, ExecutionResult
from .disk_cleaner import DiskCleanupExecutor
from .service_manager import ServiceRestartExecutor, ProcessKillExecutor
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class ExecutorManager:
    """Manage action executors"""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.executors: Dict[str, BaseExecutor] = {
            "cleanup_disk": DiskCleanupExecutor(dry_run=dry_run),
            "restart_service": ServiceRestartExecutor(dry_run=dry_run),
            "kill_process": ProcessKillExecutor(dry_run=dry_run),
            "cleanup_cache": DiskCleanupExecutor(dry_run=dry_run),  # Same as disk cleanup
        }
        self.last_execution: Dict[str, datetime] = {}
        self.cooldowns: Dict[str, int] = {}
    
    def set_cooldown(self, action_type: str, seconds: int):
        """Set cooldown period for action type"""
        self.cooldowns[action_type] = seconds
    
    def is_in_cooldown(self, action_type: str) -> bool:
        """Check if action is in cooldown period"""
        if action_type not in self.cooldowns:
            return False
        
        if action_type not in self.last_execution:
            return False
        
        cooldown_seconds = self.cooldowns[action_type]
        elapsed = (datetime.utcnow() - self.last_execution[action_type]).total_seconds()
        
        return elapsed < cooldown_seconds
    
    def get_cooldown_remaining(self, action_type: str) -> int:
        """Get remaining cooldown seconds"""
        if not self.is_in_cooldown(action_type):
            return 0
        
        cooldown_seconds = self.cooldowns[action_type]
        elapsed = (datetime.utcnow() - self.last_execution[action_type]).total_seconds()
        
        return int(cooldown_seconds - elapsed)
    
    async def execute_action(self, action_type: str, parameters: Dict[str, Any]) -> ExecutionResult:
        """Execute action with cooldown check"""
        # Check cooldown
        if self.is_in_cooldown(action_type):
            remaining = self.get_cooldown_remaining(action_type)
            logger.warning(f"Action {action_type} is in cooldown. Wait {remaining}s")
            return ExecutionResult(
                success=False,
                message=f"Cooldown active. Wait {remaining}s",
                error=f"Action in cooldown period"
            )
        
        # Get executor
        executor = self.executors.get(action_type)
        if not executor:
            logger.error(f"Unknown action type: {action_type}")
            return ExecutionResult(
                success=False,
                message=f"Unknown action type: {action_type}",
                error="Executor not found"
            )
        
        # Execute
        logger.info(f"Executing action: {action_type}")
        result = await executor.execute(parameters)
        
        # Update last execution time
        if result.success:
            self.last_execution[action_type] = datetime.utcnow()
        
        return result
