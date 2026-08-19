const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api/v1";

export class ApiError extends Error {
  constructor(status, code, message) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

export async function apiRequest(path, signal) {
  const response = await fetch(`${API_BASE_URL}${path}`, { signal });
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(
      response.status,
      body?.error?.code || "request_failed",
      body?.error?.message || "The request could not be completed.",
    );
  }
  return body;
}

export const encoded = (value) => encodeURIComponent(value);

export const endpoints = {
  plans: "/plans",
  modelMetadata: "/metadata/model",
  summary: (planKey) => `/dashboard/plans/${encoded(planKey)}/summary`,
  analytics: (name, planKey, suffix = "") =>
    `/analytics/${name}?plan_key=${encoded(planKey)}${suffix}`,
  prescribers: (planKey, limit = 60) =>
    `/analytics/prescribers?plan_key=${encoded(planKey)}&limit=${limit}`,
  prescriberSummary: (id, planKey) =>
    `/analytics/prescribers/${encoded(id)}?plan_key=${encoded(planKey)}`,
  prescriberMedications: (id, planKey, opportunities = false) =>
    `/analytics/prescribers/${encoded(id)}/${opportunities ? "opportunities" : "medications"}?plan_key=${encoded(planKey)}&limit=100`,
};
