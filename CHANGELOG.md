# Kube-Healer Changelog

## [Version 2.0.0] - 2026-01-28 - Major Functional Upgrades

### 🎯 What Changed

This release transforms Kube-Healer from a prototype to a **production-ready self-healing platform**.

---

### ✨ New Features

#### 1. Real Action Execution
- **Docker Container Restart** - Actually restarts containers using Docker SDK
- **Systemd Service Restart** - Uses systemctl for service control  
- **Process Termination** - psutil-based graceful/force kill
- **Pre/Post Validation** - Checks service exists and verifies success

#### 2. Expanded Rule Coverage (5 → 21 Rules)
- Disk & Storage: full, quota exceeded, inode exhaustion
- Memory: OOM, memory leaks
- Network: timeout, refused, reset, port conflicts
- Database: deadlocks, connection pool exhaustion
- SSL/TLS: certificate expiry, handshake failures
- HTTP: 502, 503 errors
- Process: segfaults, hung processes, permission errors
- Cache: Redis failures, cache overflow

#### 3. Docker Log Monitoring
- **New DockerWatcher** - Stream logs directly from containers
- Auto-discovery by container name
- Real-time log pattern matching
- Timestamp parsing

#### 4. Dynamic Rule Loading
- Load rules from `config/rules.yaml`
- Priority-based rule matching
- Enable/disable without code changes
- Custom rules with parameters

#### 5. Context Extraction
- Auto-detect severity (critical/high/medium/low)
- Extract error codes, PIDs, ports
- Identify components (nginx, mysql, redis, etc.)
- Parse timestamps from log lines
- Stack trace detection

#### 6. Service Discovery
- Auto-discover Docker containers
- Auto-discover systemd services
- Service metadata collection
- Find services by name

#### 7. Rule Management API
- `GET /rules` - List all rules
- `POST /rules` - Create rule
- `PUT /rules/{id}` - Update rule  
- `DELETE /rules/{id}` - Delete rule
- `GET /services/discover` - Discover services
- `GET /services/docker` - Docker containers

---

### 📊 Statistics

**Code Changes:**
- 11 files modified
- 1,200+ lines added
- 4 new modules created
- 6 new API endpoints
- 16 new healing rules

**Functional Improvements:**
- Actions: 2 placeholder → 4 fully functional
- Rules: 5 static → 21 dynamic + custom YAML
- Watchers: 1 type (file) → 2 types (file + docker)
- API: 9 endpoints → 15 endpoints

---

### 🔧 Technical Details

#### New Modules:
1. `src/watchers/docker_watcher.py` - Docker log streaming
2. `src/analyzer/context_extractor.py` - Intelligent parsing
3. `src/discovery/service_discovery.py` - Service auto-discovery
4. `config/rules.yaml` - Custom rule configuration

#### Enhanced Modules:
- `src/executors/service_manager.py` - Real Docker/systemd/psutil
- `src/analyzer/rule_based_planner.py` - 21 rules + YAML loading
- `src/agent.py` - Context extraction integration
- `src/knowledge/repository.py` - Rule CRUD operations
- `src/api/routes.py` - 6 new endpoints

---

### 🚀 Migration Guide

#### For Existing Users:

**1. Update Dependencies:**
```bash
source venv/bin/activate
pip install -r requirements.txt --upgrade
```

**2. New Configuration Options:**
```yaml
# config/config.yaml
watchers:
  - type: docker  # NEW: Docker log monitoring
    path: container-name
    patterns:
      - "ERROR.*"

# config/rules.yaml (NEW FILE)
rules:
  - name: custom_rule
    pattern: "your pattern"
    action: restart_service
    priority: 10
```

**3. New API Endpoints:**
- Test at: http://localhost:8000/docs
- Try service discovery: `GET /services/discover`
- Manage rules: `GET/POST/PUT/DELETE /rules`

---

### 🐛 Bug Fixes
- Fixed database session management for async context
- Fixed indentation in K8s restart placeholder
- Added greenlet dependency for SQLAlchemy

---

### 💡 Usage Examples

#### Watch Docker Container:
```yaml
# config/config.yaml
watchers:
  - type: docker
    path: nginx
    patterns:
      - "ERROR.*"
      - "(?i)502"
```

#### Custom Rule:
```yaml
# config/rules.yaml
rules:
  - name: high_cpu_usage
    pattern: "(?i)cpu.*9[5-9]%"
    action: restart_service
    parameters:
      service_name: myapp
      service_type: docker
```

#### Restart Docker Container via API:
```bash
curl -X POST http://localhost:8000/actions/execute \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "restart_service",
    "parameters": {
      "service_name": "nginx",
      "service_type": "docker"
    }
  }'
```

#### Create Rule via API:
```bash
curl -X POST http://localhost:8000/rules \
  -H "Content-Type: application/json" \
  -d '{
    "name": "disk_90_percent",
    "pattern": "(?i)disk.*9[0-9]%",
    "action_type": "cleanup_disk",
    "parameters": {"paths": ["/tmp"], "keep_days": 3},
    "priority": 15
  }'
```

---

### 📈 Performance & Scalability

**Improvements:**
- Async Docker log streaming (non-blocking)
- Efficient pattern matching with compiled regex
- Database indexing on timestamps
- Connection pooling for Docker/systemd

**Tested With:**
- 100+ incidents tracked
- 21 rules active simultaneously
- Multiple containers monitored
- Sub-second rule matching

---

### 🔐 Security

**Safety Features:**
- Cooldown periods prevent action spam
- Dry-run mode for testing
- Permission checks for systemd/process operations
- Graceful shutdown before force kill
- Error validation before execution

---

### 🎓 What's Next (Future Roadmap)

Potential future enhancements:
- Kubernetes pod restart implementation
- Journald log monitoring
- Rollback capabilities
- Multi-instance coordination
- ML-based anomaly detection
- Alert escalation policies
- Predictive health monitoring

---

### 📞 Support

- **GitHub**: https://github.com/nidhish1/kube-healer
- **Documentation**: See README.md and other guides
- **Issues**: https://github.com/nidhish1/kube-healer/issues

---

## [Version 1.0.0] - 2026-01-27 - Initial Release

- Basic file log monitoring
- 5 default healing rules
- Simple disk cleanup action
- Placeholder service restart
- SQLite incident tracking
- FastAPI dashboard
- Render.com deployment support
