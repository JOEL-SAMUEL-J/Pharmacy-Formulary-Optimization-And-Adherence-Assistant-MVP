# Pharmacy Formulary Optimization and Adherence Assistant

## Simplified System Architecture — Diagram Explanation

**Architecture:** Data Sources → Python Data and ML Pipeline → MySQL Data Layer → FastAPI Backend → React Frontend → PBM/Pharmacy Analyst  
**Purpose:** Explain how data moves through the prototype from collection to dashboard presentation  
**Status:** Synthetic proof of concept; not a clinical or formulary-decision system

![Simplified system architecture](./PHARMACY_FORMULARY_SIMPLIFIED_SYSTEM_ARCHITECTURE_PBM_ANALYST.png)

---

## 1. Architecture in one sentence

The prototype combines public CMS-derived plan information with synthetic member data, processes the data with Python, stores it in MySQL, applies a Logistic Regression model, aggregates the predictions, serves the results through FastAPI and displays them in a React dashboard for a PBM or pharmacy analyst.

---

## 2. Why the architecture is arranged from left to right

The arrows show the main direction in which information moves:

```text
Data is collected
    → data is prepared
    → the model learns and predicts
    → results are stored
    → the backend retrieves results
    → the frontend displays them
    → the analyst reviews them
```

Each box has one main responsibility. Keeping responsibilities separate makes the prototype easier to understand, test and maintain.

---

## 3. Data Sources

The first box contains the information used by the prototype.

### 3.1 Public CMS data

This represents the real public plan, formulary and pharmacy-network attributes used as reference information.

Examples include:

- Contract, plan and segment identifiers
- Plan and formulary identifiers
- Covered medications and RxCUIs
- Formulary tiers
- Prior authorization
- Step therapy
- Quantity limits
- Approved beneficiary-cost fields
- Preferred and nonpreferred pharmacy information

These attributes describe real public plan structures. They do not contain the prototype's synthetic adherence outcomes.

### 3.2 Synthetic member data

This represents the invented member and utilization information created for the proof of concept.

Examples include:

- Synthetic base profiles
- Age and chronic-condition count
- Medication assignments
- Member-plan scenarios
- Pharmacy selections
- Fill completion and delays
- Historical and future PDC
- Synthetic cost burden
- Adherent and non-adherent labels

No real patient is represented.

### 3.3 Why both data types are needed

CMS-derived data explains the plan environment. Synthetic member data explains the simulated person, medication history and outcome.

The prototype combines them to ask:

> Given this synthetic member's history and this plan's tier, restriction, cost and pharmacy context, what is the predicted risk of non-adherence?

### 3.4 Required provenance boundary

The system must always preserve the difference between:

```text
Real public CMS-derived attributes
```

and:

```text
Synthetic member, utilization, adherence and prediction data
```

Reports and dashboard screens must not present synthetic outcomes as measured plan performance.

---

## 4. Data and ML Pipeline — Python

The second box uses Python. Python performs both data preparation and machine-learning work.

### 4.1 Validation and generation

The validation and generation component:

1. Reads normalized plan, drug and pharmacy inputs.
2. Checks required columns and data types.
3. Preserves leading zeros in identifiers such as segment `000`.
4. Creates 1,000 synthetic base profiles.
5. Places each profile under all three selected plans.
6. Creates 3,000 member-plan scenarios.
7. Assigns medications and pharmacy exposure.
8. Creates historical and future fill events.
9. Calculates historical and future PDC.
10. Creates balanced adherent/non-adherent labels.
11. Runs integrity and reconciliation checks.

The current validated synthetic data contains:

| Data object | Count |
|---|---:|
| Base profiles | 1,000 |
| Member-plan scenarios | 3,000 |
| Member-medication rows | 5,343 |
| Fill events | 64,116 |
| Adherent scenarios | 1,500 |
| Non-adherent scenarios | 1,500 |

### 4.2 Matched-profile design

Every base profile appears under each of the three plans:

```text
1,000 base profiles × 3 plans = 3,000 scenarios
```

This allows the prototype to compare the same synthetic profile under different plan conditions.

### 4.3 Model training

Python also trains and evaluates the candidate models:

- Dummy baseline
- Logistic Regression
- Decision Tree
- Random Forest

The data is divided using `base_profile_id`, not random individual rows. All three plan scenarios for a profile remain together.

The official grouped split contains:

```text
Development: 800 profiles / 2,400 rows
Test:        200 profiles /   600 rows
Profile overlap: 0
```

Five-fold grouped cross-validation is performed inside the development partition.

### 4.4 Scoring

Scoring means applying the saved model to new feature rows.

