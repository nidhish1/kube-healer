# Docker Deployment Guide

## Quick Start

### 1. Setup Environment
```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your API keys
nano .env
```

### 2. Build and Run
```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f agent
```

### 3. Access Services
- **Agent API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Log Viewer**: http://localhost:9999

---

## Services Included

### 1. **agent** (Main Service)
- The self-healing agent with API
- Monitors logs and executes fixes
- **Ports**: 8000 (API)
- **Volumes**:
  - `./config` - Configuration files
  - `./data` - Database storage
  - `./logs` - Application logs
  - `/var/log` - Host system logs (read-only)

### 2. **redis** (Optional)
- Event queue for scaling
- **Ports**: 6379
- Not required for basic usage

### 3. **log-viewer** (Dozzle)
- Web UI for viewing Docker container logs
- **Ports**: 9999
- Access at: http://localhost:9999

---

## Viewing Logs

### All Logs Together
```bash
docker-compose logs -f
```

### Specific Component
```bash
# Agent only
docker-compose logs -f agent

# Redis only
docker-compose logs -f redis
```

### Using Log Viewer
Open http://localhost:9999 in your browser to see:
- Live log streaming from all containers
- Search and filter capabilities
- Multi-container view

### Application Logs
```bash
# View agent application logs (from volume)
tail -f logs/agent.log

# Inside container
docker exec -it self-healing-agent tail -f /app/logs/agent.log
```

---

## Management Commands

### Start/Stop
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart specific service
docker-compose restart agent
```

### View Status
```bash
# Check running services
docker-compose ps

# Health check
curl http://localhost:8000/health
```

### Access Container Shell
```bash
# Enter agent container
docker exec -it self-healing-agent bash

# Run commands inside container
docker exec self-healing-agent python -m src.main --init-db
```

---

## Configuration

### Mount Host Logs
Edit `docker-compose.yml` to monitor specific host logs:
```yaml
volumes:
  - /var/log/myapp:/host/logs/myapp:ro
  - /var/log/nginx:/host/logs/nginx:ro
```

Then update `config/config.yaml`:
```yaml
watchers:
  - type: file
    path: /host/logs/myapp/app.log
    patterns:
      - "ERROR.*"
```

### Environment Variables
All settings can be overridden via `.env` file:
- `OPENAI_API_KEY` - Your OpenAI API key
- `DRY_RUN=true` - Run in dry-run mode
- `LOG_LEVEL=DEBUG` - Set log verbosity

---

## Production Deployment

### Using Docker
```bash
# Production mode
docker-compose -f docker-compose.yml up -d

# With resource limits
docker-compose up -d --scale agent=1 --memory=1g --cpus=2
```

### Using Docker Swarm
```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml agent-stack

# Check services
docker service ls
```

### Using Kubernetes
```bash
# Generate K8s manifests
kompose convert -f docker-compose.yml

# Deploy
kubectl apply -f .
```

---

## Monitoring

### Health Checks
```bash
# Check agent health
curl http://localhost:8000/health

# Get statistics
curl http://localhost:8000/stats
```

### Container Metrics
```bash
# CPU and memory usage
docker stats self-healing-agent

# Detailed inspection
docker inspect self-healing-agent
```

---

## Troubleshooting

### Agent Not Starting
```bash
# Check logs
docker-compose logs agent

# Verify API key is set
docker exec self-healing-agent env | grep API_KEY

# Check database
docker exec self-healing-agent ls -la /app/data/
```

### Permission Issues
```bash
# Fix volume permissions
sudo chown -R 1000:1000 data logs

# Or run with current user
docker-compose run --user $(id -u):$(id -g) agent
```

### API Not Accessible
```bash
# Check if port is exposed
docker port self-healing-agent

# Test from inside container
docker exec self-healing-agent curl localhost:8000/health
```

---

## Cleanup

```bash
# Stop and remove containers
docker-compose down

# Remove volumes (WARNING: deletes data)
docker-compose down -v

# Remove images
docker-compose down --rmi all
```
