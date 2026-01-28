"""Rule-based action planner (No AI needed)"""
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class ActionPlan:
    """Planned action"""
    action_type: str
    parameters: Dict[str, Any]
    confidence: float
    reasoning: str


class RuleBasedPlanner:
    """Plan actions based on predefined rules"""
    
    def __init__(self):
        self.rules = self._load_default_rules()
        logger.info(f"Loaded {len(self.rules)} default rules")
    
    def _load_default_rules(self) -> List[Dict[str, Any]]:
        """Load default healing rules"""
        return [
            {
                "name": "disk_full",
                "pattern": re.compile(r"(?i)(disk\s+(full|space)|no\s+space\s+left|filesystem\s+full)", re.IGNORECASE),
                "action": "cleanup_disk",
                "parameters": {"paths": ["/tmp", "/var/tmp"], "keep_days": 7},
                "reasoning": "Disk is full - cleaning up old temp files"
            },
            {
                "name": "out_of_memory",
                "pattern": re.compile(r"(?i)(out\s+of\s+memory|OOM|memory\s+exhausted|cannot\s+allocate)", re.IGNORECASE),
                "action": "restart_service",
                "parameters": {"service_name": "app", "grace_period": 5},
                "reasoning": "Memory exhausted - restarting service to free memory"
            },
            {
                "name": "connection_refused",
                "pattern": re.compile(r"(?i)(connection\s+refused|failed\s+to\s+connect|ECONNREFUSED)", re.IGNORECASE),
                "action": "restart_service",
                "parameters": {"service_name": "app", "grace_period": 5},
                "reasoning": "Connection refused - service may be unresponsive, restarting"
            },
            {
                "name": "database_connection",
                "pattern": re.compile(r"(?i)(too\s+many\s+connections|max\s+connections|connection\s+pool)", re.IGNORECASE),
                "action": "restart_service",
                "parameters": {"service_name": "database", "grace_period": 10},
                "reasoning": "Database connection issues - restarting database service"
            },
            {
                "name": "cache_full",
                "pattern": re.compile(r"(?i)(cache\s+full|cache\s+exceeded|cache\s+overflow)", re.IGNORECASE),
                "action": "cleanup_cache",
                "parameters": {"cache_paths": ["/var/cache", "/tmp/cache"]},
                "reasoning": "Cache is full - clearing cache directories"
            },
        ]
    
    async def analyze_and_plan(self, error_message: str, context: Optional[str] = None) -> Optional[ActionPlan]:
        """Analyze error and generate action plan"""
        full_text = f"{error_message} {context or ''}"
        
        # Try to match against rules
        for rule in self.rules:
            if rule["pattern"].search(full_text):
                logger.info(f"Matched rule: {rule['name']}")
                return ActionPlan(
                    action_type=rule["action"],
                    parameters=rule["parameters"],
                    confidence=0.9,
                    reasoning=rule["reasoning"]
                )
        
        logger.info("No matching rule found")
        return None
