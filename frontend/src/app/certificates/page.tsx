"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useApp } from "@/lib/auth";
import { useToast } from "@/components/ui/Toast";
import { money } from "@/lib/validators";
import CertificatePreview from "@/components/certificates/CertificatePreview";
import type { PendingGroup, Certificate } from "@/types/models";

export default function CertificatesPage() {
  const { issuerId } = useApp();
  const notify = useToast();
  const [pending, setPending] = useState<PendingGroup[]>([]);
  const [certs, setCerts] = useState<Certificate[]>([]);
  const [checked, setChecked] = useState<Record<number, boolean>>({});
  const [filters, setFilters] = useState({ bin: "", supplier: "" });
  const [previewId, setPreviewId] = useState<number | null>(null);
  const [page, setPage] = useState(1);
  const PS = 20;

  async function reload() {
    if (!issuerId) return;
    setPending(await api.pending(issuerId));
    setCerts(await api.listCertificates(issuerId, filters.bin, filters.supplier));
  }
  useEffect(() => { reload(); }, [issuerId]);

  async function generateOne(g: PendingGroup) {
    try { const c = await api.generate(issuerId!, g.supplier_id); notify(`Generated ${c.certificate_no}`); await reload(); setPreviewId(c.id); }
    catch (e: any) { notify(e.message, "err"); }
  }
  async function generateSelected() {
    const ids = pending.filter((g) => checked[g.supplier_id]).map((g) => g.supplier_id);
    if (!ids.length) return notify("Select at least one group.", "warn");
    let n = 0;
    for (const sid of ids) { try { await api.generate(issuerId!, sid); n++; } catch {} }
    setChecked({}); notify(`Bulk generation: ${n} succeeded.`); await reload();
  }
  async function sendAll() {
    let ok = 0, skip = 0;
    for (const c of certs) { try { await api.dispatch(c.id, "email"); ok++; } catch { skip++; } }
    notify(`Bulk send: ${ok} sent, ${skip} skipped.`); await reload();
  }
  async function checkAll() {
    let flagged = 0;
    for (const c of certs) { const a = await api.anomalies(c.id); if (a.length) flagged++; }
    notify(flagged ? `${flagged} certificate(s) have anomalies — open them to review.` : "No anomalies found.");
  }

  const pages = Math.max(1, Math.ceil(certs.length / PS));
  const pageCerts = certs.slice((page - 1) * PS, page * PS);

  return (
    <div className="stack">
      <div className="row-between"><h1 style={{ fontSize: 18, fontWeight: 600 }} className="grow">Certificate Issue</h1>
        <button className="btn btn-ghost" onClick={() => notify("Add-supplier is done via Import; suppliers are created from the workbook.", "warn")}>+ Add Supplier</button></div>

      <div className="card p5"><div className="grid6">
        <div style={{ gridColumn: "span 2" }}><label className="label">BIN</label><input className="input mono" value={filters.bin} onChange={(e) => setFilters({ ...filters, bin: e.target.value })} onKeyDown={(e) => e.key === "Enter" && reload()} /></div>
        <div style={{ gridColumn: "span 2" }}><label className="label">Supplier name</label><input className="input" value={filters.supplier} onChange={(e) => setFilters({ ...filters, supplier: e.target.value })} onKeyDown={(e) => e.key === "Enter" && reload()} /></div>
        <button className="btn btn-primary" style={{ gridColumn: "span 2" }} onClick={() => { setPage(1); reload(); }}>Search</button></div></div>

      <div className="card"><div className="card-head"><span className="card-title grow">Pending <span className="muted" style={{ fontWeight: 400 }}>({pending.length})</span></span>
        <button className="btn btn-primary btn-sm" onClick={generateSelected}>Generate selected</button></div>
        <table className="tbl"><thead><tr><th></th><th>Supplier</th><th>BIN</th><th>Period</th>
          <th style={{ textAlign: "right" }}>Lines</th><th style={{ textAlign: "right" }}>Value (incl.)</th><th style={{ textAlign: "right" }}>VAT withheld</th><th></th></tr></thead>
          <tbody>
            {pending.map((g) => <tr key={g.supplier_id}>
              <td><input type="checkbox" checked={!!checked[g.supplier_id]} onChange={(e) => setChecked({ ...checked, [g.supplier_id]: e.target.checked })} /></td>
              <td>{g.supplier}</td><td className="mono">{g.bin || "—"}</td><td>{g.period}</td>
              <td style={{ textAlign: "right" }}>{g.line_count}</td>
              <td className="mono" style={{ textAlign: "right" }}>{money(g.total_incl)}</td>
              <td className="mono" style={{ textAlign: "right" }}>{money(g.total_vat)}</td>
              <td style={{ textAlign: "right" }}><button className="btn btn-ghost btn-sm" onClick={() => generateOne(g)}>Generate Certificate</button></td></tr>)}
            {pending.length === 0 && <tr><td colSpan={8} className="muted" style={{ padding: 16 }}>No pending groups. Import data first.</td></tr>}
          </tbody></table></div>

      <div className="card"><div className="card-head"><span className="card-title grow">Generated certificates <span className="muted" style={{ fontWeight: 400 }}>({certs.length})</span></span>
        <button className="btn btn-ghost btn-sm" onClick={checkAll}>Check all</button>
        <button className="btn btn-primary btn-sm" onClick={sendAll}>Send all</button></div>
        <table className="tbl"><thead><tr><th>Certificate No.</th><th>Supplier</th><th>BIN</th><th>Period</th><th>Issued</th>
          <th style={{ textAlign: "right" }}>VAT withheld</th><th>Status</th><th></th></tr></thead>
          <tbody>
            {pageCerts.map((c) => <tr key={c.id}>
              <td className="mono">{c.certificate_no}</td><td>{c.supplier}</td><td className="mono">{c.bin || "—"}</td>
              <td>{c.period}</td><td>{c.issue_date}</td><td className="mono" style={{ textAlign: "right" }}>{money(c.total_vat)}</td>
              <td><span className={`badge ${c.status === "sent" ? "badge-green" : "badge-rule"}`}>{c.status}</span></td>
              <td style={{ textAlign: "right", whiteSpace: "nowrap" }}>
                <a className="btn btn-ghost btn-sm" href={api.pdfUrl(c.id)} target="_blank">Export</a>
                <button className="btn btn-ghost btn-sm" onClick={() => setPreviewId(c.id)}>Preview / send</button></td></tr>)}
            {certs.length === 0 && <tr><td colSpan={8} className="muted" style={{ padding: 16 }}>No certificates match these filters.</td></tr>}
          </tbody></table>
        <div style={{ display: "flex", gap: 10, alignItems: "center", padding: "8px 16px", fontSize: 13 }}>
          <button className="btn btn-ghost btn-sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</button>
          <span>Page {page} of {pages}</span>
          <button className="btn btn-ghost btn-sm" disabled={page >= pages} onClick={() => setPage(page + 1)}>Next</button></div></div>

      {previewId && <CertificatePreview certId={previewId} onClose={() => { setPreviewId(null); reload(); }} onChanged={reload} />}
    </div>
  );
}
