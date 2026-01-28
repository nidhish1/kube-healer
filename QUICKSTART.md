# Quick Start Guide

Get up and running in 3 minutes!

## Option 1: Using Make (Recommended)

### First Time Setup
```bash
# Complete setup in one command
make quick-start

# Or step by step:
make setup        # Create .env, directories
make install      # Install dependencies
make init-db      # Initialize database
```

### Edit Configuration
```bash
# Add your API key
nano .env
# Set OPENAI_API_KEY=sk-your-key-here
```

### Run the Agent
```bash
# Run with API dashboard
make run-api

# Or just monitoring mode
make run

# Or dry-run mode (safe testing)
make run-dry
```

### Access the Dashboard
- API: http://localhost:8000
- Docs: http://localhost:8000/docs

---

## Option 2: Using Docker (Even Easier!)

```bash
# Complete Docker setup
make docker-quick-start

# Or manually:
make setup              # Create .env
# Edit .env and add API key
make docker-build       # Build images
make docker-up          # Start services
```

### Access Services
- **Agent API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Log Viewer**: http://localhost:9999

### View Logs
```bash
make docker-logs        # All services
make docker-logs-agent  # Agent only
# Or visit http://localhost:9999 for web UI
```

---

## Common Commands

### Running
```bash
make run              # Start agent
make run-api          # Start with API
make run-dry          # Dry-run mode
```

### Docker
```bash
make docker-up        # Start services
make docker-down      # Stop services
make docker-logs      # View logs
make docker-restart   # Restart
```

### Development
```bash
make format           # Format code
make lint             # Lint code
make test             # Run tests
make logs             # View logs
```

### Database
```bash
make init-db          # Initialize
make db-backup        # Backup
make db-shell         # Open SQLite
```

### Utilities
```bash
make clean            # Clean temp files
make help             # Show all commands
make stats            # Show statistics
make health           # Check health
```

---

## Configuration

### 1. Set API Key
Edit `.env`:
```bash
OPENAI_API_KEY=sk-your-key-here
# OR
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### 2. Configure Log Sources
Edit `config/config.yaml`:
```yaml
watchers:
  - type: file
    path: /var/log/app.log
    patterns:
      - "ERROR.*"
      - "Exception.*"
```

### 3. Set Up Alerts (Optional)
Add webhooks to `.env`:
```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

---

## Testing It Works

### Generate Test Logs
```bash
# Create a test log file
echo "ERROR: Test error message" >> /tmp/test-app.log
echo "FATAL: Critical failure" >> /tmp/test-app.log
```

### Watch the Agent
The agent will:
1. Detect the error ✅
2. Analyze with AI 🤖
3. Suggest/execute fix ⚡
4. Send notification 📢
5. Log to database 💾

---

## Troubleshooting

### API Key Not Set
```bash
# Check .env file
cat .env | grep API_KEY
```

### Database Not Initialized
```bash
make init-db
```

### Logs Not Found
```bash
# Check log paths
ls -la logs/
make logs-clear  # Clear if needed
```

### Port Already in Use
```bash
# Change port in .env
API_PORT=8001
```

---

## Next Steps

1. ✅ Set up API key
2. ✅ Configure log sources
3. ✅ Run `make run-api`
4. 📖 Read full docs in `README.md`
5. 🐳 Deploy with Docker: `DOCKER.md`

**Need help?** Run `make help` to see all available commands!
