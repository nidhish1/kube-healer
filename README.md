# 🛡️ Kube-Healer

**Smart DevOps agent that watches your logs, detects problems, and fixes them automatically.**

No more 3am alerts. No more manual restarts. Just set it up and let it handle the routine issues.

---

## 🚀 Quick Start

```bash
git clone https://github.com/nidhish1/kube-healer.git
cd kube-healer
docker-compose up -d
```

**Access:**
- 📊 API Dashboard: http://localhost:8000/docs
- 📜 Live Logs: http://localhost:9999

👉 **[Full Quick Start Guide →](QUICKSTART.md)**

---

## ✨ What It Does

- **Watches** your application logs in real-time
- **Detects** errors using pattern matching (disk full, OOM, connection failures)
- **Fixes** issues automatically (cleans disk, restarts services, kills processes)
- **Learns** from past incidents (tracks everything in a database)
- **Notifies** you via Slack/Discord when actions are taken

---

## 🎯 Built-in Auto-Fixes

| Problem | Action |
|---------|--------|
| Disk full | Cleanup old temp files |
| Out of memory | Restart service |
| Connection refused | Restart service |
| Too many DB connections | Restart database |
| Cache full | Clear application cache |

**Extensible:** Add your own rules in minutes.

---

## 🔧 Deployment Options

- **🐳 Docker** (recommended) - [Docker Guide →](DOCKER.md)
- **🐍 Python** (local) - [Python Setup →](README-PYTHON-VERSION.md)
- **🤖 No AI Required** (100% free) - [No-AI Guide →](README-NO-AI.md)

---

## 📖 Documentation

- **[Quick Start](QUICKSTART.md)** - Get running in 2 minutes
- **[Docker Deployment](DOCKER.md)** - Production Docker setup
- **[No-AI Mode](README-NO-AI.md)** - Free rule-based operation
- **[Python Versions](README-PYTHON-VERSION.md)** - Compatibility guide

---

## 🏗️ Architecture

```
Log Files → Watcher → Rule Engine → Executor → Fixed!
                          ↓
                    Database (history)
```

**Tech:** Python 3.11+, FastAPI, SQLite, Docker, Watchdog

---

## 🤝 Contributing

Issues and PRs welcome! Built for the DevOps community.

---

## 📜 License

MIT License - Use it however you want!
