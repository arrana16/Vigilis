# Vigilis Backend - Render Deployment Guide

## Quick Deploy to Render

### Step 1: Prepare Your Repository
Your code is ready! These files are configured:
- ✅ `Procfile` - tells Render how to start the server
- ✅ `runtime.txt` - specifies Python 3.11
- ✅ `requirements.txt` - all dependencies listed
- ✅ `backend/api.py` - FastAPI application

### Step 2: Push to GitHub
```bash
git add .
git commit -m "Ready for Render deployment"
git push origin main
```

### Step 3: Deploy on Render

1. **Go to [render.com](https://render.com)** and sign up/login with GitHub

2. **Click "New +" → "Web Service"**

3. **Connect your GitHub repository:**
   - Select "Vigilis" repository
   - Click "Connect"

4. **Configure the service:**
   - **Name:** `vigilis-backend` (or your choice)
   - **Region:** Choose closest to you
   - **Branch:** `main` (or `Agents`)
   - **Root Directory:** leave blank
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn backend.api:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** Free

5. **Add Environment Variables** (click "Advanced" → "Add Environment Variable"):
   ```
   GOOGLE_GENAI_USE_VERTEXAI = 0
   GEMINI_API_KEY = <your-gemini-api-key>
   MONGO_URI = <your-mongodb-connection-string>
   ```

6. **Click "Create Web Service"**

Render will:
- Install dependencies
- Start your FastAPI server
- Give you a live URL like `https://vigilis-backend.onrender.com`

### Step 4: Test Your Deployment

Once deployed, test with:
```bash
# Health check
curl https://your-app-name.onrender.com/health

# Chat endpoint
curl -X POST https://your-app-name.onrender.com/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What is the status?","incident_id":"690eb0a52e8f17ecb7b23e81"}'
```

### Important: MongoDB Atlas Setup

Make sure your MongoDB Atlas cluster allows connections from anywhere:
1. Go to MongoDB Atlas → Network Access
2. Add IP Address → Allow Access from Anywhere (0.0.0.0/0)
3. Or add Render's IP addresses specifically

### Environment Variables Reference

| Variable | Value | Description |
|----------|-------|-------------|
| `GOOGLE_GENAI_USE_VERTEXAI` | `0` | Force API key mode (required) |
| `GEMINI_API_KEY` | Your API key | Get from Google AI Studio |
| `MONGO_URI` | `mongodb+srv://user:pass@...` | Your MongoDB Atlas connection string |

### Auto-Deploy on Push

Render automatically redeploys when you push to GitHub! Just:
```bash
git add .
git commit -m "Update feature"
git push
```

### Monitoring & Logs

- View live logs: Render Dashboard → Your Service → Logs
- Check status: Render Dashboard → Your Service → Events
- Custom domain: Render Dashboard → Settings → Custom Domain

### Troubleshooting

**Cold starts:** Free tier sleeps after 15 min of inactivity. First request may take 30-60s.

**Build fails:** Check logs for missing dependencies or import errors.

**API returns 401:** Verify `GOOGLE_GENAI_USE_VERTEXAI=0` is set and `GEMINI_API_KEY` is correct.

**MongoDB connection fails:** Check Network Access in Atlas and verify `MONGO_URI`.

### Upgrade to Paid (Optional)

Free tier limits:
- 750 hours/month (enough for 1 service)
- Spins down after 15 min inactivity
- 512 MB RAM

Starter plan ($7/month):
- No spin down
- More RAM
- Faster builds

---

**That's it!** Your backend is live. Share the Render URL with your frontend team.
