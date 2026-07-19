"use client";
const BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("vds_token");
}
export function setToken(t: string) { localStorage.setItem("vds_token", t); }
export function clearToken() { localStorage.removeItem("vds_token"); }
export function getActiveIssuer(): number | null {
  const v = typeof window !== "undefined" ? localStorage.getItem("vds_issuer") : null;
  return v ? Number(v) : null;
}
export function setActiveIssuer(id: number) { localStorage.setItem("vds_issuer", String(id)); }

async function req(path: string, opts: RequestInit = {}) {
  const headers: Record<string, string> = { ...(opts.headers as any) };
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (opts.body && !(opts.body instanceof FormData)) headers["Content-Type"] = "application/json";
  const res = await fetch(`${BASE}${path}`, { ...opts, headers });
  if (res.status === 401 && typeof window !== "undefined") {
    clearToken(); window.location.href = "/login";
  }
  if (!res.ok) {
    let detail: any = await res.text();
    try { detail = JSON.parse(detail).detail ?? detail; } catch {}
    const err: any = new Error(typeof detail === "string" ? detail : "Request failed");
    err.detail = detail; err.status = res.status;
    throw err;
  }
  const ct = res.headers.get("content-type") || "";
  return ct.includes("application/json") ? res.json() : res.text();
}

export const api = {
  base: BASE,
  login: (username: string, password: string) =>
    req("/api/auth/login", { method: "POST", body: JSON.stringify({ username, password }) }),
  dashboard: () => req("/api/dashboard"),
  // issuers / settings
  listIssuers: () => req("/api/issuers"),
  createIssuer: (body: any) => req("/api/issuers", { method: "POST", body: JSON.stringify(body) }),
  updateIssuer: (id: number, body: any) => req(`/api/issuers/${id}`, { method: "PUT", body: JSON.stringify(body) }),
  listSignatures: (id: number) => req(`/api/issuers/${id}/signatures`),
  addSignature: (id: number, body: any) => req(`/api/issuers/${id}/signatures`, { method: "POST", body: JSON.stringify(body) }),
  updateSignature: (sid: number, body: any) => req(`/api/signatures/${sid}`, { method: "PUT", body: JSON.stringify(body) }),
  deleteSignature: (sid: number) => req(`/api/signatures/${sid}`, { method: "DELETE" }),
  uploadSignatureImage: (sid: number, file: File) => {
    const fd = new FormData(); fd.append("file", file);
    return req(`/api/signatures/${sid}/upload`, { method: "POST", body: fd });
  },
  getNumbering: (id: number) => req(`/api/issuers/${id}/numbering`),
  updateNumbering: (id: number, body: any) => req(`/api/issuers/${id}/numbering`, { method: "PUT", body: JSON.stringify(body) }),
  listRates: () => req("/api/rates"),
  addRate: (body: any) => req("/api/rates", { method: "POST", body: JSON.stringify(body) }),
  updateRate: (rid: number, body: any) => req(`/api/rates/${rid}`, { method: "PUT", body: JSON.stringify(body) }),
  deleteRate: (rid: number) => req(`/api/rates/${rid}`, { method: "DELETE" }),
  getOrgSettings: () => req("/api/org-settings"),
  updateOrgSettings: (body: any) => req("/api/org-settings", { method: "PUT", body: JSON.stringify(body) }),
  uploadImage: (id: number, kind: string, file: File) => {
    const fd = new FormData(); fd.append("file", file);
    return req(`/api/issuers/${id}/upload/${kind}`, { method: "POST", body: fd });
  },
  // import
  importFile: (issuerId: number, file: File) => {
    const fd = new FormData(); fd.append("issuer_id", String(issuerId)); fd.append("file", file);
    return req("/api/import", { method: "POST", body: fd });
  },
  // certificates
  pending: (issuerId: number) => req(`/api/certificates/pending?issuer_id=${issuerId}`),
  listCertificates: (issuerId: number, bin = "", supplier = "") =>
    req(`/api/certificates?issuer_id=${issuerId}&bin=${encodeURIComponent(bin)}&supplier=${encodeURIComponent(supplier)}`),
  generate: (issuerId: number, supplierId: number) =>
    req(`/api/certificates/generate?issuer_id=${issuerId}`, { method: "POST", body: JSON.stringify({ supplier_id: supplierId }) }),
  getCertificate: (id: number) => req(`/api/certificates/${id}`),
  pdfUrl: (id: number, bust = 0) => {
    const params = new URLSearchParams();
    const token = getToken();
    if (token) params.set("token", token);
    if (bust) params.set("t", String(bust));
    const qs = params.toString();
    return `${BASE}/api/certificates/${id}/pdf${qs ? `?${qs}` : ""}`;
  },
  setRemarks: (id: number, remarks: string) => req(`/api/certificates/${id}/remarks`, { method: "PUT", body: JSON.stringify({ remarks }) }),
  setBinStatus: (id: number, has_bin: boolean) => req(`/api/certificates/${id}/bin-status`, { method: "PUT", body: JSON.stringify({ has_bin }) }),
  setIssueDate: (id: number, mode: string, on_date: string | null) =>
    req(`/api/certificates/${id}/issue-date`, { method: "PUT", body: JSON.stringify({ mode, on_date }) }),
  anomalies: (id: number) => req(`/api/certificates/${id}/anomalies`),
  dispatch: (id: number, channel: string, override_reason?: string) =>
    req(`/api/certificates/${id}/dispatch`, { method: "POST", body: JSON.stringify({ channel, override_reason }) }),
  dispatchJobs: (id: number) => req(`/api/certificates/${id}/dispatch-jobs`),
};
