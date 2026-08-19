# Formulary Intelligence Dashboard

React + JavaScript dashboard for the Pharmacy Formulary Optimization and Adherence Assistant MVP v2.3

## Run locally

1. Copy `.env.example` to `.env`.
2. Ensure FastAPI is running at `http://127.0.0.1:8000`.
3. Install and start:

```powershell
npm install
npm run dev
```

Open `http://localhost:5173`.

## Pages

- Plan overview: KPIs, risk, tier, restriction, cost, pharmacy, medication, and opportunity analytics.
- Prescriber analysis: plan-filtered prescriber list, summary, medication exposure, and formulary review opportunities.

All official metrics are supplied by FastAPI. The frontend performs formatting and presentation only.
