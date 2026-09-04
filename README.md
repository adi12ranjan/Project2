# Voice Integrity Shield

Real-time AI voice-clone / bot-call detection. All analysis (FFT, pitch/jitter/shimmer,
spectral flatness, speaker-consistency drift) runs client-side in the browser — no audio
is uploaded anywhere.

## Live pages (deployed by Vercel from repo root)

| File | URL after deploy | What it is |
|---|---|---|
| `index.html` | `/` | Full dashboard — Command Center, Live Analysis, Forensic Evidence, Recommended Action, Audit Trail |
| `monitor.html` | `/monitor.html` (or `/monitor` with clean URLs) | Live Call Monitor — continuous mic listening with real-time risk gauge and auto-block |

Both pages need microphone permission, which browsers only grant over **HTTPS** or
`localhost` — Vercel serves HTTPS automatically, so this works out of the box once deployed.

## Deploying on Vercel

1. Push this repo to GitHub as-is (root already contains `index.html`, so no config needed).
2. In Vercel: **New Project** → import the repo → Framework Preset: **Other** (static) →
   leave Build Command and Output Directory blank → Deploy.
3. That's it — `vercel.json` just enables clean URLs.

## `chrome-extension/` folder

Not deployed by Vercel (Vercel will still serve it as static files if visited directly,
but it isn't linked from the app). This is a separately loadable Chrome extension for local
demo use:

1. Unzip / clone the repo.
2. `chrome://extensions` → enable **Developer mode** → **Load unpacked** → select the
   `chrome-extension` folder.
3. Click the extension icon → **Launch Live Monitor** (opens in its own tab, since popups
   close on blur and would kill mic capture mid-call).

## Guaranteed demo fallback

On the Live Call Monitor, the **Test: Human Caller** / **Test: Bot / Clone Caller** buttons
run the same detection pipeline against calibrated synthetic reference audio (no mic needed),
landing reliably at ~3% (low) and ~74% (high) risk respectively — useful if live mic pickup
is unreliable in a noisy demo room.
