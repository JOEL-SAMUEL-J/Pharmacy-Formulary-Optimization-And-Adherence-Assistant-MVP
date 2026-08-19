import { useEffect, useMemo, useRef, useState } from "react";
import { apiRequest, endpoints } from "./api";
import {
  Activity, AlertTriangle, BarChart3, BrainCircuit, Check, ChevronDown, Database, Gauge,
  LayoutDashboard, MapPin, Pill, Search, Stethoscope, Target, WalletCards, X,
} from "lucide-react";
import {
  Bar, BarChart as ReBarChart, CartesianGrid, Cell,
  LabelList, Pie, PieChart, ResponsiveContainer, XAxis, YAxis,
} from "recharts";

const fmtCount = (value = 0) => new Intl.NumberFormat("en-US").format(value);
const fmtRate = (value = 0) => `${(Number(value) * 100).toFixed(1)}%`;
const fmtPercent = (value = 0) => `${Number(value).toFixed(1)}%`;
const titleCase = (value) => String(value).replaceAll("_", " ").replace(/\b\w/g, (c) => c.toUpperCase());
const displayPrescriber = (value = "") => value.replace(/^Synthetic\s+/i, "");
const coverageLabels = {
  HIGH_TIER_EXPOSURE: "Tier 4+",
  ELEVATED_SYNTHETIC_COST_BURDEN: "Elevated cost pressure",
  PRIOR_AUTHORIZATION_EXPOSURE: "Prior authorization",
  STEP_THERAPY_EXPOSURE: "Step therapy",
  QUANTITY_LIMIT_EXPOSURE: "Quantity limit",
};

const REVIEW_CUTOFF = 0.40;

function RestrictionBadges({ row }) {
  const active = [
    ["Prior auth", row.prior_authorization_rate],
    ["Step therapy", row.step_therapy_rate],
    ["Quantity limit", row.quantity_limit_rate],
  ].filter(([, value]) => Number(value) > 0);
  return active.length
    ? <div className="signal-badges">{active.map(([label, value]) => <span key={label}>{label} {fmtRate(value)}</span>)}</div>
    : <span className="muted">None</span>;
}

function ReviewStatus({ flagged, row }) {
  const [open, setOpen] = useState(false);
  const reasons = (row.review_reason_codes || []).map((reason) => {
    if (reason === "HIGH_TIER_EXPOSURE") return `${coverageLabels[reason]} · highest tier ${Number(row.maximum_tier).toFixed(0)}`;
    if (reason === "ELEVATED_SYNTHETIC_COST_BURDEN") return `${coverageLabels[reason]} · ${fmtRate(row.average_synthetic_cost_burden)}`;
    if (reason === "PRIOR_AUTHORIZATION_EXPOSURE") return `${coverageLabels[reason]} · ${fmtRate(row.prior_authorization_rate)}`;
    if (reason === "STEP_THERAPY_EXPOSURE") return `${coverageLabels[reason]} · ${fmtRate(row.step_therapy_rate)}`;
    if (reason === "QUANTITY_LIMIT_EXPOSURE") return `${coverageLabels[reason]} · ${fmtRate(row.quantity_limit_rate)}`;
    return titleCase(reason);
  });
  const dialogId = `review-reasons-${row.rxcui || row.drug_name?.replace(/\W+/g, "-").toLowerCase()}`;
  return <>
    <div className="review-cell">
      <span className={`status ${flagged ? "review" : "standard"}`}>{flagged ? "Review needed" : "No review needed"}</span>
      {flagged && <button className="review-reason-trigger" type="button" onClick={() => setOpen(true)} aria-haspopup="dialog" aria-controls={dialogId}>View reasons<ChevronDown size={14} aria-hidden="true" /></button>}
    </div>
    {open && <div className="review-modal-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) setOpen(false); }}>
      <section className="review-summary-modal review-reason-modal" id={dialogId} role="dialog" aria-modal="true" aria-labelledby={`${dialogId}-title`}>
        <header><div><span>PRESCRIBER REVIEW DETAIL</span><h3 id={`${dialogId}-title`}>{row.drug_name}</h3><p>Plan and medication conditions supporting the review decision.</p></div><button type="button" onClick={() => setOpen(false)} aria-label="Close review reasons"><X size={18} /></button></header>
        <div className="review-reason-list"><h4>Reasons for review</h4>{reasons.map((reason, index) => <div key={reason}><b>{index + 1}</b><span>{reason}</span></div>)}</div>
        <footer><button type="button" onClick={() => setOpen(false)}>Close</button></footer>
      </section>
    </div>}
  </>;
}

