"""Disk cleanup executor"""
import os
import time
import shutil
from typing import Dict, Any
from datetime import datetime, timedelta
from .base import BaseExecutor, ExecutionResult
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class DiskCleanupExecutor(BaseExecutor):
    """Clean up disk space"""
    
    async def execute(self, parameters: Dict[str, Any]) -> ExecutionResult:
        """Execute disk cleanup"""
        start_time = time.time()
        
        paths = parameters.get("paths", ["/tmp"])
        keep_days = parameters.get("keep_days", 7)
        min_file_size = parameters.get("min_file_size_mb", 1)
        
        if self.dry_run:
            return ExecutionResult(
                success=True,
                message=f"[DRY RUN] Would clean files older than {keep_days} days in {paths}",
                duration_seconds=time.time() - start_time
            )
        
        try:
            cleaned_count = 0
            freed_bytes = 0
            cutoff_time = datetime.now() - timedelta(days=keep_days)
            
            for path in paths:
                if not os.path.exists(path):
                    logger.warning(f"Path does not exist: {path}")
                    continue
                
                for root, dirs, files in os.walk(path):
                    for filename in files:
                        filepath = os.path.join(root, filename)
                        
                        try:
                            # Get file stats
                            stat = os.stat(filepath)
                            file_mtime = datetime.fromtimestamp(stat.st_mtime)
                            file_size_mb = stat.st_size / (1024 * 1024)
                            
                            # Check if file should be deleted
                            if file_mtime < cutoff_time and file_size_mb >= min_file_size:
                                freed_bytes += stat.st_size
                                os.remove(filepath)
                                cleaned_count += 1
                                logger.debug(f"Deleted: {filepath} ({file_size_mb:.2f} MB)")
                        
                        except Exception as e:
                            logger.warning(f"Could not delete {filepath}: {e}")
            
            freed_mb = freed_bytes / (1024 * 1024)
            duration = time.time() - start_time
            
            return ExecutionResult(
                success=True,
                message=f"Cleaned {cleaned_count} files, freed {freed_mb:.2f} MB",
                output=f"Paths: {paths}, Files: {cleaned_count}, Space: {freed_mb:.2f} MB",
                duration_seconds=duration
            )
        
        except Exception as e:
            logger.error(f"Disk cleanup failed: {e}")
            return ExecutionResult(
                success=False,
                message="Disk cleanup failed",
                error=str(e),
                duration_seconds=time.time() - start_time
            )
