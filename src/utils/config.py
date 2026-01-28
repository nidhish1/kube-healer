"""Configuration management"""
import os
import yaml
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class WatcherConfig(BaseModel):
    """Log watcher configuration"""
    type: str = "file"
    path: str
    patterns: List[str] = Field(default_factory=list)
    enabled: bool = True


class ActionConfig(BaseModel):
    """Action configuration"""
    enabled: bool = True
    cooldown_seconds: int = 300
    max_retries: int = 3
    dry_run: bool = False


class AnalyzerConfig(BaseModel):
    """Analyzer configuration"""
    llm_provider: Optional[str] = "none"
    enable_similarity_search: bool = False
    context_lines: int = 50


class NotificationConfig(BaseModel):
    """Notification configuration"""
    enabled: bool = False
    slack_webhook: Optional[str] = None
    discord_webhook: Optional[str] = None


class AppConfig(BaseModel):
    """Main application configuration"""
    watchers: List[WatcherConfig] = Field(default_factory=list)
    actions: Dict[str, ActionConfig] = Field(default_factory=dict)
    analyzer: AnalyzerConfig = AnalyzerConfig()
    notifications: NotificationConfig = NotificationConfig()
    database_url: str = "sqlite:///data/agent.db"
    log_level: str = "INFO"


class Settings(BaseSettings):
    """Environment settings"""
    database_url: str = "sqlite:///data/agent.db"
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    slack_webhook: Optional[str] = None
    discord_webhook: Optional[str] = None
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


def load_config(config_path: str = "config/config.yaml") -> AppConfig:
    """Load configuration from YAML file"""
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config_dict = yaml.safe_load(f)
            return AppConfig(**config_dict)
    
    # Return default config
    return AppConfig(
        watchers=[
            WatcherConfig(
                type="file",
                path="/tmp/test-app.log",
                patterns=["ERROR.*", "FATAL.*", "(?i)out of memory", "(?i)disk full"]
            )
        ],
        actions={
            "service_restart": ActionConfig(cooldown_seconds=300),
            "cleanup_disk": ActionConfig(cooldown_seconds=3600),
            "kill_process": ActionConfig(cooldown_seconds=180),
            "cleanup_cache": ActionConfig(cooldown_seconds=1800),
        }
    )
