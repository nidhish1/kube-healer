# Testing AI Features - Quick Guide

## 🎯 Your Dashboard is Ready!

**Open:** http://127.0.0.1:8000

---

## 🧪 What You'll See (Without Gemini Key)

### 1. AI Suggestions Card
- Will show: "AI feature not available - Configure GEMINI_API_KEY"
- **This is expected!** AI needs your university Gemini key

### 2. Chat Button (💬)
- Visible in bottom right
- Click it → Chat panel opens
- Try sending a message → Will get error about missing API key
- **This is expected!**

### 3. Enhanced Dashboard
- Beautiful UI with charts
- Incidents and actions tables
- Cooldown management
- Quick action buttons
- All these work WITHOUT AI!

---

## ✅ What DOES Work Right Now (No Key Needed)

All these features are functional **without any API key**:

### 1. Rule-Based Healing (21 rules!)
```bash
# Test disk full detection
python -c "import sys; sys.path.insert(0, 'src'); from watchers.base import LogEvent; from datetime import datetime; print('Testing...')"
```

### 2. Manual Actions
Click these buttons in dashboard:
- 🧹 Cleanup Disk
- 🔄 Restart Service  
- 💾 Clear Cache

### 3. View Data
- See incidents
- See actions
- See cooldowns
- View stats

---

## 🔑 To Enable AI Features

### Step 1: Get Gemini API Key

**Free Option (Recommended):**
1. Go to https://ai.google.dev/
2. Click "Get API key in Google AI Studio"
3. Sign in with your university Google account
4. Click "Create API key"
5. Copy the key (starts with `AIza...`)

### Step 2: Add to .env

```bash
cd /Users/mudrex/Desktop/dev/self-healing-devops-agent
echo "GEMINI_API_KEY=AIza..." >> .env
```

(Replace `AIza...` with your actual key)

### Step 3: Restart Server

```bash
# Stop current server (Ctrl+C in terminal where it's running)
# Or:
lsof -ti:8000 | xargs kill -9

# Restart
source venv/bin/activate
python -m src.main --api --host 127.0.0.1 --port 8000
```

### Step 4: Test AI Features

**Refresh dashboard:** http://127.0.0.1:8000

Now you can:
- ✅ Click "🔍 Analyze Now" to get AI suggestions
- ✅ Chat with AI about your system
- ✅ Click "Analyze Root Cause" on incidents
- ✅ AI fallback for unmatched errors

---

## 🎮 Quick Test Scenarios

### Test 1: Generate Test Data
```bash
source venv/bin/activate
python generate_test_data.py
```

Refresh dashboard → See random incidents and actions!

### Test 2: Chat with AI (Needs API Key)
1. Click 💬 button
2. Type: "What's the most common error?"
3. AI analyzes and responds

### Test 3: Root Cause Analysis (Needs API Key)
1. Click any incident in table
2. Click "🔍 Analyze Root Cause with AI"
3. AI explains what happened

### Test 4: Trigger AI Analysis (Needs API Key)
1. Click "🔍 Analyze Now" in AI Suggestions card
2. AI analyzes unhandled errors
3. Suggests new rules
4. Click "✅ Approve & Activate" to add rule

---

## 📊 Current Dashboard Features

### Working Now (No Key):
- ✅ Live statistics
- ✅ Incidents chart
- ✅ Actions success rate chart
- ✅ Recent incidents table
- ✅ Recent actions table
- ✅ Cooldown progress bars
- ✅ Quick action buttons
- ✅ Service discovery (if Docker running)
- ✅ Rule management API

### Needs Gemini Key:
- 🔒 AI Rule Suggestions
- 🔒 AI Chat
- 🔒 Root Cause Analysis
- 🔒 AI Fallback

---

## 🎯 What to Test Right Now

**Without API key, you can:**

1. **View the beautiful UI**
   - Charts and graphs
   - Real-time data
   - Professional design

2. **Test service discovery**
   ```bash
   curl http://127.0.0.1:8000/services/discover
   ```

3. **Test rule management**
   ```bash
   curl http://127.0.0.1:8000/rules
   ```

4. **See the chat UI**
   - Click 💬 button
   - See the interface
   - (Won't get AI responses without key)

5. **Generate test data**
   ```bash
   python generate_test_data.py
   ```

---

## 🚀 Next Steps

**Right Now (No key needed):**
1. Open http://127.0.0.1:8000
2. Explore the dashboard
3. See all the new UI elements
4. Try the quick actions

**With Gemini Key (5 minutes to get):**
1. Get key from https://ai.google.dev/
2. Add to `.env`
3. Restart server
4. Test AI chat, suggestions, root cause analysis

---

## 💡 Tips

- The UI works great even without AI
- AI features are **addons** - not required
- All healing still works with 21 built-in rules
- AI just makes it smarter and self-improving
- Get the key when you're ready to try AI features!

**Your dashboard is running and looks amazing! 🎨**