function PriorityScore({ value }) {
  const numeric = Number(value || 0);
  const label = numeric >= 0.60 ? "High" : "Moderate";
  return <div className={`priority-score ${label.toLowerCase()}`}><strong>{(numeric * 100).toFixed(1)}</strong><span>{label}</span></div>;
}

function ReviewFactors({ row }) {
  const [open, setOpen] = useState(false);
  useEffect(() => {
    if (!open) return undefined;
    const closeOnEscape = (event) => { if (event.key === "Escape") setOpen(false); };
    document.addEventListener("keydown", closeOnEscape);
    return () => document.removeEventListener("keydown", closeOnEscape);
  }, [open]);
  const factors = [];
  const risk = Number(row.average_risk || 0);
  const cost = Number(row.average_cost_burden || 0);
  const coverage = Number(row.restriction_exposure || 0);
  const pharmacy = Number(row.nonpreferred_exposure || 0);
  if (risk >= 0.75) factors.push(["Very high adherence risk", fmtRate(risk), "red"]);
  else if (risk >= 0.50) factors.push(["High adherence risk", fmtRate(risk), "orange"]);
  else factors.push(["Elevated adherence risk", fmtRate(risk), "amber"]);
  if (cost >= 0.50) factors.push(["High cost pressure", fmtRate(cost), "purple"]);
  else if (cost >= 0.35) factors.push(["Moderate cost pressure", fmtRate(cost), "purple"]);
  if (coverage > 0) factors.push(["Coverage requirements", fmtRate(coverage), "blue"]);
  if (pharmacy >= 0.25) factors.push(["Non-preferred pharmacy use", fmtRate(pharmacy), "teal"]);
  const summaryId = `review-summary-${row.rxcui || row.rank}`;
  return <>
    <div className="factor-disclosure"><button type="button" onClick={() => setOpen(true)} aria-haspopup="dialog" aria-expanded={open} aria-controls={summaryId}>View summary<ChevronDown size={15} aria-hidden="true" /></button></div>
    {open && <div className="review-modal-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) setOpen(false); }}>
      <section className="review-summary-modal" id={summaryId} role="dialog" aria-modal="true" aria-labelledby={`${summaryId}-title`}>
        <header><div><span>FORMULARY REVIEW SUMMARY</span><h3 id={`${summaryId}-title`}>{row.drug_name}</h3><p>Primary factors supporting review for the selected plan.</p></div><button type="button" onClick={() => setOpen(false)} aria-label="Close review summary"><X size={18} /></button></header>
        <div className="summary-metrics"><div><span>Priority score</span><strong>{(Number(row.review_score || 0) * 100).toFixed(1)}</strong></div><div><span>Members exposed</span><strong>{fmtCount(row.exposed_members)}</strong></div></div>
        <div className="summary-factors"><h4>Review factors</h4>{factors.slice(0, 3).map(([label, value, tone]) => <div className={`summary-factor ${tone}`} key={label}><div><span>{label}</span><strong>{value}</strong></div><div className="factor-bar" aria-hidden="true"><i style={{ width: value }} /></div></div>)}</div>
        <footer><button type="button" onClick={() => setOpen(false)}>Close</button></footer>
      </section>
    </div>}
  </>;
}

function Loading({ label = "Loading data" }) {
  return <div className="state"><span className="spinner" />{label}…</div>;
}

function DashboardSkeleton() {
  return <div className="dashboard-skeleton" aria-label="Loading dashboard">
    <div className="skeleton-kpis">{Array.from({ length: 5 }, (_, i) => <div className="skeleton-card" key={i}><i /><b /><span /></div>)}</div>
    <div className="skeleton-panels">{Array.from({ length: 6 }, (_, i) => <div className="skeleton-panel" key={i}><i /><span /><span /><span /></div>)}</div>
  </div>;
}

function ErrorPanel({ error, retry }) {
  return <div className="state error"><strong>We couldn’t load this section.</strong><span>{error?.message}</span><button onClick={retry}>Try again</button></div>;
}

function PlanSelector({ plans = [], selected, onChange }) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef(null);
  useEffect(() => {
    const close = (event) => { if (!rootRef.current?.contains(event.target)) setOpen(false); };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, []);
  useEffect(() => { setOpen(false); }, [selected?.plan_key]);
  return <div className="plan-picker" ref={rootRef}>
    <span className="plan-picker-label">Selected plan</span>
    <button className={`plan-picker-trigger ${open ? "open" : ""}`} type="button" onClick={() => setOpen((value) => !value)} aria-haspopup="listbox" aria-expanded={open}>
      <span><strong>{selected?.plan_name || "Select a plan"}</strong>{selected && <small>Contract {selected.contract_id} · Plan {selected.plan_id} · Segment {selected.segment_id}</small>}</span>
      <ChevronDown size={18} />
    </button>
    {open && <div className="plan-picker-menu" role="listbox">
      {plans.map((plan) => <button type="button" role="option" aria-selected={plan.plan_key === selected?.plan_key} className={plan.plan_key === selected?.plan_key ? "selected" : ""} key={plan.plan_key} onClick={() => onChange(plan.plan_key)}>
        <span><strong>{plan.plan_name}</strong><small>Contract {plan.contract_id} · Plan {plan.plan_id} · Segment {plan.segment_id}</small></span>
        {plan.plan_key === selected?.plan_key && <Check size={17} />}
      </button>)}
    </div>}
  </div>;
}

