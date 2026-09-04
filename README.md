# FarmBridge — SIH26033 Full Starter

This is the first working full-stack build based on the SIH26033 prototype.

## Current build
- Responsive public landing page
- Farmer/consumer registration and login
- Farmer dashboard
- Add produce
- AI price suggestion prototype endpoint
- Farmer produce list
- Consumer marketplace with search/location filters
- Direct order placement
- Order status workflow
- SQLite local database
- Flask REST API

## Run in VS Code (Windows)
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python run.py
```
Open http://127.0.0.1:5000

## Suggested development order
1. Confirm this starter runs.
2. Connect real frontend interactions and improve validation.
3. Replace SQLite with Firebase if required by the team architecture.
4. Replace `/api/price-suggestion` demo estimator with the scikit-learn model trained on AGMARKNET data.
5. Add chat, SMS/low-bandwidth workflow, payments, logistics and deployment.

This is a hackathon prototype, not a production payment/authentication system.
