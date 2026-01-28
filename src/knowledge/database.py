"""Database models and connection management"""
from datetime import datetime
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

Base = declarative_base()


class Incident(Base):
    """Incident/error record"""
    __tablename__ = "incidents"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    source = Column(String(255), nullable=False)
    error_type = Column(String(100))
    message = Column(Text, nullable=False)
    context = Column(Text)
    severity = Column(String(20), default="medium")
    resolved = Column(Boolean, default=False)
    resolution_time = Column(DateTime)
    action_taken = Column(String(100))


class ActionLog(Base):
    """Action execution log"""
    __tablename__ = "action_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    incident_id = Column(Integer)
    action_type = Column(String(100), nullable=False)
    parameters = Column(Text)
    success = Column(Boolean, default=False)
    output = Column(Text)
    duration_seconds = Column(Float)
    error_message = Column(Text)


class Service(Base):
    """Service registry"""
    __tablename__ = "services"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)
    service_type = Column(String(50))  # systemd, docker, process, k8s
    identifier = Column(String(255))  # container_id, service_name, pid, etc
    last_restart = Column(DateTime)
    restart_count = Column(Integer, default=0)
    enabled = Column(Boolean, default=True)


class Rule(Base):
    """Custom healing rules"""
    __tablename__ = "rules"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)
    pattern = Column(String(500), nullable=False)
    action_type = Column(String(100), nullable=False)
    parameters = Column(Text)
    priority = Column(Integer, default=10)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class DatabaseManager:
    """Manage database connections"""
    
    def __init__(self, database_url: str = "sqlite:///data/agent.db"):
        # Convert sqlite:/// to sqlite+aiosqlite:/// for async
        if database_url.startswith("sqlite:///"):
            async_url = database_url.replace("sqlite:///", "sqlite+aiosqlite:///")
        else:
            async_url = database_url
        
        self.engine = create_async_engine(async_url, echo=False)
        self.async_session = async_sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
    
    async def init_db(self):
        """Initialize database tables"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    def get_session(self) -> AsyncSession:
        """Get async database session"""
        return self.async_session()