function KpiCard({ label, value, detail, tone = "blue", icon: Icon = Activity }) {
  return <article className={`kpi ${tone}`}><div className="kpi-head"><span>{label}</span><i><Icon size={17} strokeWidth={1.8} /></i></div><strong>{value}</strong>{detail && <small>{detail}</small>}</article>;
}

function ModelPerformance({ metadata }) {
  if (!metadata) return <section className="panel model-performance model-loading"><span className="spinner" /><span>Loading model performance…</span></section>;
  const selection = metadata.selection || {};
  const metrics = selection.test_metrics || {};
  const primaryMetrics = [
    ["Overall accuracy", metrics.accuracy, "Share of predictions that were correct"],
    ["Review accuracy", metrics.precision_non_adherent, "Share of review flags that were correct"],
    ["At-risk coverage", metrics.recall_non_adherent, "Share of at-risk members identified"],
    ["Combined quality", metrics.f1, "Balance of review accuracy and coverage"],
    ["Risk ranking", metrics.roc_auc, "Ability to rank higher-risk members first"],
  ];
  const supportingMetrics = [
    ["Balanced accuracy", metrics.balanced_accuracy, "Accuracy across both outcome groups", fmtRate],
    ["Average review precision", metrics.average_precision, "Reliability across risk cutoffs", fmtRate],
    ["Probability error", metrics.brier_score, "Lower values indicate better-calibrated predictions", (value) => Number(value).toFixed(3)],
  ];
  return <section className="panel model-performance">
    <header><div><span className="model-kicker"><BrainCircuit size={15} />Prediction quality check</span><h2>How reliable are the adherence predictions?</h2></div><span className="model-name"><Target size={14} />{titleCase(selection.model || "model")}</span></header>
    <section className="model-primary-block"><div className="model-section-heading light"><span>Prediction performance</span><small>Headline evaluation metrics</small></div><div className="model-primary">{primaryMetrics.map(([label, value, detail]) => <article key={label}><div className="model-ring" style={{ "--metric-value": fmtRate(value) }}><strong>{fmtRate(value)}</strong></div><div className="model-metric-copy"><span>{label}</span><small>{detail}</small></div></article>)}</div></section>
    <div className="model-lower"><section className="model-supporting"><div className="model-section-heading"><span>Supporting quality measures</span><small>Additional checks on model consistency and calibration</small></div><div className="model-secondary">{supportingMetrics.map(([label, value, detail, format]) => <div key={label}><span>{label}</span><strong>{format(value)}</strong><small>{detail}</small></div>)}</div></section><aside className="model-cutoff"><span>Operational setting</span><h3>Predicted-risk decision cutoff</h3><strong>{fmtRate(metadata.threshold)}</strong><p>Predictions at or above this value are classified as elevated non-adherence risk.</p></aside></div>
  </section>;
}

function RiskSummary({ data, title, description }) {
  return <div className="chart-static-summary"><span>{title}</span><p>{description}</p><div>{data.map((row) => <div key={row.category}><i>{row.category}</i><strong>{fmtRate(row.average_risk)}</strong></div>)}</div></div>;
}

function ChartCard({ title, subtitle, summary, note, children, className = "" }) {
  return <article className={`panel chart-panel real-chart ${className}`}><header><div><h3>{title}</h3><p>{subtitle}</p></div><BarChart3 size={17} /></header><div className="chart-canvas">{children}</div>{summary}{note && <p className="chart-note">{note}</p>}</article>;
}

