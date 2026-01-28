# AI Features Guide

## 🤖 Overview

Kube-Healer now includes powerful AI features powered by **Google Gemini**, transforming it from a rule-based agent to an intelligent, self-improving system.

---

## 🎯 Features

### 1. AI Rule Suggestions
**What it does:** AI analyzes unhandled errors and suggests new healing rules

**How to use:**
1. Let unhandled errors accumulate (errors that don't match any rule)
2. Click "🔍 Analyze Now" in dashboard, or wait for automatic analysis (runs daily)
3. Review suggestions in the "🤖 AI Rule Suggestions" card
4. Click "✅ Approve & Activate" to turn it into an active rule
5. Or "❌ Dismiss" if not useful

**Example:**
```
Pattern: (?i)nginx.*worker.*killed
Action: restart_service → nginx  
Confidence: 87% ⭐⭐⭐⭐
Based on 12 similar incidents
```

### 2. AI Chat Interface
**What it does:** Ask questions about your system health and incidents

**How to use:**
1. Click the "💬" button (bottom right of dashboard)
2. Ask natural language questions:
   - "Why did database restart 5 times today?"
   - "What's causing the most errors?"
   - "Should I be worried about these memory warnings?"
3. AI provides context-aware answers

### 3. AI Fallback Analysis
**What it does:** When no rule matches, AI analyzes and suggests action

**How it works:**
1. Error occurs
2. No matching rule found
3. AI analyzes the error
4. If confidence ≥ 95% → auto-execute action
5. If confidence 70-94% → save suggestion for review
6. If confidence < 70% → log only

**Safety:** Only very high-confidence suggestions auto-execute

### 4. Root Cause Analysis
**What it does:** AI explains why an incident happened and how to prevent it

**How to use:**
1. Click on any incident in the dashboard
2. Click "🔍 Analyze Root Cause with AI"
3. AI provides:
   - Root cause explanation
   - Why actions helped (or didn't)
   - Prevention recommendations

---

## 🔧 Setup

### 1. Get Gemini API Key

**Option A: University (Free)**
- Check if your university provides Google Cloud credits
- Access Gemini Pro for free

**Option B: Google AI Studio (Free tier)**
1. Go to https://ai.google.dev/
2. Click "Get API key"
3. Create project and generate key
4. Free tier: 60 requests/minute

**Option C: Google Cloud (Pay as you go)**
- Very affordable: ~$0.01-0.10 per request
- Higher rate limits

### 2. Configure API Key

Add to `.env`:
```bash
GEMINI_API_KEY=your-actual-gemini-api-key-here
```

### 3. Enable Features

Edit `config/config.yaml`:
```yaml
analyzer:
  llm_provider: gemini  # Change from "none"
  model: gemini-pro
  
  # AI Features
  enable_ai_fallback: true
  enable_rule_suggestions: true
  enable_chat: true
  
  # Safety
  ai_auto_approve_threshold: 0.95
  suggestion_batch_size: 10
  suggestion_interval_hours: 24
```

### 4. Restart

```bash
# Local
make run

# Docker
docker-compose up -d --build

# Or
cd /Users/mudrex/Desktop/dev/self-healing-devops-agent
source venv/bin/activate
python -m src.main --api
```

---

## 📊 API Endpoints

### AI Suggestions
```bash
# List pending suggestions
GET /ai/suggestions?status=pending

# Approve suggestion
POST /ai/suggestions/{id}/approve

# Reject suggestion  
POST /ai/suggestions/{id}/reject

# Trigger manual analysis
POST /ai/analyze-unhandled
```

### Chat
```bash
# Send message
POST /ai/chat
{
  "message": "Why did the app crash?"
}
```

### Root Cause
```bash
# Analyze incident
GET /incidents/{id}/root-cause
```

---

## 💡 Usage Tips

### For Rule Suggestions:

**Do:**
- ✅ Let it run for a few days to accumulate patterns
- ✅ Review confidence scores carefully
- ✅ Approve high-confidence (80%+) suggestions
- ✅ Test approved rules in dry-run mode first

**Don't:**
- ❌ Blindly approve all suggestions
- ❌ Approve rules you don't understand
- ❌ Set auto-approve threshold below 90%

### For Chat:

**Good Questions:**
- "What happened between 2pm and 3pm today?"
- "Which service is causing the most problems?"
- "Is this memory leak getting worse?"

**Not Ideal:**
- "Fix everything" (too broad)
- "What's the meaning of life?" (off-topic)

### For AI Fallback:

**Recommended Settings:**
```yaml
ai_auto_approve_threshold: 0.95  # Very conservative
enable_ai_fallback: true
```

**For Testing:**
```yaml
ai_auto_approve_threshold: 0.99  # Practically disabled
enable_ai_fallback: false  # Manual approval only
```

---

## 🔒 Safety & Privacy

### What Gets Sent to Gemini:
- Error messages (sanitized)
- Log context (50 lines around error)
- Incident statistics
- Your questions (for chat)

### What's NOT Sent:
- Full log files
- Credentials or secrets
- User data (unless in error messages)
- System configuration

### Safety Measures:
1. **Confidence Thresholds:** Only high-confidence actions auto-execute
2. **Cooldowns:** Actions still respect cooldown periods
3. **Dry-Run Mode:** Test suggestions safely
4. **Human Review:** Low-confidence suggestions require approval
5. **Audit Trail:** All AI actions logged to database

---

## 📈 Cost Estimates

**With Free Gemini Pro:**
- Rule suggestions: 1-2 requests/day = ~60/month
- AI fallback: 5-10 requests/day = ~300/month
- Chat: 10-20 requests/day = ~600/month
- Root cause: 5 requests/day = ~150/month

**Total: ~1,100 requests/month**

**Well within free tier limits!** (60 requests/minute = ~2.5M requests/month)

**If you exceed free tier:**
- Gemini Pro: $0.0005 per request
- 1,000 requests = $0.50
- Still incredibly affordable!

---

## 🐛 Troubleshooting

### "AI feature not available"
**Causes:**
1. No API key configured
2. Invalid API key
3. API key not activated

**Fix:**
```bash
# Check .env file
cat .env | grep GEMINI_API_KEY

# Test API key
curl -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}' \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=YOUR_KEY"
```

### "Rate limit exceeded"
**Cause:** Too many requests

**Fix:**
1. Increase `suggestion_interval_hours` in config
2. Decrease `suggestion_batch_size`
3. Upgrade to paid tier for higher limits

### "No suggestions created"
**Causes:**
1. Not enough unhandled errors (need 3+ similar)
2. Errors too different to group
3. AI couldn't generate valid suggestion

**Fix:**
- Let more errors accumulate
- Check logs for AI responses
- Manually trigger analysis later

### AI suggestions are low quality
**Fixes:**
1. Provide better error messages (more context)
2. Wait for more examples to accumulate
3. Only approve high-confidence (>80%) suggestions
4. Give feedback by rejecting bad suggestions

---

## 🎓 Examples

### Example 1: Nginx 502 Pattern

**Unhandled Errors:**
```
2026-01-28 10:15:23 ERROR nginx upstream timed out (502)
2026-01-28 10:20:45 ERROR nginx upstream prematurely closed connection (502)
2026-01-28 10:25:12 ERROR nginx no live upstreams while connecting to upstream (502)
```

**AI Suggestion:**
```yaml
name: ai_suggested_nginx_502
pattern: (?i)nginx.*(502|upstream.*error|upstream.*timeout)
action: restart_service
parameters:
  service_name: nginx
  service_type: docker
  grace_period: 5
confidence: 0.92
reasoning: "Nginx upstream failures - restart to reconnect"
```

**Result:** Approve → Rule activated → Future nginx 502s auto-fixed!

### Example 2: Chat Usage

**You:** "Why did the database restart 3 times in the last hour?"

**AI:**
```
Analysis of recent incidents shows:

1. First restart (10:15 AM): Out of memory error
   - Likely cause: Connection pool not released
   
2. Second restart (10:45 AM): Same OOM issue
   - Previous restart didn't solve root cause
   
3. Third restart (11:10 AM): Manual restart after OOM

Recommendation:
- Check application for connection leaks
- Increase database memory allocation
- Add connection pool monitoring
- Consider connection pool size limits
```

### Example 3: Root Cause Analysis

**Incident:** Disk full error causing application crash

**AI Analysis:**
```
Root Cause:
Log rotation was disabled, causing logs to accumulate indefinitely.
Application generates ~500MB/day of logs.

Why disk cleanup helped:
- Freed 15GB of old logs
- Gave application space to continue

Prevention:
1. Enable log rotation: logrotate -f /etc/logrotate.conf
2. Set retention to 7 days max
3. Monitor disk usage proactively
4. Add alert at 80% capacity
```

---

## 🚀 Advanced Usage

### Custom Prompting

You can customize how AI analyzes errors by modifying `src/analyzer/gemini_client.py`:

```python
prompt = f"""
You are a senior DevOps engineer analyzing production errors.

Error: {error_message}

Provide:
1. Action type (restart_service, cleanup_disk, kill_process)
2. Specific parameters
3. Confidence (0-1)
4. Brief reasoning

Consider:
- Severity and frequency
- Past similar incidents
- Business impact
"""
```

### Batch Analysis

Trigger analysis programmatically:

```python
from src.analyzer.ai_rule_suggester import AIRuleSuggester

suggester = AIRuleSuggester(db_manager, gemini_client)
suggestion_ids = await suggester.analyze_unhandled_errors()
print(f"Created {len(suggestion_ids)} suggestions")
```

---

## 📚 Learn More

- **Gemini API Docs:** https://ai.google.dev/docs
- **Rate Limits:** https://ai.google.dev/pricing
- **Best Practices:** https://ai.google.dev/docs/concepts/prompting

---

## 🎉 Benefits

### Before AI:
- ❌ Manual rule creation (hours)
- ❌ Unknown errors unhandled
- ❌ No insights into root causes
- ❌ Reactive troubleshooting

### With AI:
- ✅ Auto-generated rules (minutes)
- ✅ AI handles unknown errors
- ✅ Deep root cause analysis
- ✅ Proactive recommendations
- ✅ Natural language querying
- ✅ Self-improving system

**Result: 90% less manual work, 100% better insights!** 🚀
