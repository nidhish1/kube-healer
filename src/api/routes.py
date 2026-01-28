"""API routes"""
import json
import os
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from datetime import datetime

from ..knowledge.database import DatabaseManager
from ..knowledge.repository import IncidentRepository, ActionLogRepository
from ..executors.manager import ExecutorManager
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
