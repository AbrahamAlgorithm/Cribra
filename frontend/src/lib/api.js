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

// Read-only preview of the default checklist (no evaluation is created).
// Returns Requirement[] — used to render checkboxes before the officer
// decides which items apply to this contract.
export function getDefaultRequirements() {
  return request("/requirements/default");
}

// Creates an evaluation from an officer-curated requirement list (e.g. the
// default checklist with some items unchecked). Each item needs
// { name, description, is_mandatory, source }.
export function createManualEvaluation(requirements) {
  return request("/requirements", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mode: "manual", requirements }),
  });
}

// Sets evaluation_date explicitly (only allowed while status is "pending",
// i.e. before /evaluate is called). Certificate expiry (4A) is checked
// against this date, not the server's current date — SPEC.md Section 4.3.
export function setEvaluationDate(evaluationId, evaluationDate) {
  return request(`/evaluations/${evaluationId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ evaluation_date: evaluationDate }),
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

// Records the procurement officer's own judgement on one requirement result
// — agreement or an override on the system's finding. Returns the updated
// ComplianceReport. `note` is optional.
export function reviewResult(evaluationId, requirementId, { status, note }) {
  return request(`/reports/${evaluationId}/results/${requirementId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status, note: note || null }),
  });
}