The scoring process:

1. Receives a separate synthetic dashboard cohort.
2. Checks that the 12 expected features are present.
3. Applies the same preprocessing used during training.
4. Produces a non-adherence probability.
5. Converts the probability into an adherent/non-adherent prediction using the registered threshold.
6. Saves the prediction with its model and dataset version.

The dashboard cohort should not reuse the original training scenarios.

---

## 5. Logistic Regression Model

The orange box above the main flow represents the selected model artifact.

The selected model is the primary Model A Logistic Regression pipeline from the full model run.

### 5.1 Why Logistic Regression was selected

The selected model provides:

- 85.0% accuracy on the fixed synthetic test set
- 85.0% balanced accuracy
- 80.0% precision for non-adherent scenarios
- 93.3% recall for non-adherent scenarios
- 86.2% F1 score
- 0.938 ROC AUC
- 0.942 average precision
- Minimal training-to-validation overfitting gap
- Easier explanation than Random Forest

Although the diagram does not display a model version or threshold, those values remain stored in controlled model-run metadata.

### 5.2 What the model receives

The primary model uses these 12 predictors:

1. Age
2. Chronic-condition count
3. Medication count
4. Historical member PDC
5. Historical missed-fill rate
6. Historical mean delay days
7. Mean tier level
8. Prior-authorization rate
9. Step-therapy rate
10. Quantity-limit rate
11. Nonpreferred-pharmacy rate
12. Mean synthetic cost burden

### 5.3 What the model must not receive

The model must not use:

- Future member PDC
- The target as a feature
- Future fill-event summaries
- Hidden generation tendencies
- Generator risk or miss-probability fields
- Member or base-profile identifiers
- Random seeds

These restrictions prevent leakage, which would allow the model to see part of the answer.

### 5.4 Saved model artifact

The complete preprocessing-and-model pipeline is stored as a `.joblib` artifact.

The model artifact is loaded by the controlled scoring process. React does not load or run the model directly.

---

## 6. Data Layer — MySQL

The third box represents MySQL. MySQL is the prototype's structured data store.

It stores related data in tables and exposes safe views for specific purposes.

### 6.1 Synthetic member tables

| MySQL table | Purpose |
|---|---|
| `syn_base_profiles_v2_3` | Stores 1,000 plan-independent synthetic profiles |
| `syn_members_v2_3` | Stores 3,000 matched member-plan scenarios |
| `syn_member_medications_v2_3` | Stores medication, tier, restriction, burden and pharmacy exposure |
| `syn_fill_events_v2_3` | Stores historical and future scheduled fill events |
| `syn_member_features_v2_3` | Stores one derived feature and audit row per scenario |

### 6.2 Training view

The model team uses:

```text
ml_adherence_training_view_v2_3
```

This view contains:

- Traceability and grouped-split fields
- The 12 approved predictors
- The `non_adherent` label

It excludes future outcome-derived fields that would create leakage.

### 6.3 Prediction data

After scoring, the system should store one prediction row for every scored member-plan scenario.

Recommended fields include:

```text
model_run_id
dataset_version
member_id
base_profile_id
plan_key
predicted_non_adherence_probability
decision_threshold
predicted_class
scored_at
```

### 6.4 Aggregations

The model produces one prediction at a time. The dashboard needs summaries for entire plans and subgroups.

Aggregation combines individual predictions into:

- Plan KPIs
- Risk bands
- Medication-level summaries
- Tier-level summaries
- Prior-authorization, step-therapy and quantity-limit summaries
- Cost-burden summaries
- Preferred/nonpreferred pharmacy summaries
- Matched-profile plan comparisons
- Potential review-opportunity lists

### 6.5 Why predictions and aggregations are shown in the same data layer

Predictions are the detailed member-level results. Aggregations are the summarized results used by the dashboard.

Storing both makes the system:

- Faster
- Reproducible
- Easier to audit
- Easier to reconcile
- Less likely to calculate different KPI values in different screens

### 6.6 Correct aggregation grain

The aggregation code must understand what one row represents:

- Member KPI: unique member-plan scenario
- Medication KPI: member-medication row
- Fill KPI: scheduled fill event
- Drug KPI: unique exposed scenario for one RxCUI

This prevents members with several medications from being counted several times in a member-level KPI.

---

## 7. Backend — FastAPI

The fourth box represents the FastAPI backend.

FastAPI is the controlled connection between the React dashboard and the data/model services.

### 7.1 Simple analogy

Think of:

- React as the customer
- FastAPI as the waiter
- MySQL as the organized kitchen store
- The scoring model as a specialist working behind the scenes

