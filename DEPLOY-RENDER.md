# 🚀 Deploy to Render.com (Free!)

This guide will help you deploy Kube-Healer to Render.com's free tier.

## ⚡ Quick Deploy (5 minutes)

### 1. **Fork or Push to GitHub**
Your code is already on GitHub at `github.com/nidhish1/kube-healer`

### 2. **Sign up for Render.com**
- Go to https://render.com
- Sign up with your GitHub account (free)

### 3. **Create New Web Service**
1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub account
3. Select repository: `nidhish1/kube-healer`
4. Click **"Connect"**

### 4. **Configure Service**
Render will auto-detect the `render.yaml` file. Just verify:

- **Name:** `kube-healer` (or your choice)
- **Environment:** Docker
- **Plan:** Free
- **Health Check Path:** `/health`

### 5. **Deploy!**
- Click **"Create Web Service"**
- Wait 3-5 minutes for build and deployment
- Your app will be live at: `https://kube-healer-xxx.onrender.com`

## 📊 After Deployment

### Access Your App
- **API Docs:** `https://your-app.onrender.com/docs`
- **Health Check:** `https://your-app.onrender.com/health`
- **Stats:** `https://your-app.onrender.com/stats`

### Test It
```bash
# Health check
curl https://your-app.onrender.com/health

# Get stats
curl https://your-app.onrender.com/stats

# Execute an action
curl -X POST https://your-app.onrender.com/actions/execute \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "cleanup_disk",
    "parameters": {"paths": ["/tmp"], "keep_days": 7}
  }'
```

## 🔧 Configuration

### Environment Variables (Optional)
Add these in Render Dashboard → Environment:

```bash
DATABASE_URL=sqlite:///data/agent.db
LOG_LEVEL=INFO
SLACK_WEBHOOK=your-webhook-url
DISCORD_WEBHOOK=your-webhook-url
```

## ⚠️ Free Tier Limitations

- **Sleeps after 15 minutes** of inactivity
- Wakes up automatically on first request (~30 seconds)
- 750 hours/month free (enough for 24/7 if it's your only app)
- Good for demos and testing

## 🔄 Auto-Deploy

Every `git push` to `main` branch will automatically:
1. Build new Docker image
2. Deploy to Render
3. Restart the service

## 📝 Monitoring

### View Logs
Render Dashboard → Your Service → **Logs** tab

### Check Status
Render Dashboard → Your Service → **Events** tab

## 💡 Tips

1. **Wake it up:** Ping the `/health` endpoint every 10 minutes to keep it awake (use UptimeRobot or cron-job.org)
2. **Custom domain:** Add your own domain for free in Settings
3. **Persistent data:** Free tier has ephemeral storage - data resets on redeploy

## 🆙 Upgrade (Optional)

For always-on service without sleep:
- **Starter Plan:** $7/month
- Includes persistent disk and no sleep

## 🐛 Troubleshooting

### Build Failed
- Check Docker logs in Render dashboard
- Verify `Dockerfile` and `requirements.txt` are correct

### App Won't Start
- Check logs for errors
- Verify health check endpoint is responding

### 503 Error
- App is likely sleeping (free tier)
- Wait 30 seconds for it to wake up

## 📞 Support

- Render Docs: https://render.com/docs
- Kube-Healer Issues: https://github.com/nidhish1/kube-healer/issues

---

**That's it!** Your self-healing agent is now live and accessible worldwide! 🎉