function RiskChart({ data }) {
  const colors = [["#81d2b7", "#359577"], ["#f5d47a", "#dca637"], ["#f7b173", "#e27b39"], ["#ed8792", "#cc4b5a"]];
  return <ChartCard title="Members by predicted adherence risk" subtitle="Number of members in each predicted non-adherence risk band." summary={<RiskSummary data={data} title="Average predicted risk by risk band" description="Mean predicted probability of medication non-adherence among members in each predicted risk band." />} note="Risk bands: Low <25% · Moderate 25–49% · High 50–74% · Very high ≥75%.">
    <ResponsiveContainer width="100%" height="100%"><ReBarChart data={data} margin={{ top: 26, right: 8, left: 0, bottom: 0 }}><defs>{colors.map(([start, end], i) => <linearGradient id={`riskBar${i}`} key={i} x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor={start} /><stop offset="100%" stopColor={end} /></linearGradient>)}</defs><CartesianGrid stroke="#edf0f3" vertical={false} strokeDasharray="4 5" /><XAxis dataKey="category" tickLine={false} axisLine={false} tick={{ fill: "#738096", fontSize: 11 }} /><YAxis tickLine={false} axisLine={false} tick={{ fill: "#8791a2", fontSize: 10 }} width={38} /><Bar dataKey="member_count" name="Member count" radius={[10, 10, 3, 3]} barSize={44}>{data.map((_, i) => <Cell key={i} fill={`url(#riskBar${i})`} />)}<LabelList dataKey="member_count" position="top" formatter={fmtCount} className="chart-value-label" /></Bar></ReBarChart></ResponsiveContainer>
  </ChartCard>;
}

function TierChart({ data }) {
  const prepared = data.map((row) => ({ ...row, tier: `Tier ${row.category}` }));
  const summaryData = prepared.map((row) => ({ ...row, category: row.tier }));
  return <ChartCard title="Members by formulary tier" subtitle="Number of members associated with each formulary tier." summary={<RiskSummary data={summaryData} title="Average predicted risk by formulary tier" description="Mean predicted probability of medication non-adherence among members associated with each formulary tier." />} note="Members may use medications in more than one tier.">
    <ResponsiveContainer width="100%" height="100%"><ReBarChart data={prepared} margin={{ top: 26, right: 8, left: 0, bottom: 0 }}><defs><linearGradient id="tierBar" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#54bea1" /><stop offset="100%" stopColor="#208c70" /></linearGradient></defs><CartesianGrid stroke="#edf0f3" vertical={false} strokeDasharray="4 5" /><XAxis dataKey="tier" tickLine={false} axisLine={false} tick={{ fill: "#738096", fontSize: 11 }} /><YAxis tickLine={false} axisLine={false} tick={{ fill: "#8791a2", fontSize: 10 }} width={38} /><Bar dataKey="member_count" name="Member count" fill="url(#tierBar)" radius={[10, 10, 3, 3]} barSize={56}><LabelList dataKey="member_count" position="top" formatter={fmtCount} className="chart-value-label" /></Bar></ReBarChart></ResponsiveContainer>
  </ChartCard>;
}

function RestrictionChart({ data }) {
  return <ChartCard title="Members by coverage requirement" subtitle="Number of members subject to each formulary coverage requirement." summary={<RiskSummary data={data} title="Average predicted risk by coverage requirement" description="Mean predicted probability of medication non-adherence among members subject to each formulary coverage requirement." />} note="Members may be subject to more than one requirement.">
    <ResponsiveContainer width="100%" height="100%"><ReBarChart data={data} layout="vertical" margin={{ top: 6, right: 48, left: 14, bottom: 0 }}><defs><linearGradient id="restrictionBar" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stopColor="#68b9de" /><stop offset="100%" stopColor="#2989b7" /></linearGradient></defs><CartesianGrid stroke="#edf0f3" horizontal={false} strokeDasharray="4 5" /><XAxis type="number" hide /><YAxis type="category" dataKey="category" width={115} tickLine={false} axisLine={false} tick={{ fill: "#59657a", fontSize: 10 }} /><Bar dataKey="member_count" name="Members" fill="url(#restrictionBar)" radius={[0, 10, 10, 0]} barSize={18}><LabelList dataKey="member_count" position="right" formatter={fmtCount} className="chart-value-label" /></Bar></ReBarChart></ResponsiveContainer>
  </ChartCard>;
}

function CostChart({ data }) {
  const total = data.reduce((sum, row) => sum + Number(row.member_count || 0), 0);
  const colors = ["#85d2bb", "#3ca27f", "#e8ae43", "#d95b68"];
  return <ChartCard title="Members by medication cost pressure" subtitle="Number of members in each medication cost-pressure band." className="donut-card" summary={<RiskSummary data={data} title="Average predicted risk by medication cost pressure" description="Mean predicted probability of medication non-adherence among members in each medication cost-pressure band." />} note="Cost bands: Low <25% · Moderate 25–49% · High 50–74% · Very high ≥75%.">
    <div className="donut-layout"><div className="donut-wrap"><ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={data} dataKey="member_count" nameKey="category" innerRadius="62%" outerRadius="88%" paddingAngle={3} cornerRadius={7} stroke="#fff" strokeWidth={3}>{data.map((_, i) => <Cell key={i} fill={colors[i] || colors[0]} />)}</Pie></PieChart></ResponsiveContainer><div className="donut-center"><strong>{fmtCount(total)}</strong><span>members</span></div></div><div className="chart-legend">{data.map((row, i) => <div key={row.category}><i style={{ background: colors[i] }} /><span>{row.category}</span><strong>{fmtCount(row.member_count)}</strong></div>)}</div></div>
  </ChartCard>;
}

