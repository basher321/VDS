"use client";
import { useEffect, useState } from "react";
import { api, getToken } from "@/lib/api";
import { useToast } from "@/components/ui/Toast";
import type { Certificate, Anomaly, DispatchJob } from "@/types/models";

export default function CertificatePreview({ certId, onClose, onChanged }:
  { certId: number; onClose: () => void; onChanged?: () => void }) {
  const notify = useToast();
  const [cert, setCert] = useState<Certificate | null>(null);
  const [anoms, setAnoms] = useState<Anomaly[]>([]);
  const [jobs, setJobs] = useState<DispatchJob[]>([]);
  const [remarks, setRemarks] = useState("");
  const [override, setOverride] = useState("");
  const [dateMode, setDateMode] = useState("auto");
  const [manualDate, setManualDate] = useState("");
  const [bust, setBust] = useState(Date.now());
  const [note, setNote] = useState<{ msg: string; kind: string } | null>(null);

  async function load() {
    const c = await api.getCertificate(certId);
    setCert(c); setRemarks(c.remarks || ""); setDateMode(c.issue_date_mode);
    setAnoms(await api.anomalies(certId));
    setJobs(await api.dispatchJobs(certId));
  }
  useEffect(() => { load(); }, [certId]);

  function refreshPdf() { setBust(Date.now()); onChanged?.(); }
  const pNote = (msg: string, kind = "ok") => setNote({ msg, kind });

  async function saveRemarks() { await api.setRemarks(certId, remarks); await load(); refreshPdf(); pNote("Remarks saved — certificate re-rendered."); }
  async function setBin(v: boolean) { await api.setBinStatus(certId, v); await load(); refreshPdf(); pNote("Supplier-BIN status saved."); }
  async function saveDate() {
    if (dateMode === "manual" && !manualDate) return pNote("Pick a date for Manual mode.", "warn");
    await api.setIssueDate(certId, dateMode, dateMode === "manual" ? manualDate : null);
    await load(); refreshPdf(); pNote("Issue date saved.");
  }
  async function sendEmail() {
    try {
      const res = await api.dispatch(certId, "email", override || undefined);
      const queued = res.some((r: any) => r.status === "queued");
      pNote(queued ? `Email queued (offline mode): ${res.map((r: any) => r.recipient).join(", ")}`
                   : `Email sent to: ${res.map((r: any) => r.recipient).join(", ")}`, queued ? "warn" : "ok");
      await load(); onChanged?.();
    } catch (e: any) {
      if (e.detail?.blocked) { setAnoms(e.detail.anomalies || []); pNote("Send blocked. Fix anomalies or enter an override reason and retry.", "err"); }
      else pNote(e.message, "err");
    }
  }
  async function sendWhatsApp() {
    try { const res = await api.dispatch(certId, "whatsapp", override || undefined); pNote(`WhatsApp dispatch: ${res.map((r: any) => r.recipient).join(", ")}`); await load(); }
    catch (e: any) { pNote(e.message, "err"); }
  }
  function openPdf() { window.open(api.pdfUrl(certId, bust), "_blank"); }

  if (!cert) return null;
  return (
    <div className="modal" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal-box">
        <div className="modal-bar">
          <span className="mono grow">{cert.certificate_no}</span>
          <button className="btn btn-ghost btn-sm" onClick={sendEmail}>Send email</button>
          <button className="btn btn-ghost btn-sm" onClick={sendWhatsApp}>Send WhatsApp</button>
          <button className="btn btn-ghost btn-sm" onClick={openPdf}>Print</button>
          <a className="btn btn-ghost btn-sm" href={api.pdfUrl(certId, bust)} download>Download PDF</a>
          <button className="btn btn-primary btn-sm" onClick={onClose}>Close</button>
        </div>
        {note && <div className={`notice n-${note.kind === "err" ? "err" : note.kind === "warn" ? "warn" : "ok"}`} style={{ margin: "12px 18px" }}>{note.msg}</div>}
        {anoms.length > 0 && (
          <div className="notice n-err" style={{ margin: "12px 18px" }}>
            <b>Anomalies — sending is blocked until fixed or overridden:</b>
            <ul style={{ margin: "6px 0 8px 18px" }}>{anoms.map((a, i) => <li key={i}><span className="mono" style={{ fontSize: 11 }}>{a.code}</span> — {a.message}</li>)}</ul>
            <input className="input" placeholder="Override reason (logged with your name)..." value={override} onChange={(e) => setOverride(e.target.value)} />
          </div>
        )}
        {jobs.length > 0 && (
          <div className="card" style={{ margin: "12px 18px" }}>
            <div className="card-head" style={{ padding: "10px 14px" }}><span className="card-title grow" style={{ fontSize: 13 }}>Email delivery status</span>
              <button className="btn btn-ghost btn-sm" onClick={load}>Refresh</button></div>
            <ul style={{ listStyle: "none", margin: 0, padding: "10px 14px" }}>
              {jobs.filter((j) => j.channel === "email").map((j) => <li key={j.id}>{j.recipient} <span className="muted">— {j.status}</span></li>)}
            </ul>
          </div>
        )}
        {/* Authoritative rendered certificate (PDF from the backend renderer) */}
        <div style={{ padding: "0 18px 12px" }}>
          <object className="pdf-frame" data={api.pdfUrl(certId, bust)} type="application/pdf">
            <p className="muted" style={{ padding: 16 }}>PDF preview unavailable — <a href={api.pdfUrl(certId, bust)} target="_blank">open the certificate</a>.</p>
          </object>
        </div>
        <div className="p5 space" style={{ borderTop: "1px solid var(--rule)" }}>
          <div><label className="label">Supplier BIN on record (if applicable)</label>
            <label className="chk" style={{ marginRight: 14 }}><input type="radio" checked={cert.has_bin} onChange={() => setBin(true)} /> Yes</label>
            <label className="chk"><input type="radio" checked={!cert.has_bin} onChange={() => setBin(false)} /> No</label></div>
          <div><label className="label">Remarks</label>
            <div style={{ display: "flex", gap: 8 }}><input className="input" value={remarks} onChange={(e) => setRemarks(e.target.value)} />
              <button className="btn btn-primary" onClick={saveRemarks}>Save remarks</button></div></div>
          <div><label className="label">Issue date</label>
            <div style={{ display: "flex", alignItems: "center", gap: 14, flexWrap: "wrap" }}>
              <label className="chk"><input type="radio" checked={dateMode === "auto"} onChange={() => setDateMode("auto")} /> Automatic (today)</label>
              <label className="chk"><input type="radio" checked={dateMode === "manual"} onChange={() => setDateMode("manual")} /> Manual</label>
              {dateMode === "manual" && <input className="input" style={{ width: "auto" }} type="date" value={manualDate} onChange={(e) => setManualDate(e.target.value)} />}
              <button className="btn btn-ghost btn-sm" onClick={saveDate}>Save date</button></div></div>
        </div>
      </div>
    </div>
  );
}
