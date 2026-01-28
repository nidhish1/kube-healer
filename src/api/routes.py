"""API routes"""
import json
import os
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from datetime import datetime

from ..knowledge.database import DatabaseManager, Rule, SuggestedRule
from ..knowledge.repository import IncidentRepository, ActionLogRepository, RuleRepository, SuggestedRuleRepository
from ..executors.manager import ExecutorManager
from ..discovery.service_discovery import ServiceDiscovery
from ..analyzer.gemini_client import GeminiClient
from ..analyzer.ai_rule_suggester import AIRuleSuggester
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Kube-Healer API",
    description="Self-Healing DevOps Agent",
    version="1.0.0"
)

# Global state (will be initialized in main.py)
db_manager: Optional[DatabaseManager] = None
executor_manager: Optional[ExecutorManager] = None
gemini_client: Optional[GeminiClient] = None
ai_suggester: Optional[AIRuleSuggester] = None


# Pydantic models
class ExecuteActionRequest(BaseModel):
    action_type: str
    parameters: Dict[str, Any]


class ActionResponse(BaseModel):
    success: bool
    message: str
    action_log_id: Optional[int] = None


class IncidentResponse(BaseModel):
    id: int
    timestamp: str
    source: str
    error_type: Optional[str]
    message: str
    severity: str
    resolved: bool


class StatsResponse(BaseModel):
    total_incidents: int
    resolved_incidents: int
    total_actions: int
    successful_actions: int
    uptime_hours: float


class RuleCreateRequest(BaseModel):
    name: str
    pattern: str
    action_type: str
    parameters: Optional[Dict[str, Any]] = None
    priority: int = 50
    enabled: bool = True


class RuleUpdateRequest(BaseModel):
    name: Optional[str] = None
    pattern: Optional[str] = None
    action_type: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    priority: Optional[int] = None
    enabled: Optional[bool] = None


class RuleResponse(BaseModel):
    id: int
    name: str
    pattern: str
    action_type: str
    parameters: Optional[str]
    priority: int
    enabled: bool
    created_at: str


