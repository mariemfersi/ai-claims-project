const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

async function parseResponse(response) {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || JSON.stringify(data) || "Erreur API");
  }
  return data;
}

export async function listClaims() {
  return parseResponse(await fetch(`${API_URL}/claims/`));
}

export async function getClaim(id) {
  return parseResponse(await fetch(`${API_URL}/claims/${id}/`));
}

export async function createClaim(values, files) {
  const body = new FormData();
  Object.entries(values).forEach(([key, value]) => body.append(key, value));
  Array.from(files).forEach((file) => body.append("files", file));
  return parseResponse(await fetch(`${API_URL}/claims/`, { method: "POST", body }));
}

export async function retryClaim(id) {
  return parseResponse(await fetch(`${API_URL}/claims/${id}/retry/`, { method: "POST" }));
}

export async function updateClaimFiles(id, files, keepDocumentIds) {
  const body = new FormData();
  Array.from(files).forEach((file) => body.append("files", file));
  keepDocumentIds.forEach((documentId) => body.append("keep_document_ids", documentId));
  if (!keepDocumentIds.length) body.append("keep_document_ids", "");
  return parseResponse(await fetch(`${API_URL}/claims/${id}/add-files/`, { method: "POST", body }));
}

export async function getSystemInfo() {
  return parseResponse(await fetch(`${API_URL}/system/info/`));
}

