# WebLens 🔭 — URL Analyzer & AWS Architect AI

> Paste any URL for instant AI analysis. Describe your project for a tailored AWS architecture with real cost estimates.
> Built by Arpit Sehrawat · Bennett University

## Live Demo
🔗 https://weblens-arpit.vercel.app *(update after deploy)*

---

## What it does

| Tool | Description |
|------|-------------|
| 🔭 **URL Analyzer** | Paste any URL → AI fetches the page, summarizes it, extracts key points, and answers your specific questions about the content |
| ☁️ **AWS Architect** | Describe your project → AI recommends the right AWS services, draws a data flow diagram, estimates costs, and flags free-tier risks |

## Tech Stack
- **AI**: Llama 3.3 70B via Groq API
- **Backend**: Python serverless functions (Vercel) — uses stdlib `urllib` + `re` for page fetching and HTML parsing
- **Frontend**: Vanilla HTML/CSS/JS — zero dependencies
- **Deploy**: Vercel (static + serverless)

## File Structure
```
weblens/
├── index.html          ← Full frontend (URL Analyzer + AWS Architect)
├── api/
│   ├── analyze.py      ← URL fetch + AI analysis serverless function
│   └── architect.py    ← AWS architecture advisor serverless function
├── requirements.txt    ← No deps (uses stdlib urllib + re)
├── vercel.json         ← Routing config
└── README.md
```

## Setup & Deploy

### 1. Get a Groq API Key
- Go to https://console.groq.com → API Keys → Create API Key

### 2. Deploy to Vercel
```bash
# Install Vercel CLI if not already
npm install -g vercel

# In this folder:
vercel

# Add the env variable:
vercel env add GROQ_API_KEY
# Paste your key when prompted

# Deploy to production:
vercel --prod
```

### 3. Or push to GitHub and connect Vercel
- Push this repo to GitHub
- Go to vercel.com → New Project → Import your repo
- Settings → Environment Variables → add `GROQ_API_KEY`
- Deploy

## Local Development
```bash
npm install -g vercel
vercel dev
```
Open http://localhost:3000

## How URL Analysis Works
1. Frontend sends `{ url, query }` to `/api/analyze`
2. Python function fetches the page using `urllib` (no external deps)
3. Strips HTML tags, scripts, nav, footer — keeps clean text (~6000 words max)
4. Sends cleaned text + user query to Groq (Llama 3.3 70B)
5. Returns structured JSON: title, type, summary, key_points, answer, topics

> Note: Some pages block bots or require login — the analyzer handles these gracefully with error messages.

---

Built with ❤️ for SIH 2024 · [Portfolio](https://my-portfolio-steel-nu-70.vercel.app)