function PharmacyChart({ data }) {
  return <ChartCard title="Members by pharmacy network status" subtitle="Number of members using preferred or non-preferred pharmacies." summary={<RiskSummary data={data} title="Average predicted risk by pharmacy network status" description="Mean predicted probability of medication non-adherence among members using each pharmacy network type." />} note="Members may use both pharmacy types.">
    <ResponsiveContainer width="100%" height="100%"><ReBarChart data={data} margin={{ top: 26, right: 6, left: -18, bottom: 0 }}><defs><linearGradient id="pharmacyBar" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#9185ee" /><stop offset="100%" stopColor="#5c50c7" /></linearGradient></defs><CartesianGrid stroke="#edf0f3" vertical={false} strokeDasharray="4 5" /><XAxis dataKey="category" tickLine={false} axisLine={false} tick={{ fill: "#738096", fontSize: 11 }} /><YAxis tickLine={false} axisLine={false} tick={{ fill: "#8791a2", fontSize: 10 }} /><Bar dataKey="member_count" name="Members" fill="url(#pharmacyBar)" radius={[10, 10, 3, 3]} barSize={74}><LabelList dataKey="member_count" position="top" formatter={fmtCount} className="chart-value-label" /></Bar></ReBarChart></ResponsiveContainer>
  </ChartCard>;
}

function MedicationName({ value }) {
  return <div className="medication-name"><i><Pill size={14} strokeWidth={1.9} /></i><span>{value}</span></div>;
}

function metricTone(value) {
  const numeric = Number(value);
  if (numeric >= 0.75) return "very-high";
  if (numeric >= 0.5) return "high";
  if (numeric >= 0.25) return "moderate";
  return "low";
}

function PercentMetric({ value, tone }) {
  const numeric = Math.max(0, Math.min(Number(value) || 0, 1));
  return <div className={`percent-metric ${tone || metricTone(numeric)}`}>
    <strong>{fmtRate(numeric)}</strong><span aria-hidden="true"><i style={{ width: `${numeric * 100}%` }} /></span>
  </div>;
}

function ExposurePill({ value }) {
  const numeric = Number(value) || 0;
  return numeric > 0
    ? <span className="exposure-pill active">{fmtRate(numeric)}</span>
    : <span className="exposure-pill is-zero">—</span>;
}

function DataTable({ columns, rows, empty = "No matching results." }) {
  if (!rows?.length) return <div className="empty">{empty}</div>;
  return <div className="table-wrap"><table><thead><tr>{columns.map((c) => <th className={`col-${c.key}`} key={c.key}><abbr title={c.description || c.label}>{c.label}</abbr></th>)}</tr></thead>
    <tbody>{rows.map((row, index) => <tr key={row.rxcui || row.prescriber_id || index}>{columns.map((c) => <td className={`col-${c.key}`} key={c.key}>{c.render ? c.render(row[c.key], row) : row[c.key]}</td>)}</tr>)}</tbody>
  </table></div>;
}

