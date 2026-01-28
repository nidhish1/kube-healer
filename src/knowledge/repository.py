"""Repository pattern for database operations"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import select, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession
from .database import Incident, ActionLog, Service, Rule


class IncidentRepository:
    """Manage incidents"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_incident(self, source: str, message: str, error_type: Optional[str] = None,
                             context: Optional[str] = None, severity: str = "medium") -> Incident:
        """Create new incident"""
        incident = Incident(
            source=source,
            message=message,
            error_type=error_type,
            context=context,
            severity=severity
        )
        self.session.add(incident)
        await self.session.commit()
        await self.session.refresh(incident)
        return incident
    
    async def get_recent_incidents(self, hours: int = 24, limit: int = 100) -> List[Incident]:
        """Get recent incidents"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        result = await self.session.execute(
            select(Incident)
            .where(Incident.timestamp >= cutoff)
            .order_by(desc(Incident.timestamp))
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def mark_resolved(self, incident_id: int, action_taken: str):
        """Mark incident as resolved"""
        result = await self.session.execute(
            select(Incident).where(Incident.id == incident_id)
        )
        incident = result.scalar_one_or_none()
        if incident:
            incident.resolved = True
            incident.resolution_time = datetime.utcnow()
            incident.action_taken = action_taken
            await self.session.commit()


class ActionLogRepository:
    """Manage action logs"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_action_log(self, action_type: str, parameters: Optional[str] = None,
                               incident_id: Optional[int] = None, success: bool = False,
                               output: Optional[str] = None, duration_seconds: Optional[float] = None,
                               error_message: Optional[str] = None) -> ActionLog:
        """Create action log"""
        log = ActionLog(
            incident_id=incident_id,
            action_type=action_type,
            parameters=parameters,
            success=success,
            output=output,
            duration_seconds=duration_seconds,
            error_message=error_message
        )
        self.session.add(log)
        await self.session.commit()
        await self.session.refresh(log)
        return log
    
    async def get_recent_actions(self, limit: int = 50) -> List[ActionLog]:
        """Get recent action logs"""
        result = await self.session.execute(
            select(ActionLog)
            .order_by(desc(ActionLog.timestamp))
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_last_action_time(self, action_type: str) -> Optional[datetime]:
        """Get timestamp of last action execution"""
        result = await self.session.execute(
            select(ActionLog.timestamp)
            .where(ActionLog.action_type == action_type)
            .order_by(desc(ActionLog.timestamp))
            .limit(1)
        )
        return result.scalar_one_or_none()


class ServiceRepository:
    """Manage services"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_or_create_service(self, name: str, service_type: str, identifier: str) -> Service:
        """Get existing or create new service"""
        result = await self.session.execute(
            select(Service).where(Service.name == name)
        )
        service = result.scalar_one_or_none()
        
        if not service:
            service = Service(name=name, service_type=service_type, identifier=identifier)
            self.session.add(service)
            await self.session.commit()
            await self.session.refresh(service)
        
        return service
    
    async def record_restart(self, service_id: int):
        """Record service restart"""
        result = await self.session.execute(
            select(Service).where(Service.id == service_id)
        )
        service = result.scalar_one_or_none()
        if service:
            service.last_restart = datetime.utcnow()
            service.restart_count += 1
            await self.session.commit()


class RuleRepository:
    """Manage rules"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_enabled_rules(self) -> List[Rule]:
        """Get all enabled rules"""
        result = await self.session.execute(
            select(Rule)
            .where(Rule.enabled == True)
            .order_by(Rule.priority)
        )
        return list(result.scalars().all())
    
    async def get_all_rules(self) -> List[Rule]:
        """Get all rules"""
        result = await self.session.execute(
            select(Rule).order_by(Rule.priority)
        )
        return list(result.scalars().all())
    
    async def create_rule(self, name: str, pattern: str, action_type: str,
                         parameters: Optional[str] = None, priority: int = 50,
                         enabled: bool = True) -> Rule:
        """Create a new rule"""
        rule = Rule(
            name=name,
            pattern=pattern,
            action_type=action_type,
            parameters=parameters,
            priority=priority,
            enabled=enabled
        )
        self.session.add(rule)
        await self.session.commit()
        await self.session.refresh(rule)
        return rule
    
    async def update_rule(self, rule_id: int, **kwargs) -> Optional[Rule]:
        """Update an existing rule"""
        result = await self.session.execute(
            select(Rule).where(Rule.id == rule_id)
        )
        rule = result.scalar_one_or_none()
        
        if not rule:
            return None
        
        for key, value in kwargs.items():
            if hasattr(rule, key):
                setattr(rule, key, value)
        
        await self.session.commit()
        await self.session.refresh(rule)
        return rule
    
    async def delete_rule(self, rule_id: int) -> bool:
        """Delete a rule"""
        result = await self.session.execute(
            select(Rule).where(Rule.id == rule_id)
        )
        rule = result.scalar_one_or_none()
        
        if not rule:
            return False
        
        await self.session.delete(rule)
        await self.session.commit()
        return True


class SuggestedRuleRepository:
    """Manage AI-suggested rules"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_suggestion(self, pattern: str, action_type: str, parameters: str,
                               confidence: float, reasoning: str, example_errors: str) -> SuggestedRule:
        """Create a new rule suggestion"""
        suggestion = SuggestedRule(
            pattern=pattern,
            action_type=action_type,
            parameters=parameters,
            confidence=confidence,
            reasoning=reasoning,
            example_errors=example_errors,
            status="pending"
        )
        self.session.add(suggestion)
        await self.session.commit()
        await self.session.refresh(suggestion)
        return suggestion
    
    async def get_pending_suggestions(self) -> List[SuggestedRule]:
        """Get all pending suggestions"""
        result = await self.session.execute(
            select(SuggestedRule)
            .where(SuggestedRule.status == "pending")
            .order_by(SuggestedRule.confidence.desc(), SuggestedRule.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_all_suggestions(self) -> List[SuggestedRule]:
        """Get all suggestions"""
        result = await self.session.execute(
            select(SuggestedRule).order_by(SuggestedRule.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_suggestion(self, suggestion_id: int) -> Optional[SuggestedRule]:
        """Get a specific suggestion"""
        result = await self.session.execute(
            select(SuggestedRule).where(SuggestedRule.id == suggestion_id)
        )
        return result.scalar_one_or_none()
    
    async def approve_suggestion(self, suggestion_id: int) -> Optional[SuggestedRule]:
        """Approve a suggestion and mark it as reviewed"""
        suggestion = await self.get_suggestion(suggestion_id)
        if not suggestion:
            return None
        
        suggestion.status = "approved"
        suggestion.reviewed_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(suggestion)
        return suggestion
    
    async def reject_suggestion(self, suggestion_id: int) -> Optional[SuggestedRule]:
        """Reject a suggestion"""
        suggestion = await self.get_suggestion(suggestion_id)
        if not suggestion:
            return None
        
        suggestion.status = "rejected"
        suggestion.reviewed_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(suggestion)
        return suggestion
    
    async def delete_suggestion(self, suggestion_id: int) -> bool:
        """Delete a suggestion"""
        suggestion = await self.get_suggestion(suggestion_id)
        if not suggestion:
            return False
        
        await self.session.delete(suggestion)
        await self.session.commit()
        return True
