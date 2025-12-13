# Yellow Pages Sports Chatbot - Flask API Deployment

## 🚀 Deployment Guide for Railway

### Prerequisites
- Railway account (free): https://railway.app
- GitHub account
- OpenAI API key

### Files in This Directory
```
flask_api_deploy/
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── Procfile                    # Railway deployment config
├── .gitignore                  # Git ignore rules
├── yellowpages_v5_final.csv    # Business data (copy from parent dir)
└── yellowpages_vectorstore/    # FAISS index (copy from parent dir)
```

### Step 1: Prepare Files

**Copy your data files:**
```bash
# From the parent directory
cp ../yellowpages_v5_final.csv .
cp -r ../yellowpages_vectorstore .
```

### Step 2: Deploy to Railway

#### Option A: Deploy from GitHub (Recommended)

1. **Create GitHub Repository:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Flask API for chatbot"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/yellowpages-chatbot-api.git
   git push -u origin main
   ```

2. **Deploy on Railway:**
   - Go to https://railway.app
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Add environment variable:
     - Key: `OPENAI_API_KEY`
     - Value: `your-openai-api-key`
   - Railway will auto-deploy!

3. **Get Your URL:**
   - Railway provides a URL like: `https://your-app.railway.app`
   - Copy this URL for your Lovable frontend

#### Option B: Deploy via Railway CLI

1. **Install Railway CLI:**
   ```bash
   npm install -g @railway/cli
   ```

2. **Login and Deploy:**
   ```bash
   railway login
   railway init
   railway up
   ```

3. **Set Environment Variable:**
   ```bash
   railway variables set OPENAI_API_KEY=your-key-here
   ```

### Step 3: Update Lovable Frontend

In your Lovable app, update the API URL:

```typescript
// Change from:
const API_URL = 'http://127.0.0.1:5000/chat';

// To:
const API_URL = 'https://your-app.railway.app/chat';
```

### Step 4: Test Your Deployed API

**Health Check:**
```bash
curl https://your-app.railway.app/
```

**Test Chat:**
```bash
curl -X POST https://your-app.railway.app/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "หาโยคะในกรุงเทพ"}'
```

### Troubleshooting

**Issue: "Module not found"**
- Check `requirements.txt` has all dependencies
- Redeploy: `railway up`

**Issue: "FAISS loading error"**
- Ensure `yellowpages_vectorstore` folder is committed to Git
- Check folder structure is correct

**Issue: "OpenAI API error"**
- Verify `OPENAI_API_KEY` environment variable is set
- Check API key has credits

### API Endpoints

#### GET /
Health check endpoint
```json
{
  "status": "Chatbot API is running!",
  "service": "Yellow Pages Sports Chatbot",
  "version": "1.0"
}
```

#### POST /chat
Chat endpoint
```json
Request:
{
  "message": "หาโยคะในกรุงเทพ"
}

Response:
{
  "response": "สวัสดีค่ะ! 😊 ดิฉันมีคำแนะนำ..."
}
```

### Cost Considerations

**Railway Free Tier:**
- $5 free credits monthly
- Enough for testing/demo
- Auto-sleeps after inactivity

**OpenAI API:**
- Uses gpt-4o-mini (cheap)
- ~$0.01 per conversation
- Set hard limit on OpenAI dashboard

### For Submission

**Include in your report:**
1. Live demo URL: `https://your-lovable-app.lovable.dev`
2. API endpoint: `https://your-app.railway.app`
3. GitHub repo: `https://github.com/YOUR_USERNAME/yellowpages-chatbot-api`
4. This README for reproducibility

**Advantages:**
- ✅ Evaluators can test immediately (no setup!)
- ✅ Shows production deployment skills
- ✅ Professional presentation
- ✅ Scalable architecture

---

## 📝 Local Development

To run locally:
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variable
export OPENAI_API_KEY=your-key-here

# Run Flask
python app.py
```

Access at: http://localhost:5000

---

## 🎯 Architecture

```
User (Lovable UI)
    ↓
Railway Flask API (this app)
    ↓
Multi-Agent Router
    ↓
├─ Business Search (FAISS)
├─ Knowledge Agent (LLM)
├─ Exploration Agent
└─ Out-of-Scope Handler
    ↓
Response Polishing
    ↓
User receives Thai response
```

**Key Features:**
- 5 specialized agents
- FAISS vector search (3,536 businesses)
- Smart context switching
- Location validation
- Natural Thai responses

---

Created by PATI for AI Engineer Position Application