# Routes
@app.get("/", response_class=HTMLResponse)
async def root():
    """Dashboard UI"""
    dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard.html")
    
    try:
        with open(dashboard_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        # Fallback to JSON if dashboard not found
        return HTMLResponse(content="""
            <html>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1>🛡️ Kube-Healer</h1>
                    <p>Dashboard UI not found. Visit <a href="/docs">/docs</a> for API documentation.</p>
                </body>
            </html>
        """)


@app.get("/health")
async def health_check():
    """Health check endpoint for Render.com"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/incidents", response_model=List[IncidentResponse])
async def get_incidents(hours: int = 24, limit: int = 100):
    """Get recent incidents"""
    if not db_manager:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    async with db_manager.get_session() as session:
        repo = IncidentRepository(session)
        incidents = await repo.get_recent_incidents(hours=hours, limit=limit)
        
        return [
            IncidentResponse(
                id=inc.id,
                timestamp=inc.timestamp.isoformat(),
                source=inc.source,
                error_type=inc.error_type,
                message=inc.message,
                severity=inc.severity,
                resolved=inc.resolved
            )
            for inc in incidents
        ]


@app.get("/actions")
async def get_actions(limit: int = 50):
    """Get recent action logs"""
    if not db_manager:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    async with db_manager.get_session() as session:
        repo = ActionLogRepository(session)
        actions = await repo.get_recent_actions(limit=limit)
        
        return [
            {
                "id": action.id,
                "timestamp": action.timestamp.isoformat(),
                "incident_id": action.incident_id,
                "action_type": action.action_type,
                "parameters": action.parameters,
                "success": action.success,
                "output": action.output,
                "duration_seconds": action.duration_seconds,
                "error_message": action.error_message
            }
            for action in actions
        ]


@app.post("/actions/execute", response_model=ActionResponse)
async def execute_action(request: ExecuteActionRequest):
    """Execute an action manually"""
    if not executor_manager or not db_manager:
        raise HTTPException(status_code=500, detail="System not initialized")
    
    # Execute action
    result = await executor_manager.execute_action(
        action_type=request.action_type,
        parameters=request.parameters
    )
    
    # Log to database
    async with db_manager.get_session() as session:
        repo = ActionLogRepository(session)
        action_log = await repo.create_action_log(
            action_type=request.action_type,
            parameters=json.dumps(request.parameters),
            success=result.success,
            output=result.output,
            duration_seconds=result.duration_seconds,
            error_message=result.error
        )
    
    return ActionResponse(
        success=result.success,
        message=result.message,
        action_log_id=action_log.id
    )


@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get system statistics"""
    if not db_manager:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    async with db_manager.get_session() as session:
        incident_repo = IncidentRepository(session)
        action_repo = ActionLogRepository(session)
        
        incidents = await incident_repo.get_recent_incidents(hours=24 * 7, limit=10000)
        actions = await action_repo.get_recent_actions(limit=10000)
        
        return StatsResponse(
            total_incidents=len(incidents),
            resolved_incidents=sum(1 for i in incidents if i.resolved),
            total_actions=len(actions),
            successful_actions=sum(1 for a in actions if a.success),
            uptime_hours=24.0  # Placeholder
        )


@app.get("/cooldowns")
async def get_cooldowns():
    """Get cooldown status for all actions"""
    if not executor_manager:
        raise HTTPException(status_code=500, detail="Executor manager not initialized")
    
    cooldowns = {}
    for action_type in executor_manager.cooldowns.keys():
        cooldowns[action_type] = {
            "in_cooldown": executor_manager.is_in_cooldown(action_type),
            "remaining_seconds": executor_manager.get_cooldown_remaining(action_type),
            "cooldown_seconds": executor_manager.cooldowns[action_type]
        }
    
    return cooldowns


# Rule Management Endpoints
@app.get("/rules", response_model=List[RuleResponse])
async def get_rules():
    """Get all rules"""
    if not db_manager:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    async with db_manager.get_session() as session:
        repo = RuleRepository(session)
        rules = await repo.get_all_rules()
        
        return [
            RuleResponse(
                id=rule.id,
                name=rule.name,
                pattern=rule.pattern,
                action_type=rule.action_type,
                parameters=rule.parameters,
                priority=rule.priority,
                enabled=rule.enabled,
                created_at=rule.created_at.isoformat()
            )
            for rule in rules
        ]


@app.post("/rules", response_model=RuleResponse)
async def create_rule(request: RuleCreateRequest):
    """Create a new rule"""
    if not db_manager:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    async with db_manager.get_session() as session:
        repo = RuleRepository(session)
        
        try:
            rule = await repo.create_rule(
                name=request.name,
                pattern=request.pattern,
                action_type=request.action_type,
                parameters=json.dumps(request.parameters) if request.parameters else None,
                priority=request.priority,
                enabled=request.enabled
            )
            
            return RuleResponse(
                id=rule.id,
                name=rule.name,
                pattern=rule.pattern,
                action_type=rule.action_type,
                parameters=rule.parameters,
                priority=rule.priority,
                enabled=rule.enabled,
                created_at=rule.created_at.isoformat()
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))


@app.put("/rules/{rule_id}", response_model=RuleResponse)
async def update_rule(rule_id: int, request: RuleUpdateRequest):
    """Update an existing rule"""
    if not db_manager:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    async with db_manager.get_session() as session:
        repo = RuleRepository(session)
        
        # Build update dict
        updates = {}
        if request.name is not None:
            updates['name'] = request.name
        if request.pattern is not None:
            updates['pattern'] = request.pattern
        if request.action_type is not None:
            updates['action_type'] = request.action_type
        if request.parameters is not None:
            updates['parameters'] = json.dumps(request.parameters)
        if request.priority is not None:
            updates['priority'] = request.priority
        if request.enabled is not None:
            updates['enabled'] = request.enabled
        
        rule = await repo.update_rule(rule_id, **updates)
        
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")
        
        return RuleResponse(
            id=rule.id,
            name=rule.name,
            pattern=rule.pattern,
            action_type=rule.action_type,
            parameters=rule.parameters,
            priority=rule.priority,
            enabled=rule.enabled,
            created_at=rule.created_at.isoformat()
        )


