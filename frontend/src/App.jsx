import { useEffect, useMemo, useRef, useState } from "react";
import { apiRequest, endpoints } from "./api";
import {
  Activity, AlertTriangle, BarChart3, BrainCircuit, Check, ChevronDown, Database, Gauge,
  LayoutDashboard, MapPin, Pill, Search, Stethoscope, Target, WalletCards,
} from "lucide-react";
import {
  Bar, BarChart as ReBarChart, CartesianGrid, Cell, ComposedChart,
  Line, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";

const fmtCount = (value = 0) => new Intl.NumberFormat("en-US").format(value);
const fmtRate = (value = 0) => `${(Number(value) * 100).toFixed(1)}%`;
const fmtPercent = (value = 0) => `${Number(value).toFixed(1)}%`;
const titleCase = (value) => String(value).replaceAll("_", " ").replace(/\b\w/g, (c) => c.toUpperCase());
const displayPrescriber = (value = "") => value.replace(/^Synthetic\s+/i, "");
const readableReason = (value = "") => titleCase(value.replace("SYNTHETIC_", ""));

function RestrictionBadges({ row }) {
  const active = [
    ["PA", row.prior_authorization_rate],
    ["ST", row.step_therapy_rate],
    ["QL", row.quantity_limit_rate],
  ].filter(([, value]) => Number(value) > 0);
  return active.length
    ? <div className="signal-badges">{active.map(([label]) => <span key={label}>{label}</span>)}</div>
    : <span className="muted">None</span>;
}

function ReviewStatus({ flagged, reasons = [] }) {
  const cleanReasons = reasons.map(readableReason);
  return <div className="review-cell">
    <span className={`status ${flagged ? "review" : "standard"}`}>{flagged ? "Review" : "Standard"}</span>
    {flagged && <small title={cleanReasons.join(", ")}>{cleanReasons.length} signal{cleanReasons.length === 1 ? "" : "s"}</small>}
  </div>;
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
    ["Accuracy", metrics.accuracy, "Correct classifications"],
    ["Precision", metrics.precision_non_adherent, "Flag reliability"],
    ["Recall", metrics.recall_non_adherent, "At-risk cases identified"],
    ["F1 score", metrics.f1, "Precision–recall balance"],
    ["ROC AUC", metrics.roc_auc, "Ranking discrimination"],
  ];
  const secondaryMetrics = [
    ["Balanced accuracy", metrics.balanced_accuracy, "Higher is better", fmtRate],
    ["Average precision", metrics.average_precision, "Higher is better", fmtRate],
    ["Brier score", metrics.brier_score, "Lower is better", (value) => Number(value).toFixed(3)],
    ["Risk-flag threshold", metadata.threshold, "Probability required to flag", fmtRate],
  ];
  return <section className="panel model-performance">
    <header><div><span className="model-kicker"><BrainCircuit size={15} />Selected model evaluation</span><h2>Model performance</h2><p>Held-out evaluation metrics for the active {titleCase(selection.model || "model")}</p></div><span className="model-name"><Target size={14} />{titleCase(selection.model || "model")}</span></header>
    <div className="model-primary">{primaryMetrics.map(([label, value, detail]) => <article key={label}><div className="model-ring" style={{ "--metric-value": fmtRate(value) }}><strong>{fmtRate(value)}</strong></div><div className="model-metric-copy"><span>{label}</span><small>{detail}</small></div></article>)}</div>
    <div className="model-secondary">{secondaryMetrics.map(([label, value, detail, format]) => <div key={label}><span>{label}</span><strong>{format(value)}</strong><small>{detail}</small></div>)}</div>
  </section>;
}

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  const row = payload[0]?.payload;
  const hasRiskSeries = payload.some((item) => item.dataKey === "risk_pct");
  return <div className="chart-tooltip"><strong>{label}</strong>{payload.map((item) => <span key={item.dataKey}><i style={{ background: item.color }} />{item.name}: {item.dataKey === "risk_pct" ? `${Number(item.value).toFixed(1)}%` : fmtCount(item.value)}</span>)}{!hasRiskSeries && row?.average_risk != null && <span><i style={{ background: "#6c63d9" }} />Mean risk: {fmtRate(row.average_risk)}</span>}</div>;
}

function ChartCard({ title, subtitle, note, children, className = "" }) {
  return <article className={`panel chart-panel real-chart ${className}`}><header><div><h3>{title}</h3><p>{subtitle}</p></div><BarChart3 size={17} /></header><div className="chart-canvas">{children}</div>{note && <p className="chart-note">{note}</p>}</article>;
}

