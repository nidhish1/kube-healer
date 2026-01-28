"""Extract context around errors for better analysis"""
import re
from typing import List, Optional, Dict, Any
from datetime import datetime
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class ContextExtractor:
    """Extract context information from log messages and files"""
    
    def __init__(self, context_lines: int = 50):
        self.context_lines = context_lines
        self.severity_patterns = {
            "critical": re.compile(r"(?i)(critical|fatal|panic|emergency)"),
            "high": re.compile(r"(?i)(error|err|fail)"),
            "medium": re.compile(r"(?i)(warning|warn)"),
            "low": re.compile(r"(?i)(info|notice|debug)")
        }
    
    def extract_severity(self, message: str) -> str:
        """Extract severity level from log message"""
        for severity, pattern in self.severity_patterns.items():
            if pattern.search(message):
                return severity
        return "medium"
    
    def extract_timestamp(self, message: str) -> Optional[datetime]:
        """Try to extract timestamp from log message"""
        # Common log timestamp patterns
        patterns = [
            # ISO format: 2026-01-28T04:00:00.000Z
            (r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)", "%Y-%m-%dT%H:%M:%S"),
            # Standard format: 2026-01-28 04:00:00
            (r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})", "%Y-%m-%d %H:%M:%S"),
            # Syslog format: Jan 28 04:00:00
            (r"([A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})", "%b %d %H:%M:%S"),
        ]
        
        for pattern, format_str in patterns:
            match = re.search(pattern, message)
            if match:
                try:
                    timestamp_str = match.group(1)
                    # Handle ISO format with timezone
                    if 'T' in timestamp_str:
                        timestamp_str = timestamp_str.replace('Z', '+00:00')
                        return datetime.fromisoformat(timestamp_str)
                    return datetime.strptime(timestamp_str, format_str)
                except:
                    continue
        
        return None
    
    def extract_stack_trace(self, message: str) -> Optional[str]:
        """Detect if message contains a stack trace"""
        stack_indicators = [
            r"Traceback \(most recent call last\)",
            r"at\s+[\w\.]+\([^\)]+\):\d+",
            r"^\s+at\s+",
            r"^\s+File\s+\"",
            r"Exception in thread",
        ]
        
        for indicator in stack_indicators:
            if re.search(indicator, message, re.MULTILINE):
                return message  # Return full message as stack trace
        
        return None
    
    def extract_component(self, message: str, source: str) -> Optional[str]:
        """Try to identify the component/service from message or source"""
        # From source path
        if "nginx" in source.lower():
            return "nginx"
        elif "mysql" in source.lower() or "mariadb" in source.lower():
            return "mysql"
        elif "redis" in source.lower():
            return "redis"
        elif "postgres" in source.lower():
            return "postgres"
        
        # From message content
        components = ["nginx", "mysql", "redis", "postgres", "mongodb", "elasticsearch", 
                     "rabbitmq", "kafka", "docker", "kubernetes"]
        
        message_lower = message.lower()
        for comp in components:
            if comp in message_lower:
                return comp
        
        return None
    
    async def extract_context_from_file(self, file_path: str, error_line_number: int) -> str:
        """Extract context lines around error from file"""
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            # Get lines before and after
            start = max(0, error_line_number - self.context_lines)
            end = min(len(lines), error_line_number + self.context_lines)
            
            context_lines = lines[start:end]
            
            # Mark the error line
            context = []
            for i, line in enumerate(context_lines, start=start):
                marker = " >>> " if i == error_line_number else "     "
                context.append(f"{marker}{line.rstrip()}")
            
            return "\n".join(context)
        
        except Exception as e:
            logger.error(f"Failed to extract file context: {e}")
            return ""
    
    def extract_error_details(self, message: str, source: str) -> Dict[str, Any]:
        """Extract all relevant details from error"""
        details = {
            "severity": self.extract_severity(message),
            "timestamp": self.extract_timestamp(message),
            "stack_trace": self.extract_stack_trace(message),
            "component": self.extract_component(message, source),
        }
        
        # Extract error code if present
        error_code_match = re.search(r"(?i)(error|exit)\s*(?:code)?[:=\s]+(\d+)", message)
        if error_code_match:
            details["error_code"] = error_code_match.group(2)
        
        # Extract PID if present
        pid_match = re.search(r"(?i)(?:pid|process)[:=\s]+(\d+)", message)
        if pid_match:
            details["pid"] = int(pid_match.group(1))
        
        # Extract port if present
        port_match = re.search(r"(?i)port[:=\s]+(\d+)", message)
        if port_match:
            details["port"] = int(port_match.group(1))
        
        return details