function PlanOverview({ planKey }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [reload, setReload] = useState(0);
  const [showMedicationProfile, setShowMedicationProfile] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    setData(null); setError(null); setShowMedicationProfile(false);
    Promise.all([
      apiRequest(endpoints.summary(planKey), controller.signal),
      apiRequest(endpoints.analytics("risk-distribution", planKey), controller.signal),
      apiRequest(endpoints.analytics("tiers", planKey), controller.signal),
      apiRequest(endpoints.analytics("restrictions", planKey), controller.signal),
      apiRequest(endpoints.analytics("pharmacies", planKey), controller.signal),
      apiRequest(endpoints.analytics("cost-burden", planKey), controller.signal),
      apiRequest(endpoints.analytics("medications", planKey, "&limit=12"), controller.signal),
      apiRequest(endpoints.analytics("opportunities", planKey, "&limit=10"), controller.signal),
    ]).then(([summary, risk, tiers, restrictions, pharmacies, costs, meds, opportunities]) =>
      setData({ summary: summary.data, risk: risk.data, tiers: tiers.data, restrictions: restrictions.data, pharmacies: pharmacies.data, costs: costs.data, meds: meds.data, opportunities: opportunities.data })
    ).catch((e) => e.name !== "AbortError" && setError(e));
    return () => controller.abort();
  }, [planKey, reload]);
  if (error) return <ErrorPanel error={error} retry={() => setReload((x) => x + 1)} />;
  if (!data) return <DashboardSkeleton />;
  const s = data.summary;
  const medColumns = [
    { key: "drug_name", label: "Medication", render: (value) => <MedicationName value={value} /> }, { key: "exposed_members", label: "Members exposed", render: (value) => <span className="count-cell">{fmtCount(value)}</span> },
    { key: "average_risk", label: "Avg. predicted risk", description: "Average model-predicted likelihood of non-adherence", render: (value) => <PercentMetric value={value} /> }, { key: "average_cost_burden", label: "Avg. cost pressure", render: (value) => <PercentMetric value={value} tone="cost" /> },
    { key: "prior_authorization_rate", label: "Prior auth", render: (value) => <ExposurePill value={value} /> }, { key: "step_therapy_rate", label: "Step therapy", render: (value) => <ExposurePill value={value} /> }, { key: "quantity_limit_rate", label: "Quantity limit", render: (value) => <ExposurePill value={value} /> },
  ];
  const opportunityColumns = [
    { key: "rank", label: "Rank", render: (value) => <span className="rank-badge">{value}</span> },
    { key: "drug_name", label: "Medication", render: (value) => <MedicationName value={value} /> },
    { key: "exposed_members", label: "Members", render: (value) => <span className="count-cell">{fmtCount(value)}</span> },
    { key: "review_score", label: "Priority score", description: "Medication review priority score", render: (value) => <PriorityScore value={value} /> },
    { key: "review_factors", label: "Review summary", render: (_, row) => <ReviewFactors row={row} /> },
  ];
  const reviewRows = data.opportunities
    .filter((row) => Number(row.review_score) >= REVIEW_CUTOFF)
    .slice(0, 5)
    .map((row, index) => ({ ...row, rank: index + 1 }));
  const accessExposureRows = [
    ["Prior authorization", s.prior_authorization_exposure],
    ["Step therapy", s.step_therapy_exposure],
    ["Quantity limits", s.quantity_limit_exposure],
    ["Nonpreferred pharmacy use", s.nonpreferred_pharmacy_exposure],
  ].sort((a, b) => Number(b[1]) - Number(a[1]));
  return <>
    <section className="dashboard-group"><header className="group-heading"><div><h2>Adherence outlook</h2><p>Population risk profile for the selected plan.</p></div></header>
      <section className="kpi-grid">
        <KpiCard label="Members evaluated" value={fmtCount(s.total_members_scored)} detail="Members included for this plan" icon={Database} />
        <KpiCard label="Members above risk cutoff" value={fmtCount(s.members_flagged_at_risk)} detail="Members whose predicted non-adherence risk meets or exceeds the decision cutoff" tone="red" icon={AlertTriangle} />
        <KpiCard label="Share above risk cutoff" value={fmtPercent(s.percentage_flagged_at_risk)} detail="Percentage of evaluated members meeting the decision cutoff" tone="orange" icon={Gauge} />
        <KpiCard label="Average predicted non-adherence risk" value={fmtRate(s.average_predicted_risk)} detail="Average model prediction across members" tone="purple" icon={Activity} />
        <KpiCard label="Average medication cost pressure" value={fmtRate(s.average_cost_burden)} detail="Average member cost indicator" tone="green" icon={WalletCards} />
      </section>
      <section className="chart-grid outlook-charts"><RiskChart data={data.risk} /><TierChart data={data.tiers} /></section>
    </section>
    <section className="dashboard-group"><header className="group-heading"><div><h2>Access and affordability</h2><p>Coverage, cost, and pharmacy conditions associated with member adherence risk.</p></div></header><section className="chart-grid access-charts">
      <RestrictionChart data={data.restrictions} /><CostChart data={data.costs} /><PharmacyChart data={data.pharmacies} />
      <article className="panel exposure-panel featured-exposure"><span className="exposure-kicker">ACCESS EXPOSURE SUMMARY</span><h3>Plan access exposure ranking</h3><p>Average member-level exposure to coverage and pharmacy access conditions, ordered from highest to lowest.</p>
        <div className="exposure-ranking-list">{accessExposureRows.map(([label,value], index) =>
          <div className={`meter ${index === 0 ? "leading" : ""}`} key={label}><span><b className="exposure-rank">{index + 1}</b>{label}</span><strong>{fmtRate(value)}</strong><div><i style={{width:fmtRate(value)}} /></div></div>)}</div>
        <p className="exposure-definition">Measure: Average member-level medication exposure rate, not the percentage of distinct members affected.</p>
      </article>
    </section></section>
    <section className="dashboard-group"><header className="group-heading"><div><h2>Medication review priorities</h2><p>Highest-priority medications meeting the operational review cutoff.</p></div></header>
      <section className="panel priority-panel"><header><div><span className="report-kicker">FORMULARY REVIEW REPORT</span><h3>Top formulary review opportunities</h3><p>Ranked by priority score with the principal factors supporting review.</p></div><div className="report-meta"><strong>{reviewRows.length}</strong><span>medications shown</span><small>Review cutoff ≥ {(REVIEW_CUTOFF * 100).toFixed(0)}</small></div></header><DataTable columns={opportunityColumns} rows={reviewRows} empty="No medications meet the current review cutoff." /></section>
      <section className={`panel medication-explorer ${showMedicationProfile ? "open" : ""}`}>
        <header><div><h3>Medication profile</h3><p>Detailed member reach, predicted adherence risk, cost pressure, and coverage requirements.</p></div><button type="button" onClick={() => setShowMedicationProfile((value) => !value)} aria-expanded={showMedicationProfile} aria-controls="medication-profile-table">{showMedicationProfile ? "Hide medications" : `View all medications (${data.meds.length})`}<ChevronDown size={16} aria-hidden="true" /></button></header>
        {showMedicationProfile && <div className="medication-explorer-content" id="medication-profile-table"><DataTable columns={medColumns} rows={data.meds} /></div>}
      </section>
    </section>
  </>;
}

