const API_BASE = import.meta.env.VITE_API_BASE_URL;

// Fail loudly at load rather than firing requests at `undefined/...` later.
if (!API_BASE) {
  throw new Error(
    "VITE_API_BASE_URL is not set. Copy .env.example to .env and restart the dev server.",
  );
}

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const message = body.detail ? JSON.stringify(body.detail) : response.statusText;
    throw new Error(`${body.error || "request_failed"}: ${message}`);
  }
  return response.json();
}

// Creates a new evaluation against the default BPP/PPA checklist.
// Returns the full Evaluation object (id, requirements, status, ...).
export function createDefaultEvaluation() {
  return request("/requirements", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mode: "default" }),
  });
}

// Attaches contractor submission files to an evaluation.
export function submitDocuments(evaluationId, files) {
  const form = new FormData();
  form.append("evaluation_id", evaluationId);
  for (const file of files) form.append("files", file);
  return request("/submissions", { method: "POST", body: form });
}

// Kicks off the (long-running, background) evaluation run.
export function runEvaluate(evaluationId) {
  return request("/evaluate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ evaluation_id: evaluationId }),
  });
}

// { evaluation_id, status }
export function getStatus(evaluationId) {
  return request(`/status/${evaluationId}`);
}

// The finished ComplianceReport.
export function getReport(evaluationId) {
  return request(`/reports/${evaluationId}`);
}
