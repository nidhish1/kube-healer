"""Main self-healing agent"""
import asyncio
import json
from typing import Optional
from datetime import datetime

from .watchers.manager import WatcherManager
from .watchers.base import LogEvent
from .analyzer.rule_based_planner import RuleBasedPlanner
from .analyzer.context_extractor import ContextExtractor
from .analyzer.gemini_client import GeminiClient
from .analyzer.ai_rule_suggester import AIRuleSuggester
from .executors.manager import ExecutorManager
from .knowledge.database import DatabaseManager
from .knowledge.repository import IncidentRepository, ActionLogRepository, SuggestedRuleRepository
from .utils.config import load_config, AppConfig
from .utils.notifier import Notifier
from .utils.logger import setup_logger
from .analyzer.rule_based_planner import ActionPlan
import os
import json

logger = setup_logger(__name__)


class SelfHealingAgent:
    """Main self-healing agent orchestrator"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        logger.info("🤖 Initializing Self-Healing Agent...")
        
        # Load configuration
        self.config = load_config(config_path)
        
        # Initialize components
        self.db_manager = DatabaseManager(self.config.database_url)
        self.planner = RuleBasedPlanner()
        self.context_extractor = ContextExtractor(context_lines=self.config.analyzer.context_lines)
        
        # Initialize AI components if API key is available
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        self.gemini_client = None
        self.ai_suggester = None
        
        if gemini_api_key and gemini_api_key != 'your-gemini-api-key-here':
            try:
                self.gemini_client = GeminiClient(api_key=gemini_api_key)
                self.ai_suggester = AIRuleSuggester(
                    db_manager=self.db_manager,
                    gemini_client=self.gemini_client
                )
                logger.info("✨ AI features enabled with Gemini")
            except Exception as e:
                logger.warning(f"AI features disabled: {e}")
        else:
            logger.info("AI features disabled - no Gemini API key configured")
        
        self.executor_manager = ExecutorManager(dry_run=self.config.actions.get("global", {}).get("dry_run", False))
        self.notifier = Notifier(
            slack_webhook=self.config.notifications.slack_webhook if self.config.notifications.enabled else None,
            discord_webhook=self.config.notifications.discord_webhook if self.config.notifications.enabled else None
        )
        self.watcher_manager = WatcherManager(callback=self.handle_log_event)
        
        # Setup cooldowns
        for action_type, action_config in self.config.actions.items():
            if action_type != "global":
                self.executor_manager.set_cooldown(action_type, action_config.cooldown_seconds)
        
        # Add watchers from config
        for watcher_config in self.config.watchers:
            self.watcher_manager.add_watcher_from_config(watcher_config)
        
        logger.info("✅ Agent initialized successfully")
    
    async def start(self):
        """Start the agent"""
        logger.info("🚀 Starting Self-Healing Agent...")
        
        # Initialize database
        await self.db_manager.init_db()
        logger.info("✅ Database initialized")
        
        # Start watchers
        await self.watcher_manager.start_all()
        logger.info("✅ Watchers started")
        
        logger.info("🛡️  Self-Healing Agent is now active and monitoring...")
    
    async def stop(self):
        """Stop the agent"""
        logger.info("🛑 Stopping Self-Healing Agent...")
        await self.watcher_manager.stop_all()
        logger.info("✅ Agent stopped")
    
    async def handle_log_event(self, event: LogEvent):
        """Handle detected log event"""
        logger.info(f"📋 Detected event from {event.source}: {event.message[:100]}")
        
        try:
            # Extract context and details
            error_details = self.context_extractor.extract_error_details(event.message, event.source)
            severity = error_details.get("severity", "medium")
            component = error_details.get("component")
            
            # Build context string
            context_parts = []
            if error_details.get("error_code"):
                context_parts.append(f"Error Code: {error_details['error_code']}")
            if error_details.get("pid"):
                context_parts.append(f"PID: {error_details['pid']}")
            if error_details.get("port"):
                context_parts.append(f"Port: {error_details['port']}")
            if component:
                context_parts.append(f"Component: {component}")
            
            context = " | ".join(context_parts) if context_parts else None
            
            # Store incident with extracted details
            async with self.db_manager.get_session() as session:
                incident_repo = IncidentRepository(session)
                incident = await incident_repo.create_incident(
                    source=event.source,
                    message=event.message,
                    error_type=event.matched_pattern,
                    context=context,
                    severity=severity
                )
                incident_id = incident.id
            
            # Analyze and plan
            logger.info("🔍 Analyzing with rule-based planner...")
            plan = await self.planner.analyze_and_plan(event.message)
            
            if not plan:
                logger.info("ℹ️  No action plan generated")
                return
            
            logger.info(f"📝 Action plan: {plan.action_type} - {plan.reasoning}")
            
            # Execute action
            logger.info(f"⚡ Executing action: {plan.action_type}")
            result = await self.executor_manager.execute_action(
                action_type=plan.action_type,
                parameters=plan.parameters
            )
            
            # Log action
            async with self.db_manager.get_session() as session:
                action_repo = ActionLogRepository(session)
                await action_repo.create_action_log(
                    action_type=plan.action_type,
                    parameters=json.dumps(plan.parameters),
                    incident_id=incident_id,
                    success=result.success,
                    output=result.output,
                    duration_seconds=result.duration_seconds,
                    error_message=result.error
                )
            
            # Update incident
            if result.success:
                async with self.db_manager.get_session() as session:
                    incident_repo = IncidentRepository(session)
                    await incident_repo.mark_resolved(incident_id, plan.action_type)
                logger.info(f"✅ Action completed: {result.message}")
            else:
                logger.error(f"❌ Action failed: {result.message}")
            
            # Send notification
            if self.config.notifications.enabled:
                severity = "success" if result.success else "error"
                await self.notifier.send_notification(
                    title="Auto-Healing Action",
                    message=f"Action: {plan.action_type}\nResult: {result.message}",
                    severity=severity
                )
        
        except Exception as e:
            logger.error(f"❌ Error handling log event: {e}", exc_info=True)
