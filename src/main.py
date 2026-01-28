"""Main entry point"""
import asyncio
import argparse
import uvicorn
from .agent import SelfHealingAgent
from .api import routes
from .utils.logger import setup_logger

logger = setup_logger(__name__)


async def run_agent_only(config_path: str = "config/config.yaml"):
    """Run agent without API"""
    agent = SelfHealingAgent(config_path=config_path)
    
    try:
        await agent.start()
        
        # Keep running
        while True:
            await asyncio.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        await agent.stop()


async def run_with_api(config_path: str = "config/config.yaml", host: str = "0.0.0.0", port: int = 8000):
    """Run agent with API server"""
    # Initialize agent
    agent = SelfHealingAgent(config_path=config_path)
    await agent.start()
    
    # Set global state for API
    routes.db_manager = agent.db_manager
    routes.executor_manager = agent.executor_manager
    routes.gemini_client = agent.gemini_client
    routes.ai_suggester = agent.ai_suggester
    
    # Run API server
    logger.info(f"🌐 Starting API server on {host}:{port}")
    config = uvicorn.Config(
        routes.app,
        host=host,
        port=port,
        log_level="info"
    )
    server = uvicorn.Server(config)
    
    try:
        await server.serve()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        await agent.stop()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Kube-Healer: Self-Healing DevOps Agent")
    parser.add_argument("--config", default="config/config.yaml", help="Path to config file")
    parser.add_argument("--api", action="store_true", help="Enable API server")
    parser.add_argument("--host", default="0.0.0.0", help="API host")
    parser.add_argument("--port", type=int, default=8000, help="API port")
    parser.add_argument("--init-db", action="store_true", help="Initialize database and exit")
    
    args = parser.parse_args()
    
    if args.init_db:
        # Just initialize database and exit
        from .knowledge.database import DatabaseManager
        from .utils.config import load_config
        
        config = load_config(args.config)
        db_manager = DatabaseManager(config.database_url)
        asyncio.run(db_manager.init_db())
        logger.info("✅ Database initialized")
        return
    
    # Run agent
    if args.api:
        asyncio.run(run_with_api(args.config, args.host, args.port))
    else:
        asyncio.run(run_agent_only(args.config))


if __name__ == "__main__":
    main()
