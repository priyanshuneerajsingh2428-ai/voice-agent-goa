# 🚀 Deploy to Render (Free Tier) - Step by Step

Your #RAGInGoa agent is ready to go live! Follow these steps to deploy to Render for FREE with a permanent public URL.

---

## ⏱️ Time Required: ~10 minutes

## 💰 Cost: FREE (forever, with free tier limits)

---

## Step 1: Create GitHub Repository (2 minutes)

First, push your code to GitHub so Render can automatically deploy it.

### Option A: Command Line (if you have git installed)
```bash
cd "c:\Users\Priya\voice agent goa"
git init
git add .
git commit -m "Initial commit: RAGInGoa voice agent ready for deployment"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/voice-agent-goa.git
git push -u origin main
```

### Option B: Using GitHub Web Interface
1. Go to https://github.com/new
2. Create a new repository called `voice-agent-goa`
3. Copy the repository URL
4. Use Git Desktop or command line to push your code

**Note:** If you don't have GitHub, [sign up free here](https://github.com/signup)

---

## Step 2: Create Render Account (2 minutes)

1. Go to https://render.com
2. Click **"Get Started"** (top right)
3. Sign up with GitHub (recommended for auto-deployment)
   - This lets Render auto-deploy every time you push to GitHub
4. Authorize Render to access your GitHub account
5. Confirm your email

---

## Step 3: Deploy Your App (5 minutes)

Once logged into Render:

### 3.1 Create New Web Service
1. Click **"New +"** (top right)
2. Select **"Web Service"**

### 3.2 Connect Your Repository
1. Look for "Connect Repository"
2. Find and click your `voice-agent-goa` repository
3. Click **"Connect"**

### 3.3 Configure Service Settings
Fill in the deployment form:

| Field | Value |
|-------|-------|
| **Name** | `rainingoa` (or any name) |
| **Environment** | `Python 3` |
| **Region** | `Oregon (US West)` or your preferred region |
| **Branch** | `main` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn app:app` |

### 3.4 Add Environment Variables (if needed)
Click **"Advanced"** and add:
- `PYTHON_VERSION` → `3.13.0`
- `FLASK_ENV` → `production`

### 3.5 Select Plan
- Select **"Free"** tier (bottom left)
- **Cost: $0/month** ✅

### 3.6 Deploy
Click **"Create Web Service"** and wait 2-3 minutes for deployment.

---

## Step 4: Get Your Public URL (1 minute)

Once deployment completes (you'll see a green checkmark):

1. Your app URL will be shown at the top of the page
2. It looks like: `https://rainingoa.onrender.com`
3. **This is your permanent public URL!**

Click the URL to visit your live website! 🎉

---

## ✅ Verify Deployment

### Test These URLs:

```
Landing Page:
https://YOUR_URL.onrender.com/

Agent Interface:
https://YOUR_URL.onrender.com/agent

API Endpoint:
https://YOUR_URL.onrender.com/ask
```

**Expected Results:**
- ✅ Landing page loads with features
- ✅ Agent interface shows with voice button
- ✅ API returns answers

---

## 🔄 How to Update Your App

Every time you push code to GitHub, Render automatically redeploys! Just:

```bash
git add .
git commit -m "Your update message"
git push origin main
```

Render detects the push and redeploys in ~2-3 minutes.

---

## ⚠️ Free Tier Limitations

**Render Free Tier includes:**
- ✅ 1 free web service
- ✅ 750 compute hours/month (covers ~24/7 uptime)
- ✅ Automatic HTTPS/SSL
- ✅ Auto-deploy from GitHub
- ✅ 100 GB bandwidth
- ✅ Generous CPU/RAM allocation

**Potential limitations:**
- ⚠️ **Cold start:** First request after idle period takes 15-30 seconds (free tier only)
  - Workaround: Use external uptime monitor like Uptime Robot
- ⚠️ **Spins down:** App goes to sleep after 15 minutes of inactivity
  - Solution: Upgrade to paid ($7/month) for always-on

---

## 🎯 Upgrade to Paid (Optional)

If you want faster performance:

1. Click **"Settings"** on your Render dashboard
2. Scroll to **"Plan"**
3. Click **"Upgrade to Paid"** ($7/month)

**Benefits:**
- ✅ No cold starts
- ✅ Always running
- ✅ Professional performance
- ✅ Priority support

---

## 🔐 Production Checklist

Before sharing your URL with judges, verify:

- [ ] Landing page loads without errors
- [ ] Agent interface is responsive
- [ ] Voice input works (or shows fallback message)
- [ ] Answers are accurate
- [ ] Performance metrics display
- [ ] No console errors (check browser dev tools)

---

## 📱 Share Your URL

Now you can send judges:
```
🎓 Check out my RAG Agent: https://your-url.onrender.com
```

**They can:**
- Visit your landing page
- Try the agent interface
- Test voice queries
- See live performance metrics

All from any device, anywhere in the world! 🌍

---

## 🆘 Troubleshooting

### "Build failed" error?
- Check that `requirements.txt` exists
- Ensure all dependencies are listed
- Wait 5 minutes and click "Manual Deploy" again

### App crashes immediately?
- Check the **"Logs"** tab in Render dashboard
- Verify `gunicorn app:app` command is correct
- Ensure `app.py` has `if __name__ == '__main__':` block

### Very slow first request?
- This is normal on free tier (cold start)
- Upgrade to paid ($7/month) for instant loading
- Or use Uptime Robot to keep app warm

### Landing page encoding error?
- This should already be fixed in app.py
- If not, contact support

---

## 📊 Monitor Your Deployment

In the Render dashboard:

1. **Metrics** tab - View CPU, RAM, network usage
2. **Logs** tab - See real-time server logs
3. **Events** tab - Track deployment history
4. **Settings** tab - Manage secrets, environment vars, plan

---

## 🎁 What You Now Have

✅ **Live website** at https://your-url.onrender.com
✅ **Automatic deployments** from GitHub
✅ **HTTPS/SSL** (secure connection)
✅ **Always updated** with latest code
✅ **Professional URL** for portfolio
✅ **Permanent home** for your project

---

## 🚀 Share with Hacker House Judges

Email or message your Render URL:

```
Dear Judges,

Here's my #RAGInGoa project - a voice-enabled RAG agent for college queries:

🔗 Live Demo: https://rainingoa.onrender.com
📖 GitHub: https://github.com/your-username/voice-agent-goa
📚 Docs: Check README.md and DEMO.md in repository

Features:
• Voice input with semantic search
• FAISS-powered retrieval
• <150ms latency
• Zero hallucinations (grounded answers)
• Beautiful responsive UI

Thanks!
```

---

## ✨ Success!

Your app is now live on the internet. 🎉

**Permanent URL:** `https://your-url.onrender.com`

Share this with judges, add to your portfolio, or use for any college deployment!

---

## 📞 Need Help?

- **Render Docs:** https://docs.render.com
- **Render Support:** https://render.com/support
- **Deploy again:** Click "Manual Deploy" button in Render dashboard

---

**Congratulations! Your voice-enabled RAG agent is live!** 🚀