React asks for a plan summary. FastAPI validates the request, obtains the correct versioned results and returns them in a predictable format.

### 7.2 Backend responsibilities

FastAPI should:

- Check application and database health
- Return the selected plan list
- Return plan and formulary reference information
- Return plan-level KPI cards
- Return chart-ready aggregation results
- Return prediction and model-run metadata
- Return potential review opportunities
- Validate plan keys and filters
- Use parameterized database queries
- Record request and run identifiers
- Return clear error messages without exposing database details

### 7.3 Recommended endpoints

| Endpoint | Purpose |
|---|---|
| `GET /api/v1/health` | Confirm that FastAPI and MySQL are available |
| `GET /api/v1/metadata/active-run` | Return active dataset, model and aggregation metadata |
| `GET /api/v1/plans` | Populate the plan dropdown |
| `GET /api/v1/plans/{planKey}/summary` | Return plan KPI cards |
| `GET /api/v1/plans/compare` | Compare the selected plans |
| `GET /api/v1/analytics/risk-distribution` | Return risk-band chart data |
| `GET /api/v1/analytics/tiers` | Return tier-level analytics |
| `GET /api/v1/analytics/restrictions` | Return PA/ST/QL analytics |
| `GET /api/v1/analytics/cost-burden` | Return cost-burden analytics |
| `GET /api/v1/analytics/pharmacies` | Return pharmacy-access analytics |
| `GET /api/v1/drugs` | Return medication-level analysis |
| `GET /api/v1/opportunities` | Return potential review opportunities |
| `GET /api/v1/models/{runId}/metrics` | Return model-evaluation results |

### 7.4 What FastAPI should not do during a dashboard request

FastAPI should not:

- Retrain the model
- Generate new synthetic fill histories
- Change the model threshold
- Recalculate the full training pipeline
- Allow the browser to submit raw SQL
- Return database credentials

Training, scoring and large aggregation refreshes should run as controlled batch processes.

---

## 8. Frontend — React Dashboard

The fifth box represents the React frontend.

React is the visible application used by the PBM or pharmacy analyst.

### 8.1 Plan dropdown

The plan dropdown controls the selected plan.

The flow is:

1. React requests the plan list from FastAPI.
2. The user selects a plan.
3. React sends the selected `plan_key` to FastAPI.
4. FastAPI returns the appropriate KPI and chart data.
5. React updates the dashboard.

The complete plan key uses:

```text
contract_id | plan_id | segment_id
```

Example:

```text
S4802|138|000
```

### 8.2 KPI cards

Three important plan KPIs are:

#### Total members scored

The number of synthetic scenarios scored for the selected plan.

#### Members flagged at risk

The number whose predicted probability meets or exceeds the registered decision threshold.

#### Percentage flagged at risk

```text
members flagged / total members scored × 100
```

### 8.3 Average predicted risk

Average predicted risk is the mean of all member-level probabilities.

It is different from the percentage flagged because the percentage flagged depends on the decision threshold.

### 8.4 Charts and analysis

The React dashboard may display:

- Risk distribution by plan
- Predicted risk by tier
- Prior-authorization exposure
- Step-therapy exposure
- Quantity-limit exposure
- Cost-burden distribution
- Preferred/nonpreferred pharmacy comparison
- Medication-level risk and exposure
- Matched-profile plan differences

### 8.5 Review signals

The dashboard can show a transparent worklist labelled:

> Potential Formulary Review Opportunity — Synthetic POC

A review signal may combine:

- Predicted risk
- Exposed synthetic population
- Higher tier
- PA, ST or QL exposure
- Synthetic cost burden
- Nonpreferred-pharmacy exposure
- Matched-profile differences across plans

It is a prioritization signal, not an automatic recommendation to change the formulary.

### 8.6 What React should not calculate

React should not recreate the official KPI formulas. FastAPI should return chart-ready, validated aggregate values.

This prevents two dashboard pages from calculating the same metric differently.

---

## 9. Primary User — PBM / Pharmacy Analyst

The person icon on the right represents the main user of the prototype.

### 9.1 PBM

PBM means Pharmacy Benefit Manager. A PBM is generally an organization that helps administer prescription-drug benefits.

### 9.2 Individual users

The person using the dashboard may be:

- Formulary analyst
- Pharmacy benefits analyst
- Clinical pharmacist
- Formulary manager
- Adherence-program analyst
- Health-plan pharmacy team member

### 9.3 What the user does

The analyst:

1. Selects a plan.
2. Reviews population-level risk.
3. Examines tiers, restrictions, burden and pharmacy exposure.
4. Reviews medication-level patterns.
5. Compares matched profiles across plans.
6. Investigates potential review opportunities.
7. Uses professional judgment before taking any action.