function RiskChart({ data }) {
  const colors = [["#81d2b7", "#359577"], ["#f5d47a", "#dca637"], ["#f7b173", "#e27b39"], ["#ed8792", "#cc4b5a"]];
  return <ChartCard title="Predicted-risk distribution" subtitle="Scored scenarios by risk band">
    <ResponsiveContainer width="100%" height="100%"><ReBarChart data={data} margin={{ top: 8, right: 6, left: -18, bottom: 0 }}><defs>{colors.map(([start, end], i) => <linearGradient id={`riskBar${i}`} key={i} x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor={start} /><stop offset="100%" stopColor={end} /></linearGradient>)}</defs><CartesianGrid stroke="#edf0f3" vertical={false} strokeDasharray="4 5" /><XAxis dataKey="category" tickLine={false} axisLine={false} tick={{ fill: "#738096", fontSize: 11 }} /><YAxis tickLine={false} axisLine={false} tick={{ fill: "#8791a2", fontSize: 10 }} /><Tooltip cursor={{ fill: "#f3f7f6" }} content={<ChartTooltip />} /><Bar dataKey="member_count" name="Scenarios" radius={[10, 10, 3, 3]} barSize={44}>{data.map((_, i) => <Cell key={i} fill={`url(#riskBar${i})`} />)}</Bar></ReBarChart></ResponsiveContainer>
  </ChartCard>;
}

function TierChart({ data }) {
  const prepared = data.map((row) => ({ ...row, tier: `Tier ${row.category}`, risk_pct: row.average_risk * 100 }));
  return <ChartCard title="Medication-tier exposure" subtitle="Member exposure and mean predicted risk" note="Members may appear in more than one tier.">
    <ResponsiveContainer width="100%" height="100%"><ComposedChart data={prepared} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}><defs><linearGradient id="tierBar" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#54bea1" /><stop offset="100%" stopColor="#208c70" /></linearGradient><filter id="lineGlow"><feDropShadow dx="0" dy="3" stdDeviation="3" floodColor="#6c63d9" floodOpacity=".25" /></filter></defs><CartesianGrid stroke="#edf0f3" vertical={false} strokeDasharray="4 5" /><XAxis dataKey="tier" tickLine={false} axisLine={false} tick={{ fill: "#738096", fontSize: 11 }} /><YAxis yAxisId="count" tickLine={false} axisLine={false} tick={{ fill: "#8791a2", fontSize: 10 }} /><YAxis yAxisId="risk" orientation="right" domain={[0, 100]} hide /><Tooltip cursor={{ fill: "#f3f7f6" }} content={<ChartTooltip />} /><Bar yAxisId="count" dataKey="member_count" name="Members exposed" fill="url(#tierBar)" radius={[10, 10, 3, 3]} barSize={56} /><Line yAxisId="risk" type="monotone" dataKey="risk_pct" name="Mean risk" stroke="#6c63d9" strokeWidth={3} dot={{ r: 5, fill: "#fff", stroke: "#6c63d9", strokeWidth: 2.5 }} activeDot={{ r: 7 }} style={{ filter: "url(#lineGlow)" }} /></ComposedChart></ResponsiveContainer>
  </ChartCard>;
}

function RestrictionChart({ data }) {
  return <ChartCard title="Utilization-management exposure" subtitle="Distinct members with PA, ST or QL" note="Restriction categories may overlap.">
    <ResponsiveContainer width="100%" height="100%"><ReBarChart data={data} layout="vertical" margin={{ top: 6, right: 12, left: 8, bottom: 0 }}><defs><linearGradient id="restrictionBar" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stopColor="#68b9de" /><stop offset="100%" stopColor="#2989b7" /></linearGradient></defs><CartesianGrid stroke="#edf0f3" horizontal={false} strokeDasharray="4 5" /><XAxis type="number" hide /><YAxis type="category" dataKey="category" width={105} tickLine={false} axisLine={false} tick={{ fill: "#59657a", fontSize: 10 }} /><Tooltip cursor={{ fill: "#f3f7f6" }} content={<ChartTooltip />} /><Bar dataKey="member_count" name="Members exposed" fill="url(#restrictionBar)" radius={[0, 10, 10, 0]} barSize={18} /></ReBarChart></ResponsiveContainer>
  </ChartCard>;
}

