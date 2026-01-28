"""Rule-based action planner (No AI needed)"""
import os
import re
import yaml
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
    
    def __init__(self, rules_config_path: Optional[str] = "config/rules.yaml"):
        self.rules = self._load_default_rules()
        
        # Load custom rules from YAML if available
        if rules_config_path and os.path.exists(rules_config_path):
            custom_rules = self._load_custom_rules(rules_config_path)
            if custom_rules:
                self.rules = custom_rules + self.rules  # Custom rules have priority
                logger.info(f"Loaded {len(custom_rules)} custom rules from {rules_config_path}")
        
        logger.info(f"Total rules loaded: {len(self.rules)}")
    
    def _load_default_rules(self) -> List[Dict[str, Any]]:
        """Load default healing rules"""
        return [
            # Disk and Storage Issues
            {
                "name": "disk_full",
                "pattern": re.compile(r"(?i)(disk\s+(full|space)|no\s+space\s+left|filesystem\s+full)", re.IGNORECASE),
                "action": "cleanup_disk",
                "parameters": {"paths": ["/tmp", "/var/tmp"], "keep_days": 7},
                "reasoning": "Disk is full - cleaning up old temp files"
            },
            {
                "name": "disk_quota_exceeded",
                "pattern": re.compile(r"(?i)(quota\s+exceeded|disk\s+quota)", re.IGNORECASE),
                "action": "cleanup_disk",
                "parameters": {"paths": ["/tmp", "/var/tmp", "/var/log"], "keep_days": 3},
                "reasoning": "Disk quota exceeded - aggressive cleanup needed"
            },
            {
                "name": "inode_exhausted",
                "pattern": re.compile(r"(?i)(no\s+space\s+left.*inode|inode.*exhausted)", re.IGNORECASE),
                "action": "cleanup_disk",
                "parameters": {"paths": ["/tmp"], "keep_days": 1, "min_file_size_mb": 0},
                "reasoning": "Inodes exhausted - removing small/old files"
            },
            
            # Memory Issues
            {
                "name": "out_of_memory",
                "pattern": re.compile(r"(?i)(out\s+of\s+memory|OOM|memory\s+exhausted|cannot\s+allocate)", re.IGNORECASE),
                "action": "restart_service",
                "parameters": {"service_name": "app", "service_type": "docker", "grace_period": 5},
                "reasoning": "Memory exhausted - restarting service to free memory"
            },
            {
                "name": "memory_leak",
                "pattern": re.compile(r"(?i)(memory\s+leak|heap\s+overflow)", re.IGNORECASE),
                "action": "restart_service",
                "parameters": {"service_name": "app", "service_type": "docker", "grace_period": 10},
                "reasoning": "Memory leak detected - restarting to reclaim memory"
            },
            
            # Connection and Network Issues
            {
                "name": "connection_refused",
                "pattern": re.compile(r"(?i)(connection\s+refused|failed\s+to\s+connect|ECONNREFUSED)", re.IGNORECASE),
                "action": "restart_service",
                "parameters": {"service_name": "app", "service_type": "docker", "grace_period": 5},
                "reasoning": "Connection refused - service may be unresponsive, restarting"
            },
            {
                "name": "connection_timeout",
                "pattern": re.compile(r"(?i)(connection\s+timeout|timed?\s+out|ETIMEDOUT)", re.IGNORECASE),
                "action": "restart_service",
                "parameters": {"service_name": "app", "service_type": "docker", "grace_period": 5},
                "reasoning": "Connection timeout - restarting unresponsive service"
            },
            {
                "name": "connection_reset",
                "pattern": re.compile(r"(?i)(connection\s+reset|ECONNRESET)", re.IGNORECASE),
                "action": "restart_service",
                "parameters": {"service_name": "app", "service_type": "docker", "grace_period": 5},
                "reasoning": "Connection reset - network issue, restarting service"
            },
            {
                "name": "port_already_in_use",
                "pattern": re.compile(r"(?i)(port.*already\s+in\s+use|address\s+already\s+in\s+use|EADDRINUSE)", re.IGNORECASE),
                "action": "restart_service",
                "parameters": {"service_name": "app", "service_type": "docker", "grace_period": 5},
                "reasoning": "Port conflict - restarting to release and rebind port"
            },
            
            # Database Issues
            {
                "name": "database_connection",
                "pattern": re.compile(r"(?i)(too\s+many\s+connections|max\s+connections|connection\s+pool)", re.IGNORECASE),
                "action": "restart_service",
                "parameters": {"service_name": "database", "service_type": "docker", "grace_period": 10},
                "reasoning": "Database connection pool exhausted - restarting database"
            },
            {
                "name": "database_deadlock",
                "pattern": re.compile(r"(?i)(deadlock|lock\s+wait\s+timeout)", re.IGNORECASE),
                "action": "restart_service",
                "parameters": {"service_name": "database", "service_type": "docker", "grace_period": 15},
                "reasoning": "Database deadlock detected - restarting to clear locks"
            },
            {
                "name": "database_connection_failed",
                "pattern": re.compile(r"(?i)(database.*connection.*failed|could\s+not\s+connect.*database)", re.IGNORECASE),
                "action": "restart_service",
                "parameters": {"service_name": "database", "service_type": "docker", "grace_period": 10},
                "reasoning": "Cannot connect to database - restarting database service"
            },
            
            # Cache Issues
            {
                "name": "cache_full",
                "pattern": re.compile(r"(?i)(cache\s+full|cache\s+exceeded|cache\s+overflow)", re.IGNORECASE),
                "action": "cleanup_cache",
                "parameters": {"cache_paths": ["/var/cache", "/tmp/cache"]},
                "reasoning": "Cache is full - clearing cache directories"
            },
            {
                "name": "redis_connection_failed",
                "pattern": re.compile(r"(?i)(redis.*connection.*failed|could\s+not\s+connect.*redis)", re.IGNORECASE),
                "action": "restart_service",
                "parameters": {"service_name": "redis", "service_type": "docker", "grace_period": 5},
                "reasoning": "Redis connection failed - restarting Redis service"
            },
            
            # SSL/TLS Issues
            {
                "name": "ssl_certificate_expired",
                "pattern": re.compile(r"(?i)(certificate.*expired|ssl.*expired)", re.IGNORECASE),
                "action": "restart_service",
                "parameters": {"service_name": "app", "service_type": "docker", "grace_period": 5},
                "reasoning": "SSL certificate expired - restarting to reload certificates"
            },
            {
                "name": "ssl_handshake_failed",
                "pattern": re.compile(r"(?i)(ssl.*handshake.*failed|tls.*handshake)", re.IGNORECASE),
                "action": "restart_service",
                "parameters": {"service_name": "app", "service_type": "docker", "grace_period": 5},
                "reasoning": "SSL handshake failed - restarting service"
            },
            
            # Permission Issues
            {
                "name": "permission_denied",
                "pattern": re.compile(r"(?i)(permission\s+denied|access\s+denied|EACCES)", re.IGNORECASE),
                "action": "restart_service",
                "parameters": {"service_name": "app", "service_type": "docker", "grace_period": 5},
                "reasoning": "Permission denied - restarting with proper permissions"
            },
            
            # Service Availability
            {
                "name": "service_unavailable",
                "pattern": re.compile(r"(?i)(service\s+unavailable|503)", re.IGNORECASE),
                "action": "restart_service",
                "parameters": {"service_name": "app", "service_type": "docker", "grace_period": 5},
                "reasoning": "Service unavailable (503) - restarting service"
            },
            {
                "name": "bad_gateway",
                "pattern": re.compile(r"(?i)(bad\s+gateway|502)", re.IGNORECASE),
                "action": "restart_service",
                "parameters": {"service_name": "app", "service_type": "docker", "grace_period": 5},
                "reasoning": "Bad gateway (502) - upstream service issue, restarting"
            },
            
            # Process Issues
            {
                "name": "segmentation_fault",
                "pattern": re.compile(r"(?i)(segmentation\s+fault|segfault|SIGSEGV)", re.IGNORECASE),
                "action": "restart_service",
                "parameters": {"service_name": "app", "service_type": "docker", "grace_period": 5},
                "reasoning": "Segmentation fault - process crashed, restarting"
            },
            {
                "name": "process_hung",
                "pattern": re.compile(r"(?i)(process.*hung|not\s+responding|unresponsive)", re.IGNORECASE),
                "action": "restart_service",
                "parameters": {"service_name": "app", "service_type": "docker", "grace_period": 3},
                "reasoning": "Process hung/unresponsive - forcing restart"
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
    
    def _load_custom_rules(self, config_path: str) -> List[Dict[str, Any]]:
        """Load custom rules from YAML configuration"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            if not config or 'rules' not in config:
                logger.warning(f"No rules found in {config_path}")
                return []
            
            custom_rules = []
            for rule_config in config['rules']:
                if not rule_config.get('enabled', True):
                    continue
                
                try:
                    custom_rule = {
                        "name": rule_config['name'],
                        "pattern": re.compile(rule_config['pattern']),
                        "action": rule_config['action'],
                        "parameters": rule_config.get('parameters', {}),
                        "reasoning": rule_config.get('reasoning', f"Matched custom rule: {rule_config['name']}"),
                        "priority": rule_config.get('priority', 50)
                    }
                    custom_rules.append(custom_rule)
                except Exception as e:
                    logger.error(f"Failed to load rule {rule_config.get('name')}: {e}")
            
            # Sort by priority (lower number = higher priority)
            custom_rules.sort(key=lambda r: r.get('priority', 50))
            
            return custom_rules
        
        except Exception as e:
            logger.error(f"Failed to load custom rules from {config_path}: {e}")
            return []
