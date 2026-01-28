# Python Version Compatibility

## Supported Python Versions

### ✅ Fully Supported (Recommended)
- **Python 3.11** - Best compatibility, all features work
- **Python 3.12** - Good compatibility, all features work

### ⚠️ Partially Supported
- **Python 3.13** - Core features work, ChromaDB not available
- **Python 3.14** - Core features work, ChromaDB not available

### ❌ Not Supported
- Python 3.10 and below - Too old, missing features

---

## What Works with Python 3.14?

### ✅ Core Features (Working)
- Log watching and pattern detection
- AI analysis (OpenAI/Anthropic)
- Action execution (service restart, disk cleanup)
- Database storage
- REST API
- Slack/Discord notifications

### ❌ Optional Features (Not Available)
- **ChromaDB** - Vector similarity search
  - Reason: `onnxruntime` doesn't support Python 3.14 yet
  - Impact: Can't find similar past incidents automatically
  - Workaround: Use simple pattern matching instead

---

## Checking Your Python Version

```bash
# Check system Python
python3 --version

# Check venv Python (after running make quick-start)
make python-version
```

---

## Recommendations

### If You Have Python 3.14 (Your Case)
✅ **Use the project as-is** - All core features work!
- ChromaDB is optional and not critical
- The agent works perfectly without it

### If You Want Full Features
📥 **Install Python 3.11 or 3.12**

#### Option 1: Using pyenv (Recommended)
```bash
# Install pyenv
brew install pyenv

# Install Python 3.12
pyenv install 3.12.0

# Use it for this project
cd /path/to/project
pyenv local 3.12.0

# Now run make quick-start
make quick-start
```

#### Option 2: Using Homebrew
```bash
# Install Python 3.12
brew install python@3.12

# Create venv with it
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-optional.txt
```

### If You Want Zero Issues
🐳 **Use Docker Instead**
```bash
# No Python version issues at all!
make docker-quick-start
```

Docker uses Python 3.11 internally and everything just works!

---

## Summary

| Feature | Python 3.11-3.12 | Python 3.13-3.14 |
|---------|------------------|------------------|
| Log Monitoring | ✅ | ✅ |
| AI Analysis | ✅ | ✅ |
| Auto-Remediation | ✅ | ✅ |
| REST API | ✅ | ✅ |
| Notifications | ✅ | ✅ |
| ChromaDB | ✅ | ❌ |
| Vector Search | ✅ | ❌ |

**Bottom line:** You can use Python 3.14! The agent works great, you just won't have advanced similarity search.
