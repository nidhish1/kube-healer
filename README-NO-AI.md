# Running Without AI (Completely Free!)

The agent now works **without requiring any AI API keys**! It uses a rule-based system instead.

## 🎯 How It Works

Instead of using AI to analyze errors, the agent uses **predefined rules**:

```
Error Pattern → Matches Rule → Executes Action
```

## 📋 Built-in Rules

The agent automatically handles these errors:

| Error Pattern | Action | Confidence |
|---------------|--------|------------|
| "disk full", "no space left" | Cleanup /tmp, /var/cache | 90% |
| "out of memory", "OOM" | Restart service | 85% |
| "connection refused" | Restart service | 80% |
| "too many connections" | Restart database service | 85% |
| "cache full" | Clear cache | 75% |

## 🚀 Quick Start

### 1. Start the Agent
```bash
docker-compose up -d
```

### 2. Watch Logs
Open Dozzle: http://localhost:9999

### 3. Test It!
```bash
# Copy test script into container
docker cp test-agent.sh self-healing-agent:/tmp/

# Run tests
docker exec -it self-healing-agent bash -c "cd /tmp && ./test-agent.sh"
```

Or manually trigger errors:
```bash
docker exec self-healing-agent bash -c 'echo "$(date) ERROR: No space left on device" >> /tmp/test-app.log'
```

## 📊 What You'll See

In Dozzle (http://localhost:9999):
```
🔍 Analyzing with rule-based planner...
📋 Suggested: cleanup_disk
   Confidence: 90%
   Reasoning: Rule-based: Disk space exhausted, cleaning temporary files
⚡ Auto-executing action...
✅ Action completed successfully
```

## 🎨 Customizing Rules

Want to add your own rules? Edit `src/analyzer/rule_based_planner.py`:

```python
{
    "name": "my_custom_rule",
    "patterns": [
        r"(?i)my error pattern",
        r"(?i)another pattern",
    ],
    "action_type": "restart_service",
    "parameters": {"wait_seconds": 10},
    "confidence": 0.8,
    "severity": "high",
    "reasoning": "My custom error detected",
}
```

## ✅ Advantages

- ✅ **Completely free** - No API costs
- ✅ **Fast** - No API latency
- ✅ **Private** - No data leaves your system
- ✅ **Predictable** - Same input = same action
- ✅ **Simple** - Easy to understand and debug

## ⚠️ Limitations

- ❌ Can't understand new error types automatically
- ❌ Can't provide intelligent reasoning
- ❌ Requires manual rule creation for new patterns
- ❌ Less flexible than AI-based analysis

## 🔄 Switching Back to AI

If you get an API key later:

1. Edit `src/agent.py`
2. Uncomment the LLM client initialization
3. Add your API key to `.env`
4. Rebuild: `docker-compose build`

## 🎯 This is Perfect For:

- **Learning** how self-healing agents work
- **Development** and testing
- **Small projects** with predictable errors
- **Cost-conscious** deployments
- **Air-gapped** environments

## 📈 Success Metrics

The agent still tracks:
- Incidents detected
- Actions executed
- Success rates
- Response times

Check via API: http://localhost:8000/stats

## 🆘 Troubleshooting

**Agent not detecting errors?**
- Check log file exists: `docker exec self-healing-agent ls -la /tmp/test-app.log`
- Check patterns match: Look at `config/config.yaml`

**Actions not executing?**
- Check dry-run mode: `config/config.yaml` → `dry_run: false`
- Check cooldown hasn't activated yet

**Need help?**
- View agent logs: `docker-compose logs -f agent`
- Check Dozzle: http://localhost:9999
- View API docs: http://localhost:8000/docs