function PrescriberAnalysis({ planKey }) {
  const [prescribers, setPrescribers] = useState(null);
  const [selected, setSelected] = useState("");
  const [detail, setDetail] = useState(null);
  const [rowsLoading, setRowsLoading] = useState(false);
  const [view, setView] = useState("medications");
  const [search, setSearch] = useState("");
  const [error, setError] = useState(null);
  const previousDetailKey = useRef("");
  useEffect(() => {
    const controller = new AbortController(); setPrescribers(null); setSelected(""); setError(null);
    apiRequest(endpoints.prescribers(planKey), controller.signal).then((body) => { setPrescribers(body.data); setSelected(body.data[0]?.prescriber_id || ""); }).catch((e) => e.name !== "AbortError" && setError(e));
    return () => controller.abort();
  }, [planKey]);
  useEffect(() => {
    if (!selected) { setDetail(null); setRowsLoading(false); return; }
    const controller = new AbortController();
    const detailKey = `${planKey}|${selected}`;
    const identityChanged = previousDetailKey.current !== detailKey;
    previousDetailKey.current = detailKey;
    if (identityChanged) setDetail(null);
    else setRowsLoading(true);
    setError(null);
    Promise.all([
      apiRequest(endpoints.prescriberSummary(selected, planKey), controller.signal),
      apiRequest(endpoints.prescriberMedications(selected, planKey, view === "opportunities"), controller.signal),
    ]).then(([summary, rows]) => setDetail({ summary: summary.data, rows: rows.data })).catch((e) => e.name !== "AbortError" && setError(e)).finally(() => { if (!controller.signal.aborted) setRowsLoading(false); });
    return () => controller.abort();
  }, [selected, planKey, view]);
  if (error) return <ErrorPanel error={error} retry={() => window.location.reload()} />;
  if (!prescribers) return <Loading label="Loading prescriber analytics" />;
  const filteredPrescribers = prescribers.filter((p) => `${p.prescriber_display_name} ${p.prescriber_id} ${p.specialty}`.toLowerCase().includes(search.toLowerCase()));
  const columns = [
    { key: "drug_name", label: "Medication", render: (value) => <MedicationName value={value} /> }, { key: "distinct_member_count", label: "Members", description: "Distinct members using this medication", render: (value) => <span className="count-cell">{fmtCount(value)}</span> },
    { key: "average_tier", label: "Avg. tier", description: "Average formulary tier", render: (v) => Number(v).toFixed(1) }, { key: "average_synthetic_cost_burden", label: "Avg. cost pressure", render: fmtRate },
    { key: "restrictions", label: "Coverage requirements", render: (_, row) => <RestrictionBadges row={row} /> },
    { key: "formulary_review_flag", label: "Review decision", render: (v, row) => <ReviewStatus flagged={v} row={row} /> },
  ];
  return <>
    <section className="prescriber-layout">
      <aside className="panel prescriber-list"><header><h3>Prescribers</h3><p>{prescribers.length} available for this plan</p><label className="prescriber-search"><Search size={15} /><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search name, ID or specialty" /></label></header>
        <div className="prescriber-scroll">{filteredPrescribers.map((p) => <button className={selected === p.prescriber_id ? "active" : ""} key={p.prescriber_id} onClick={() => setSelected(p.prescriber_id)}>
          <span><strong>{displayPrescriber(p.prescriber_display_name)}</strong><small>{p.specialty} · {p.prescriber_id}</small></span><b>{p.assignment_exposure_count}</b>
        </button>)}{!filteredPrescribers.length && <div className="prescriber-empty">No prescribers match your search.</div>}</div>
      </aside>
      <div className="prescriber-main">
        {!detail ? <Loading label="Loading prescriber detail" /> : <>
          <section className="profile-card">
            <div className="profile-identity"><div className="profile-avatar"><Stethoscope size={23} strokeWidth={1.8} /></div><div><span className="eyebrow">Prescriber formulary profile</span><h2>{displayPrescriber(detail.summary.prescriber_display_name)}</h2><div className="profile-meta"><span>{detail.summary.specialty}</span><span><MapPin size={12} />{detail.summary.prescriber_region}</span><span>{detail.summary.prescriber_id}</span></div></div></div>
            <div className="profile-stats"><span><i>Members</i><strong>{fmtCount(detail.summary.distinct_member_count)}</strong><small>People receiving medications</small></span><span><i>Medication records</i><strong>{fmtCount(detail.summary.assignment_exposure_count)}</strong><small>Total records reviewed</small></span><span><i>Medications</i><strong>{detail.summary.distinct_drug_count}</strong><small>Unique products</small></span><span><i>Average tier</i><strong>{Number(detail.summary.average_tier).toFixed(1)}</strong><small>For the selected plan</small></span></div>
          </section>
          <div className="segmented"><button className={view === "medications" ? "active" : ""} onClick={() => setView("medications")}>All medications</button><button className={view === "opportunities" ? "active" : ""} onClick={() => setView("opportunities")}>Top review priorities</button></div>
          <section className={`panel table-panel prescriber-results ${rowsLoading ? "rows-updating" : ""}`} aria-busy={rowsLoading}><DataTable columns={columns} rows={view === "opportunities" ? detail.rows.slice(0, 5) : detail.rows} empty={view === "opportunities" ? "No medications meet the review criteria for this prescriber." : "No medication exposure found."} /></section>
        </>}
      </div>
    </section>
  </>;
}