function CostChart({ data }) {
  const total = data.reduce((sum, row) => sum + Number(row.member_count || 0), 0);
  const colors = ["#85d2bb", "#3ca27f", "#e8ae43", "#d95b68"];
  return <ChartCard title="Cost-burden distribution" subtitle="Scored scenarios by burden band" className="donut-card">
    <div className="donut-layout"><div className="donut-wrap"><ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={data} dataKey="member_count" nameKey="category" innerRadius="62%" outerRadius="88%" paddingAngle={3} cornerRadius={7} stroke="#fff" strokeWidth={3}>{data.map((_, i) => <Cell key={i} fill={colors[i] || colors[0]} />)}</Pie><Tooltip content={<ChartTooltip />} /></PieChart></ResponsiveContainer><div className="donut-center"><strong>{fmtCount(total)}</strong><span>scenarios</span></div></div><div className="chart-legend">{data.map((row, i) => <div key={row.category}><i style={{ background: colors[i] }} /><span>{row.category}</span><strong>{fmtCount(row.member_count)}</strong></div>)}</div></div>
  </ChartCard>;
}

function PharmacyChart({ data }) {
  return <ChartCard title="Pharmacy preference exposure" subtitle="Distinct members by pharmacy category" note="Members may appear in both categories.">
    <ResponsiveContainer width="100%" height="100%"><ReBarChart data={data} margin={{ top: 8, right: 6, left: -18, bottom: 0 }}><defs><linearGradient id="pharmacyBar" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#9185ee" /><stop offset="100%" stopColor="#5c50c7" /></linearGradient></defs><CartesianGrid stroke="#edf0f3" vertical={false} strokeDasharray="4 5" /><XAxis dataKey="category" tickLine={false} axisLine={false} tick={{ fill: "#738096", fontSize: 11 }} /><YAxis tickLine={false} axisLine={false} tick={{ fill: "#8791a2", fontSize: 10 }} /><Tooltip cursor={{ fill: "#f5f3ff" }} content={<ChartTooltip />} /><Bar dataKey="member_count" name="Members exposed" fill="url(#pharmacyBar)" radius={[10, 10, 3, 3]} barSize={74} /></ReBarChart></ResponsiveContainer>
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
  useEffect(() => {
    const controller = new AbortController();
    setData(null); setError(null);
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
    { key: "average_risk", label: "Mean risk", render: (value) => <PercentMetric value={value} /> }, { key: "average_cost_burden", label: "Mean cost burden", render: (value) => <PercentMetric value={value} tone="cost" /> },
    { key: "prior_authorization_rate", label: "PA", render: (value) => <ExposurePill value={value} /> }, { key: "step_therapy_rate", label: "ST", render: (value) => <ExposurePill value={value} /> }, { key: "quantity_limit_rate", label: "QL", render: (value) => <ExposurePill value={value} /> },
  ];
  const opportunityColumns = [
    { key: "drug_name", label: "Medication for review", render: (value) => <MedicationName value={value} /> }, { key: "exposed_members", label: "Members exposed", render: (value) => <span className="count-cell">{fmtCount(value)}</span> },
    { key: "average_risk", label: "Mean risk", render: (value) => <PercentMetric value={value} /> }, { key: "restriction_exposure", label: "Restriction exposure", render: (value) => <PercentMetric value={value} tone="restriction" /> },
    { key: "review_score", label: "Review score", render: (value) => <PercentMetric value={value} tone="score" /> },
  ];
  return <>
    <section className="kpi-grid">
      <KpiCard label="Scored scenarios" value={fmtCount(s.total_members_scored)} detail="Member-plan scenarios evaluated" icon={Database} />
      <KpiCard label="Scenarios flagged" value={fmtCount(s.members_flagged_at_risk)} detail="At the model decision threshold" tone="red" icon={AlertTriangle} />
      <KpiCard label="Flagged scenario rate" value={fmtPercent(s.percentage_flagged_at_risk)} detail="Share of all scored scenarios" tone="orange" icon={Gauge} />
      <KpiCard label="Mean non-adherence risk" value={fmtRate(s.average_predicted_risk)} detail="Average predicted probability" tone="purple" icon={Activity} />
      <KpiCard label="Mean cost-burden score" value={fmtRate(s.average_cost_burden)} detail="Average member-plan burden" tone="green" icon={WalletCards} />
    </section>
    <section className="chart-grid">
      <RiskChart data={data.risk} />
      <TierChart data={data.tiers} />
      <RestrictionChart data={data.restrictions} />
      <CostChart data={data.costs} />
      <PharmacyChart data={data.pharmacies} />
      <article className="panel exposure-panel"><h3>Mean exposure rates</h3><p>Average member-plan feature values</p>
        {[['Prior authorization',s.prior_authorization_exposure],['Step therapy',s.step_therapy_exposure],['Quantity limit',s.quantity_limit_exposure],['Nonpreferred pharmacy',s.nonpreferred_pharmacy_exposure]].map(([label,value]) =>
          <div className="meter" key={label}><span>{label}</span><strong>{fmtRate(value)}</strong><div><i style={{width:fmtRate(value)}} /></div></div>)}
      </article>
    </section>
    <section className="panel table-panel"><header><div><h3>Medication analysis</h3><p>Exposure and formulary conditions for the selected plan</p></div></header><DataTable columns={medColumns} rows={data.meds} /></section>
    <section className="panel table-panel"><header><div><h3>Formulary review opportunities</h3><p>Ranked using backend risk, cost, restriction and pharmacy signals</p></div></header><DataTable columns={opportunityColumns} rows={data.opportunities} /></section>
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
    { key: "drug_name", label: "Medication", render: (value) => <MedicationName value={value} /> }, { key: "distinct_member_count", label: "Exposed", description: "Distinct members exposed", render: (value) => <span className="count-cell">{fmtCount(value)}</span> },
    { key: "average_tier", label: "Tier", description: "Mean formulary tier", render: (v) => Number(v).toFixed(1) }, { key: "average_synthetic_cost_burden", label: "Cost", description: "Mean cost-burden score", render: fmtRate },
    { key: "restrictions", label: "UM", description: "Utilization management: PA, ST and QL", render: (_, row) => <RestrictionBadges row={row} /> },
    { key: "prescriber_drug_share", label: "Share", description: "Share of this prescriber's medication assignments", render: fmtRate },
    { key: "formulary_review_flag", label: "Status", description: "Formulary review status", render: (v, row) => <ReviewStatus flagged={v} reasons={row.review_reason_codes} /> },
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
            <div className="profile-stats"><span><i>Members</i><strong>{fmtCount(detail.summary.distinct_member_count)}</strong><small>Distinct exposure</small></span><span><i>Assignments</i><strong>{fmtCount(detail.summary.assignment_exposure_count)}</strong><small>Medication records</small></span><span><i>Drugs</i><strong>{detail.summary.distinct_drug_count}</strong><small>Distinct RxCUIs</small></span><span><i>Mean tier</i><strong>{Number(detail.summary.average_tier).toFixed(1)}</strong><small>Selected plan</small></span></div>
          </section>
          <div className="segmented"><button className={view === "medications" ? "active" : ""} onClick={() => setView("medications")}>All medications</button><button className={view === "opportunities" ? "active" : ""} onClick={() => setView("opportunities")}>Review opportunities</button></div>
          <section className={`panel table-panel prescriber-results ${rowsLoading ? "rows-updating" : ""}`} aria-busy={rowsLoading}><DataTable columns={columns} rows={detail.rows} empty={view === "opportunities" ? "No review opportunities for this prescriber and plan." : "No medication exposure found."} /></section>
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
    overview: ["Plan performance overview", "Explore risk, access, cost and medication signals for the selected plan."],
    prescribers: ["Prescriber formulary analysis", "Review prescriber medication exposure and plan-specific formulary conditions."],
    model: ["Model performance", "Review evaluation metrics for the active adherence-risk model."],
  }[page];
  return <div className="app-shell">
    <aside className="sidebar"><div className="brand"><div className="brand-mark">Rx</div><div><strong>Pharmacy Formulary</strong><span>Optimization & Adherence Assistant</span></div></div><span className="nav-section-label">Workspace</span>
      <nav><button className={page === "overview" ? "active" : ""} onClick={() => setPage("overview")}><span><LayoutDashboard size={17} /></span>Plan overview</button><button className={page === "prescribers" ? "active" : ""} onClick={() => setPage("prescribers")}><span><Stethoscope size={17} /></span>Prescriber analysis</button><button className={page === "model" ? "active" : ""} onClick={() => setPage("model")}><span><BrainCircuit size={17} /></span>Model performance</button></nav>
      <div className="sidebar-foot"><span className="status-dot" />API connected</div>
    </aside>
    <main><header className="topbar"><div><span className="eyebrow">Pharmacy Formulary Optimization and Adherence Assistant</span><h1>{pageContent[0]}</h1><p>{pageContent[1]}</p></div>
      {page !== "model" && <PlanSelector plans={plans || []} selected={plan} onChange={setPlanKey} />}
    </header>
    <div className={`content ${page === "model" ? "model-page" : ""}`}>{error ? <ErrorPanel error={error} retry={() => window.location.reload()} /> : page === "model" ? modelError ? <ErrorPanel error={modelError} retry={() => window.location.reload()} /> : <ModelPerformance metadata={modelMetadata} /> : !planKey ? <DashboardSkeleton /> : page === "overview" ? <PlanOverview planKey={planKey} /> : <PrescriberAnalysis planKey={planKey} />}</div>
    </main>
  </div>;
}
