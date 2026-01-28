"""AI-powered rule suggestion system"""
import asyncio
import json
from typing import List, Optional
from datetime import datetime, timedelta
from ..knowledge.database import DatabaseManager
from ..knowledge.repository import IncidentRepository, SuggestedRuleRepository
from ..analyzer.gemini_client import GeminiClient
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class AIRuleSuggester:
    """Analyzes unhandled incidents and suggests new rules"""
    
    def __init__(self, db_manager: DatabaseManager, gemini_client: Optional[GeminiClient] = None,
                 batch_size: int = 10, check_interval_hours: int = 24):
        self.db_manager = db_manager
        self.gemini_client = gemini_client
        self.batch_size = batch_size
        self.check_interval_hours = check_interval_hours
        self.last_check = None
    
    async def analyze_unhandled_errors(self) -> List[int]:
        """Analyze unhandled errors and create rule suggestions"""
        if not self.gemini_client:
            logger.info("AI rule suggester disabled - no Gemini client")
            return []
        
        # Get unhandled incidents (not resolved, no matching rule)
        async with self.db_manager.get_session() as session:
            incident_repo = IncidentRepository(session)
            
            # Get recent unresolved incidents
            incidents = await incident_repo.get_unresolved_incidents(limit=100)
            
            if len(incidents) < self.batch_size:
                logger.info(f"Only {len(incidents)} unhandled incidents, need {self.batch_size} for batch analysis")
                return []
            
            logger.info(f"Found {len(incidents)} unhandled incidents, analyzing...")
            
            # Group similar errors
            error_groups = self._group_similar_errors(incidents)
            
            suggestion_ids = []
            for group in error_groups:
                if len(group) >= 3:  # Need at least 3 similar errors
                    suggestion_id = await self._suggest_rule_for_group(group)
                    if suggestion_id:
                        suggestion_ids.append(suggestion_id)
            
            logger.info(f"Created {len(suggestion_ids)} rule suggestions")
            return suggestion_ids
    
    async def analyze_specific_errors(self, error_messages: List[str]) -> Optional[int]:
        """Analyze specific errors and suggest a rule (for manual triggering)"""
        if not self.gemini_client:
            return None
        
        if len(error_messages) < 1:
            return None
        
        try:
            # Get AI suggestion
            suggestion = await self.gemini_client.suggest_rule_from_errors(error_messages)
            
            if not suggestion:
                logger.warning("AI did not provide a valid suggestion")
                return None
            
            # Store suggestion
            async with self.db_manager.get_session() as session:
                suggested_repo = SuggestedRuleRepository(session)
                
                db_suggestion = await suggested_repo.create_suggestion(
                    pattern=suggestion.pattern,
                    action_type=suggestion.action_type,
                    parameters=json.dumps(suggestion.parameters),
                    confidence=suggestion.confidence,
                    reasoning=suggestion.reasoning,
                    example_errors=json.dumps(suggestion.example_errors)
                )
                
                logger.info(f"Created rule suggestion: {db_suggestion.id} (confidence: {suggestion.confidence:.2f})")
                return db_suggestion.id
        
        except Exception as e:
            logger.error(f"Failed to analyze errors: {e}")
            return None
    
    async def should_run_automatic_analysis(self) -> bool:
        """Check if it's time to run automatic analysis"""
        if self.last_check is None:
            return True
        
        time_since_last = datetime.utcnow() - self.last_check
        return time_since_last.total_seconds() >= self.check_interval_hours * 3600
    
    async def run_automatic_analysis(self):
        """Run automatic analysis if conditions are met"""
        if not await self.should_run_automatic_analysis():
            return []
        
        logger.info("Running automatic AI rule suggestion analysis...")
        self.last_check = datetime.utcnow()
        
        return await self.analyze_unhandled_errors()
    
    def _group_similar_errors(self, incidents: List) -> List[List]:
        """Group similar error messages together"""
        # Simple grouping by error keywords
        groups = {}
        
        for incident in incidents:
            message = incident.message.lower()
            
            # Extract key words (simple approach)
            key_words = []
            error_keywords = ['error', 'failed', 'exception', 'timeout', 'refused', 
                            'memory', 'disk', 'connection', 'oom', 'killed']
            
            for keyword in error_keywords:
                if keyword in message:
                    key_words.append(keyword)
            
            # Create group key
            if key_words:
                group_key = '_'.join(sorted(key_words[:3]))  # Use top 3 keywords
            else:
                # Use first 30 characters as fallback
                group_key = message[:30]
            
            if group_key not in groups:
                groups[group_key] = []
            
            groups[group_key].append(incident)
        
        # Return groups with at least 3 similar incidents
        return [group for group in groups.values() if len(group) >= 3]
    
    async def _suggest_rule_for_group(self, incidents: List) -> Optional[int]:
        """Create a rule suggestion for a group of similar incidents"""
        try:
            # Extract error messages
            error_messages = [inc.message for inc in incidents[:10]]  # Max 10 examples
            
            # Get AI suggestion
            suggestion = await self.gemini_client.suggest_rule_from_errors(error_messages)
            
            if not suggestion:
                return None
            
            # Store suggestion
            async with self.db_manager.get_session() as session:
                suggested_repo = SuggestedRuleRepository(session)
                
                db_suggestion = await suggested_repo.create_suggestion(
                    pattern=suggestion.pattern,
                    action_type=suggestion.action_type,
                    parameters=json.dumps(suggestion.parameters),
                    confidence=suggestion.confidence,
                    reasoning=suggestion.reasoning,
                    example_errors=json.dumps(suggestion.example_errors)
                )
                
                return db_suggestion.id
        
        except Exception as e:
            logger.error(f"Failed to create suggestion for group: {e}")
            return None