@app.delete("/rules/{rule_id}")
async def delete_rule(rule_id: int):
    """Delete a rule"""
    if not db_manager:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    async with db_manager.get_session() as session:
        repo = RuleRepository(session)
        success = await repo.delete_rule(rule_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Rule not found")
        
        return {"success": True, "message": f"Rule {rule_id} deleted"}


# Service Discovery Endpoints
@app.get("/services/discover")
async def discover_services():
    """Discover all running services"""
    discovery = ServiceDiscovery()
    services = await discovery.discover_all()
    
    return [
        {
            "name": svc.name,
            "type": svc.service_type,
            "identifier": svc.identifier,
            "status": svc.status,
            "metadata": svc.metadata
        }
        for svc in services
    ]


@app.get("/services/docker")
async def discover_docker_services():
    """Discover Docker containers only"""
    discovery = ServiceDiscovery()
    services = await discovery.discover_docker_containers()
    
    return [
        {
            "name": svc.name,
            "type": svc.service_type,
            "identifier": svc.identifier,
            "status": svc.status,
            "metadata": svc.metadata
        }
        for svc in services
    ]


# AI Suggestion Endpoints
class SuggestedRuleResponse(BaseModel):
    id: int
    pattern: str
    action_type: str
    parameters: str
    confidence: float
    reasoning: str
    example_errors: str
    status: str
    created_at: str
    reviewed_at: Optional[str]


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str


@app.get("/ai/suggestions", response_model=List[SuggestedRuleResponse])
async def get_ai_suggestions(status: Optional[str] = None):
    """Get AI rule suggestions"""
    if not db_manager:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    async with db_manager.get_session() as session:
        repo = SuggestedRuleRepository(session)
        
        if status == "pending":
            suggestions = await repo.get_pending_suggestions()
        else:
            suggestions = await repo.get_all_suggestions()
        
        return [
            SuggestedRuleResponse(
                id=s.id,
                pattern=s.pattern,
                action_type=s.action_type,
                parameters=s.parameters,
                confidence=s.confidence,
                reasoning=s.reasoning,
                example_errors=s.example_errors,
                status=s.status,
                created_at=s.created_at.isoformat(),
                reviewed_at=s.reviewed_at.isoformat() if s.reviewed_at else None
            )
            for s in suggestions
        ]


@app.post("/ai/suggestions/{suggestion_id}/approve")
async def approve_suggestion(suggestion_id: int):
    """Approve and activate an AI suggestion"""
    if not db_manager:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    async with db_manager.get_session() as session:
        suggested_repo = SuggestedRuleRepository(session)
        rule_repo = RuleRepository(session)
        
        # Get suggestion
        suggestion = await suggested_repo.get_suggestion(suggestion_id)
        if not suggestion:
            raise HTTPException(status_code=404, detail="Suggestion not found")
        
        if suggestion.status != "pending":
            raise HTTPException(status_code=400, detail="Suggestion already reviewed")
        
        # Create rule from suggestion
        try:
            params_dict = json.loads(suggestion.parameters)
            rule = await rule_repo.create_rule(
                name=f"ai_suggested_{suggestion_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                pattern=suggestion.pattern,
                action_type=suggestion.action_type,
                parameters=suggestion.parameters,
                priority=15  # AI suggestions get medium-high priority
            )
            
            # Mark suggestion as approved
            await suggested_repo.approve_suggestion(suggestion_id)
            
            return {
                "success": True,
                "message": "Rule created and activated",
                "rule_id": rule.id,
                "suggestion_id": suggestion_id
            }
        
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to create rule: {str(e)}")


@app.post("/ai/suggestions/{suggestion_id}/reject")
async def reject_suggestion(suggestion_id: int):
    """Reject an AI suggestion"""
    if not db_manager:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    async with db_manager.get_session() as session:
        repo = SuggestedRuleRepository(session)
        
        suggestion = await repo.reject_suggestion(suggestion_id)
        if not suggestion:
            raise HTTPException(status_code=404, detail="Suggestion not found")
        
        return {
            "success": True,
            "message": "Suggestion rejected",
            "suggestion_id": suggestion_id
        }


@app.post("/ai/analyze-unhandled")
async def trigger_ai_analysis():
    """Manually trigger AI analysis of unhandled errors"""
    if not ai_suggester:
        raise HTTPException(status_code=503, detail="AI suggester not available")
    
    try:
        suggestion_ids = await ai_suggester.analyze_unhandled_errors()
        
        return {
            "success": True,
            "suggestions_created": len(suggestion_ids),
            "suggestion_ids": suggestion_ids
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/ai/chat", response_model=ChatResponse)
async def chat_with_ai(request: ChatRequest):
    """Chat with AI about incidents"""
    if not gemini_client:
        raise HTTPException(status_code=503, detail="AI chat not available - no Gemini API key configured")
    
    if not db_manager:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    try:
        # Gather context
        async with db_manager.get_session() as session:
            incident_repo = IncidentRepository(session)
            action_repo = ActionLogRepository(session)
            
            # Get stats
            total_incidents = len(await incident_repo.get_recent_incidents(limit=1000))
            resolved = len([i for i in await incident_repo.get_recent_incidents(limit=1000) if i.resolved])
            actions = await action_repo.get_recent_actions(limit=100)
            successful_actions = len([a for a in actions if a.success])
            
            # Get recent incidents
            recent = await incident_repo.get_recent_incidents(limit=10)
            recent_data = [
                {
                    "timestamp": inc.timestamp.isoformat(),
                    "message": inc.message,
                    "severity": inc.severity,
                    "resolved": inc.resolved
                }
                for inc in recent
            ]
            
            context = {
                "stats": {
                    "total_incidents": total_incidents,
                    "resolved_incidents": resolved,
                    "total_actions": len(actions),
                    "successful_actions": successful_actions
                },
                "recent_incidents": recent_data
            }
        
        # Call AI
        answer = await gemini_client.chat(request.message, context)
        
        return ChatResponse(answer=answer)
    
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@app.get("/incidents/{incident_id}/root-cause")
async def analyze_root_cause(incident_id: int):
    """Get AI root cause analysis for an incident"""
    if not gemini_client:
        raise HTTPException(status_code=503, detail="AI analysis not available")
    
    if not db_manager:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    try:
        async with db_manager.get_session() as session:
            incident_repo = IncidentRepository(session)
            action_repo = ActionLogRepository(session)
            
            # Get incident
            incidents = await incident_repo.get_recent_incidents(limit=1000)
            incident = next((i for i in incidents if i.id == incident_id), None)
            
            if not incident:
                raise HTTPException(status_code=404, detail="Incident not found")
            
            # Get related actions
            actions = await action_repo.get_actions_for_incident(incident_id)
            
            # Format data
            incident_data = {
                "message": incident.message,
                "source": incident.source,
                "severity": incident.severity,
                "context": incident.context,
                "timestamp": incident.timestamp.isoformat()
            }
            
            actions_data = [
                {
                    "action_type": a.action_type,
                    "success": a.success,
                    "message": a.output if a.success else a.error_message,
                    "duration": a.duration_seconds
                }
                for a in actions
            ]
            
            # Get AI analysis
            analysis = await gemini_client.analyze_root_cause(incident_data, actions_data)
            
            return {
                "incident_id": incident_id,
                "root_cause_analysis": analysis
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Root cause analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
