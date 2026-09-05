# TraceMail AI — Email Threat & Forensic Intelligence Platform

Smart India Hackathon 2026 — PS-26106

Full-stack version: **Next.js (React) frontend + Python FastAPI backend**, built on
top of the working TraceMail AI prototype. The detection engine (SPF/DKIM/DMARC
analysis, lookalike-domain detection via edit distance, keyword-based threat
detection, weighted explainable scoring, relay-chain forensics, offline demo
geolocation, investigation graph, Markdown report generation) is the same
engine used and verified earlier in this project — every score is backed by a
listed reason, nothing is a fabricated ML accuracy percentage.

## Project structure

```
/                     Next.js frontend lives at repo root (Vercel expects
                      package.json here for zero-config detection — no
                      Root Directory setting needed)
  app/
    layout.jsx            root layout (wraps pages with the sidebar Shell)
    page.jsx               Dashboard
    investigation/page.jsx  Email Investigation (main demo page)
    intelligence/page.jsx    Threat Intelligence
    iocs/page.jsx            IOC Explorer
    reports/page.jsx         Reports
    globals.css              TraceMail AI dark SOC design system
  components/              Shell, ThreatGauge, Badge, ForensicGraph,
                             InvestigationResult, ReportModal
  lib/api.js                fetch helpers
  next.config.mjs            proxies /api/* to BACKEND_URL (defaults to
                             localhost:8000 for local dev)
  package.json

backend/                 FastAPI app — separate service, not deployed by Vercel
  app/
    main.py             FastAPI app + routes
    parser.py            .eml -> structured fields
    auth_analyzer.py     SPF/DKIM/DMARC + alignment
    relay_tracer.py       Received-header chain reconstruction
    ioc_extractor.py     IPs/domains/URLs/emails/hashes + risk rating
    threat_detector.py    phishing/BEC/impersonation detection
    risk_scorer.py        weighted score + plain-English reasons
    geolocation.py         offline demo IP -> location dataset
    graph_builder.py      investigation graph nodes/edges
    report_generator.py   Markdown forensic report
    database.py           SQLite persistence
    pipeline.py            orchestrates all of the above
    demo_data/             4 real, hand-built demo .eml files
  requirements.txt

render.yaml             one-click Render blueprint for the backend
```

## Deploying

**Frontend (Vercel):** push this repo to GitHub, import it into Vercel. Since
`package.json` sits at the repo root, Vercel auto-detects Next.js with zero
configuration — no Root Directory setting to remember or forget.

**Backend (Render):** New → Blueprint → point at the same repo → it reads
`render.yaml` automatically (it sets its own root directory to `backend/`
internally, so this works from the same repo without conflicting with the
frontend). Copy the resulting URL.

**Connect them:** in Vercel → Settings → Environment Variables, add
`BACKEND_URL` = your Render URL (e.g. `https://tracemail-ai-backend.onrender.com`,
no trailing slash). Redeploy the frontend once so it picks up the variable.



## Running it locally

**Terminal 1 — backend:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Confirm it's up: `http://localhost:8000/api/health`

**Terminal 2 — frontend (run from the repo root, not a subfolder):**
```bash
npm install
npm run dev
```
Open `http://localhost:3000`. `next.config.mjs` proxies `/api/*` requests to
the backend on port 8000 by default, so no environment variables are needed
for local development.

## Demo flow

1. Go to **Email Investigation**.
2. Pick one of the 4 built-in demo emails (BEC / Phishing / Legit / Lookalike
   domain) — or upload a `.eml` file, or paste raw content.
3. Click **Analyze Email** — the real pipeline runs: threat gauge, detection
   findings with point-by-point reasons, SPF/DKIM/DMARC cards, IOC list,
   forensic relay trace, geolocation panel (clearly labeled demo data),
   investigation graph, and recommended actions.
4. Click **View Report** or **Download** for the full Markdown incident report.
5. Visit **Dashboard**, **Threat Intelligence**, and **IOC Explorer** to see
   aggregate views across every email analyzed this session.

## What's verified vs. what needs your local run

The backend pipeline was executed end-to-end against all 4 demo emails during
development (100/CRITICAL, 87/CRITICAL, 0/SAFE, 83/CRITICAL — each with
correct, distinct, genuinely-computed reasons, not hardcoded per-email
output), and every backend `.py` file was syntax-checked. Every frontend
`.jsx`/`.js` file was syntax-verified with esbuild's real JS/JSX parser, and
every relative import path was checked to resolve to an actual file.

What could not be verified in the sandbox this was built in (no network
access to `npm install` Next.js or `pip install` FastAPI): the live Next.js
dev server actually rendering in a browser, and the real `uvicorn` server
handling requests. Both follow completely standard, documented patterns for
Next.js App Router and FastAPI — but running the two commands above on your
machine is the first true end-to-end check. If either errors, send the exact
message and it gets fixed immediately.