The prototype assists the analyst. It does not replace the analyst.

---

## 10. End-to-end training flow

The top model box and the Python/MySQL boxes together represent the offline training process.

```text
Public CMS-derived inputs
    +
Synthetic generation inputs
    ↓
Validated synthetic member tables
    ↓
Leakage-safe MySQL training view
    ↓
Grouped development/test split
    ↓
Baseline, Logistic Regression, Decision Tree and Random Forest
    ↓
Grouped cross-validation and one final test
    ↓
Selected Logistic Regression pipeline
    ↓
Saved model artifact and model-run metadata
```

The dashboard does not execute this training flow when a user selects a plan.

---

## 11. End-to-end dashboard flow

The normal dashboard flow is:

```text
Separate synthetic dashboard cohort
    ↓
Validate the same 12 feature definitions
    ↓
Load the saved Logistic Regression pipeline
    ↓
Predict member-plan risk probabilities and classes
    ↓
Store predictions in MySQL
    ↓
Join predictions with plan, medication and pharmacy context
    ↓
Build and validate dashboard aggregations
    ↓
FastAPI returns active versioned results
    ↓
React displays KPIs, charts and review signals
    ↓
PBM/pharmacy analyst investigates the results
```

---

## 12. Why batch scoring is recommended

The proof of concept should use batch scoring instead of scoring or retraining during every dashboard request.

Batch scoring means that a controlled process scores a complete cohort and saves the results before the user opens the dashboard.

Benefits include:

- Faster dashboard responses
- Stable demonstration results
- Clear dataset and model versions
- Easier validation
- Easier debugging
- No accidental retraining from React
- Reproducible aggregations

---

## 13. Versioning and reproducibility

The simplified image intentionally does not show version numbers, model labels or thresholds. The implementation must still store them behind the scenes.

Every active result should be traceable to:

- Dataset generation version
- Source file hash
- Fixed grouped split
- Feature contract
- Model run ID
- Model artifact hash
- Model parameters
- Decision threshold
- Python and library versions
- Scoring timestamp
- Aggregation version

FastAPI should return relevant active-run metadata so the dashboard never mixes data from different model runs.

---

## 14. Security boundaries

### React

- Communicates only with FastAPI
- Does not connect directly to MySQL
- Does not receive database credentials
- Does not load the model artifact

### FastAPI

- Validates input parameters
- Uses parameterized SQL
- Restricts allowed frontend origins
- Uses environment variables for secrets
- Returns controlled response schemas

### MySQL

- Uses separate read and write permissions where practical
- Restricts synthetic loading, scoring and aggregation writes to controlled jobs
- Preserves foreign keys and validation constraints

### Model artifact

- Stored outside public frontend files
- Loaded only by the backend or controlled scoring job
- Verified using an artifact hash

---

## 15. What the architecture proves

The architecture demonstrates that the prototype can:

- Combine plan/formulary context with synthetic member history
- Maintain real-versus-synthetic provenance
- Train a leakage-safe model
- Predict synthetic adherence risk
- Store model results with traceability
- Aggregate member-level predictions correctly
- Serve consistent analytics through an API
- Display plan-level and medication-level results in a dashboard
- Support a PBM or pharmacy analyst's review workflow

---

## 16. What the architecture does not prove

The architecture does not prove that:

- A formulary restriction caused non-adherence
- A real member will be adherent or non-adherent
- One plan is clinically better than another
- A formulary should be changed
- A restriction should be removed
- A medicine should change tiers
- The model will achieve the same performance on real-world data
- A review opportunity guarantees improved outcomes or savings

---

## 17. Required dashboard disclaimer

> This prototype combines real public CMS-derived plan, formulary, beneficiary-cost and pharmacy-network attributes with synthetic member, medication, utilization, cost-burden, adherence and prediction data. It demonstrates a proof-of-concept analytical workflow. The results do not represent real patients, measured plan performance, clinical evidence, official CMS quality measures, causal effects, guaranteed formulary-review needs or recommendations to change coverage or formulary policy.

---

## 18. Final summary

The image shows a simple but complete system.

Data begins with public CMS-derived plan information and synthetic members. Python validates and prepares the data, trains the model and scores new synthetic scenarios. MySQL stores the tables, training view, predictions and aggregations. FastAPI provides a safe and consistent interface. React turns the results into plan dropdowns, KPI cards, charts and review signals. A PBM or pharmacy analyst uses the dashboard to investigate potential formulary and adherence-risk patterns.

The model supplies evidence for review. The human analyst remains responsible for interpretation and any next step.