export default function App() {
  const [plans, setPlans] = useState(null);
  const [modelMetadata, setModelMetadata] = useState(null);
  const [modelError, setModelError] = useState(null);
  const [planKey, setPlanKey] = useState("");
  const [page, setPage] = useState("overview");
  const [error, setError] = useState(null);
  useEffect(() => {
    apiRequest(endpoints.plans).then((body) => { setPlans(body.data); setPlanKey(body.data[0]?.plan_key || ""); }).catch(setError);
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    apiRequest(endpoints.modelMetadata, controller.signal).then((body) => setModelMetadata(body.data)).catch((error) => { if (error.name !== "AbortError") setModelError(error); });
    return () => controller.abort();
  }, []);
  const plan = useMemo(() => plans?.find((p) => p.plan_key === planKey), [plans, planKey]);
  const pageContent = {
    overview: ["Plan adherence and formulary overview", "Understand predicted adherence risk, the plan factors connected to it, and where action is needed."],
    prescribers: ["Prescriber medication review", "Identify medications that may need attention and see the specific reason for each review decision."],
    model: ["Prediction quality", "Understand how reliably the model identifies members who may need adherence support."],
  }[page];
  return <div className="app-shell">
    <aside className="sidebar"><span className="nav-section-label">Workspace</span>
      <nav><button className={page === "overview" ? "active" : ""} onClick={() => setPage("overview")}><span><LayoutDashboard size={17} /></span>Plan overview</button><button className={page === "prescribers" ? "active" : ""} onClick={() => setPage("prescribers")}><span><Stethoscope size={17} /></span>Prescriber review</button><button className={page === "model" ? "active" : ""} onClick={() => setPage("model")}><span><BrainCircuit size={17} /></span>Prediction quality</button></nav>
      <div className="sidebar-foot"><span className="status-dot" />Reporting data ready</div>
    </aside>
    <main><header className="topbar"><div><span className="eyebrow">Pharmacy Formulary Optimization and Adherence Assistant</span><h1>{pageContent[0]}</h1><p>{pageContent[1]}</p></div>
      {page !== "model" && <PlanSelector plans={plans || []} selected={plan} onChange={setPlanKey} />}
    </header>
    <div className={`content ${page === "model" ? "model-page" : ""}`}>{error ? <ErrorPanel error={error} retry={() => window.location.reload()} /> : page === "model" ? modelError ? <ErrorPanel error={modelError} retry={() => window.location.reload()} /> : <ModelPerformance metadata={modelMetadata} /> : !planKey ? <DashboardSkeleton /> : page === "overview" ? <PlanOverview planKey={planKey} /> : <PrescriberAnalysis planKey={planKey} />}</div>
    </main>
  </div>;
}
