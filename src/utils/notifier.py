"""Notification system for alerts"""
import requests
from typing import Optional, Dict, Any
from .logger import setup_logger

logger = setup_logger(__name__)


class Notifier:
    """Send notifications to Slack/Discord"""
    
    def __init__(self, slack_webhook: Optional[str] = None, discord_webhook: Optional[str] = None):
        self.slack_webhook = slack_webhook
        self.discord_webhook = discord_webhook
    
    async def send_notification(self, message: str, title: str = "Kube-Healer Alert", severity: str = "info"):
        """Send notification to configured channels"""
        if self.slack_webhook:
            await self._send_slack(message, title, severity)
        
        if self.discord_webhook:
            await self._send_discord(message, title, severity)
    
    async def _send_slack(self, message: str, title: str, severity: str):
        """Send to Slack"""
        try:
            emoji = {"info": ":information_source:", "warning": ":warning:", "error": ":x:", "success": ":white_check_mark:"}.get(severity, ":robot_face:")
            
            payload = {
                "text": f"{emoji} *{title}*\n{message}"
            }
            
            response = requests.post(self.slack_webhook, json=payload, timeout=10)
            response.raise_for_status()
            logger.info("Sent Slack notification")
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
    
    async def _send_discord(self, message: str, title: str, severity: str):
        """Send to Discord"""
        try:
            color = {"info": 3447003, "warning": 16776960, "error": 15158332, "success": 3066993}.get(severity, 0)
            
            payload = {
                "embeds": [{
                    "title": title,
                    "description": message,
                    "color": color
                }]
            }
            
            response = requests.post(self.discord_webhook, json=payload, timeout=10)
            response.raise_for_status()
            logger.info("Sent Discord notification")
        except Exception as e:
            logger.error(f"Failed to send Discord notification: {e}")
