# Model artifact location

Place the selected Model A files here:

- `logistic_regression_pipeline.joblib`
- `model_selection.json`

Use the files from `mvp_v2_3_run_20260817T155422Z/model_a` and the run-level
`model_selection.json`. The registered threshold is read from the JSON file and
falls back to `MODEL_THRESHOLD` only when metadata is unavailable.

