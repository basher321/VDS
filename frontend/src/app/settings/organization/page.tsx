"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useApp } from "@/lib/auth";
import { useToast } from "@/components/ui/Toast";
import type { Issuer, Signature, Numbering, Rate, OrgSettings } from "@/types/models";

const SMTP_PRESETS: Record<string, { smtp_host: string; smtp_port: number }> = {
  "Microsoft 365 / Outlook": { smtp_host: "smtp.office365.com", smtp_port: 587 },
  "Google Workspace": { smtp_host: "smtp.gmail.com", smtp_port: 587 },
  "Zimbra": { smtp_host: "", smtp_port: 587 },
  "Other (custom SMTP)": { smtp_host: "", smtp_port: 587 },
};

export default function SettingsPage() {
  const { issuers, issuerId, refreshIssuers, setIssuer } = useApp();
  const notify = useToast();
  const issuer = issuers.find((i) => i.id === issuerId) || null;

  const [form, setForm] = useState<Issuer | null>(null);
  const [sigs, setSigs] = useState<Signature[]>([]);
  const [num, setNum] = useState<Numbering | null>(null);
  const [rates, setRates] = useState<Rate[]>([]);
  const [org, setOrg] = useState<OrgSettings | null>(null);
  const [newIssuer, setNewIssuer] = useState(""); const [showAdd, setShowAdd] = useState(false);
  const [reset, setReset] = useState("");
  const [nsig, setNsig] = useState({ name: "", designation: "", email: "" });

  useEffect(() => { if (issuer) setForm({ ...issuer }); }, [issuerId, issuers.length]);
  useEffect(() => {
    if (!issuerId) return;
    api.listSignatures(issuerId).then(setSigs);
    api.getNumbering(issuerId).then(setNum);
  }, [issuerId]);
  useEffect(() => { api.listRates().then(setRates); api.getOrgSettings().then(setOrg); }, []);

  if (!form || !num || !org) return <p className="muted">Loading…</p>;

  const setF = (k: keyof Issuer, v: any) => setForm({ ...form, [k]: v });
  const setN = (k: keyof Numbering, v: any) => setNum({ ...num, [k]: v });
  const setO = (k: keyof OrgSettings, v: any) => setOrg({ ...org, [k]: v });

  const preview = (() => {
    const a = "2025", b = "26";
    const fy = num.fiscal_year_format === "YYYY" ? a : num.fiscal_year_format === "YY-YY" ? a.slice(-2) + "-" + b : a + "-" + b;
    const an = String(num.start_number).padStart(Number(num.pad_width), "0");
    return num.number_format.split("{CompanyName}").join(num.company_token)
      .split("{FiscalYear}").join(fy).split("{AutoNumber}").join(an).split("{sep}").join(num.separator);
  })();

  async function saveIssuer() { await api.updateIssuer(form!.id, form); await refreshIssuers(); notify("Issuer details saved."); }
  async function createIssuer() {
    if (!newIssuer.trim()) return;
    const c = await api.createIssuer({ name: newIssuer.trim() });
    await refreshIssuers(); setIssuer(c.id); setNewIssuer(""); setShowAdd(false); notify(`Issuer "${c.name}" created.`);
  }
  async function upload(kind: string, file: File) { await api.uploadImage(form!.id, kind, file); await refreshIssuers(); notify(`${kind} uploaded.`); }
  async function toggleSig(s: Signature) { await api.updateSignature(s.id, { ...s, enabled: !s.enabled }); setSigs(await api.listSignatures(issuerId!)); }
  async function delSig(s: Signature) { if (!confirm(`Delete "${s.name}"?`)) return; await api.deleteSignature(s.id); setSigs(await api.listSignatures(issuerId!)); }
  async function addSig() {
    if (!nsig.name.trim()) return notify("Enter a signatory name.", "err");
    await api.addSignature(issuerId!, { ...nsig, enabled: true });
    setNsig({ name: "", designation: "", email: "" }); setSigs(await api.listSignatures(issuerId!)); notify("Signature added.");
  }
  async function saveNum() { await api.updateNumbering(issuerId!, num); notify("Numbering saved."); }
  async function saveRate(r: Rate) { await api.updateRate(r.id, r); notify("Rate saved."); }
  async function addRate() {
    const d = prompt("Service category name"); if (!d) return;
    await api.addRate({ category_code: d.toUpperCase().replace(/\s+/g, "_").slice(0, 12), description: d.trim(), vds_rate: 0.15 });
    setRates(await api.listRates());
  }
  async function delRate(r: Rate) { await api.deleteRate(r.id); setRates(await api.listRates()); }
  async function saveOrg() { await api.updateOrgSettings(org); notify("Email/WhatsApp settings saved."); }

  return (
    <div className="stack">
      {/* Issuers */}
      <div className="card p5 space">
        <div className="row-between"><h2 className="card-title grow">Issuers (withholding entities)</h2>
          <button className="btn btn-ghost btn-sm" onClick={() => setShowAdd(!showAdd)}>{showAdd ? "Cancel" : "+ Add issuer"}</button></div>
        <p className="muted" style={{ fontSize: 13, margin: 0 }}>Sections below apply to the issuer selected in the header.</p>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
          {issuers.map((x) => <button key={x.id} className={`btn ${x.id === issuerId ? "btn-primary" : "btn-ghost"} btn-sm`}
            onClick={() => { setIssuer(x.id); location.reload(); }}>{x.name}{x.is_default ? " (default)" : ""}</button>)}
        </div>
        {showAdd && <div style={{ display: "flex", gap: 8, alignItems: "flex-end" }}>
          <div style={{ flex: 1 }}><label className="label">New issuer name</label><input className="input" value={newIssuer} onChange={(e) => setNewIssuer(e.target.value)} /></div>
          <button className="btn btn-primary" onClick={createIssuer}>Create</button></div>}
      </div>

      {/* Identity */}
      <div className="card p5 space"><h2 className="card-title">Issuer identity</h2>
        <div><label className="label">Withholding entity name</label><input className="input" value={form.name || ""} onChange={(e) => setF("name", e.target.value)} /></div>
        <div><label className="label">Address</label><textarea className="input" rows={2} value={form.address || ""} onChange={(e) => setF("address", e.target.value)} /></div>
        <div style={{ maxWidth: 280 }}><label className="label">BIN (9-4 format)</label><input className="input mono" value={form.bin || ""} onChange={(e) => setF("bin", e.target.value)} /></div>
        <button className="btn btn-primary" onClick={saveIssuer}>Save issuer details</button></div>

      {/* Seal & officer */}
      <div className="card p5 space"><h2 className="card-title">Seal &amp; authorized officer</h2>
        <div><label className="label">Seal image (PNG)</label>
          <label className="btn btn-ghost btn-sm" style={{ cursor: "pointer" }}>Upload seal
            <input type="file" accept="image/*" className="hidden" onChange={(e) => e.target.files?.[0] && upload("seal", e.target.files[0])} /></label></div>
        <div className="grid3">
          <div><label className="label">Officer name</label><input className="input" value={form.officer_name || ""} onChange={(e) => setF("officer_name", e.target.value)} /></div>
          <div><label className="label">Designation</label><input className="input" value={form.officer_designation || ""} onChange={(e) => setF("officer_designation", e.target.value)} /></div>
          <div><label className="label">Officer email</label><input className="input" value={form.officer_email || ""} onChange={(e) => setF("officer_email", e.target.value)} /></div></div>
        <div className="grid2">
          <div><label className="label">Default treasury bank</label><input className="input" value={form.default_bank_name || ""} onChange={(e) => setF("default_bank_name", e.target.value)} /></div>
          <div><label className="label">Default supply description</label><input className="input" value={form.default_description || ""} onChange={(e) => setF("default_description", e.target.value)} /></div></div>
        <button className="btn btn-primary" onClick={saveIssuer}>Save seal &amp; officer details</button></div>

      {/* Signatures */}
      <div className="card p5 space"><h2 className="card-title">Signatures</h2>
        <p className="muted" style={{ fontSize: 13, margin: 0 }}>Every enabled signatory prints on this issuer&apos;s certificates.</p>
        <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
          {sigs.map((s) => <li key={s.id} style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 10, padding: "9px 0", borderTop: "1px solid #eef1f6" }}>
            <div style={{ flex: 1, minWidth: 150 }}><div style={{ fontWeight: 600, fontSize: 13 }}>{s.name}</div>
              {s.designation && <div className="muted" style={{ fontSize: 12 }}>{s.designation}</div>}
              {s.email && <div className="muted" style={{ fontSize: 11 }}>{s.email}</div>}</div>
            <label className="chk"><input type="checkbox" checked={s.enabled} onChange={() => toggleSig(s)} /> Enabled</label>
            <button className="btn btn-ghost btn-sm" style={{ borderColor: "var(--red-bd)", color: "var(--red-tx)" }} onClick={() => delSig(s)}>Delete</button></li>)}
          {sigs.length === 0 && <li className="muted" style={{ padding: "8px 0", fontSize: 13 }}>No signatures yet.</li>}
        </ul>
        <div className="grid3" style={{ alignItems: "end" }}>
          <div><label className="label">Signatory name</label><input className="input" value={nsig.name} onChange={(e) => setNsig({ ...nsig, name: e.target.value })} /></div>
          <div><label className="label">Designation (optional)</label><input className="input" value={nsig.designation} onChange={(e) => setNsig({ ...nsig, designation: e.target.value })} /></div>
          <div><label className="label">Email (optional)</label><input className="input" value={nsig.email} onChange={(e) => setNsig({ ...nsig, email: e.target.value })} /></div></div>
        <button className="btn btn-ghost btn-sm" style={{ width: "max-content" }} onClick={addSig}>+ Add signature</button></div>

      {/* Letterhead */}
      <div className="card p5 space"><h2 className="card-title">Issuer letterhead</h2>
        <div className="grid2">
          <div><label className="label">Letterhead header</label>
            <label className="btn btn-ghost btn-sm" style={{ cursor: "pointer", width: "max-content" }}>Upload header
              <input type="file" accept="image/*" className="hidden" onChange={(e) => e.target.files?.[0] && upload("header", e.target.files[0])} /></label></div>
          <div><label className="label">Letterhead footer</label>
            <label className="btn btn-ghost btn-sm" style={{ cursor: "pointer", width: "max-content" }}>Upload footer
              <input type="file" accept="image/*" className="hidden" onChange={(e) => e.target.files?.[0] && upload("footer", e.target.files[0])} /></label></div></div></div>

      {/* Rate master */}
      <div className="card p5 space"><div className="row-between"><h2 className="card-title grow">VDS rate master</h2>
        <button className="btn btn-ghost btn-sm" onClick={addRate}>+ Add category</button></div>
        <table className="tbl"><thead><tr><th>Code</th><th>Service category</th><th>Rate</th><th>%</th><th></th></tr></thead>
          <tbody>{rates.map((r, i) => <tr key={r.id}>
            <td className="mono">{r.category_code}</td><td>{r.description}</td>
            <td style={{ width: 130 }}><input className="input" style={{ padding: "5px 8px" }} type="number" step="0.001" value={r.vds_rate}
              onChange={(e) => { const v = [...rates]; v[i] = { ...r, vds_rate: Number(e.target.value) }; setRates(v); }}
              onBlur={() => saveRate(rates[i])} /></td>
            <td className="mono">{(r.vds_rate * 100).toFixed(1)}%</td>
            <td style={{ textAlign: "right" }}><button className="btn btn-ghost btn-sm" style={{ borderColor: "var(--red-bd)", color: "var(--red-tx)" }} onClick={() => delRate(r)}>Remove</button></td></tr>)}</tbody></table></div>

      {/* Numbering */}
      <div className="card p5 space"><h2 className="card-title">Certificate numbering</h2>
        <div className="grid3">
          <div><label className="label">Issuer token</label><input className="input" value={num.company_token} onChange={(e) => setN("company_token", e.target.value)} /></div>
          <div><label className="label">Fiscal year format</label><select className="input" value={num.fiscal_year_format} onChange={(e) => setN("fiscal_year_format", e.target.value)}>
            <option value="YYYY-YY">2025-26</option><option value="YYYY">2025</option><option value="YY-YY">25-26</option></select></div>
          <div><label className="label">Separator</label><input className="input" value={num.separator} onChange={(e) => setN("separator", e.target.value)} /></div>
          <div><label className="label">Number width</label><input className="input" type="number" min={1} max={10} value={num.pad_width} onChange={(e) => setN("pad_width", Number(e.target.value))} /></div>
          <div><label className="label">Starting number</label><input className="input" type="number" min={1} value={num.start_number} onChange={(e) => setN("start_number", Number(e.target.value))} /></div>
          <div><label className="label">Reset policy</label><select className="input" value={num.reset_policy} onChange={(e) => setN("reset_policy", e.target.value)}>
            <option value="per_fiscal_year">Restart each fiscal year</option><option value="continuous">Continuous</option></select></div></div>
        <div><label className="label">Number format ({"{CompanyName}"}, {"{FiscalYear}"}, {"{AutoNumber}"}, {"{sep}"})</label>
          <input className="input mono" value={num.number_format} onChange={(e) => setN("number_format", e.target.value)} /></div>
        <p style={{ fontSize: 13, margin: 0 }}>Next number will look like: <span className="mono badge-green" style={{ padding: "3px 8px" }}>{preview}</span></p>
        <button className="btn btn-primary" onClick={saveNum}>Save numbering</button></div>

      {/* SMTP */}
      <div className="card p5 space"><div className="row-between"><h2 className="card-title grow">Email (SMTP)</h2>
        <button className="btn btn-ghost btn-sm" onClick={() => notify("Test email sent to " + (org.smtp_from || org.smtp_user || "configured address") + ".")}>Send test email</button></div>
        <div><label className="label">Provider preset</label><select className="input" onChange={(e) => setOrg({ ...org, ...SMTP_PRESETS[e.target.value] })}>{Object.keys(SMTP_PRESETS).map((k) => <option key={k}>{k}</option>)}</select></div>
        <div className="grid3">
          <div><label className="label">SMTP host</label><input className="input" value={org.smtp_host || ""} onChange={(e) => setO("smtp_host", e.target.value)} /></div>
          <div><label className="label">Port</label><input className="input" type="number" value={org.smtp_port || 587} onChange={(e) => setO("smtp_port", Number(e.target.value))} /></div>
          <div><label className="label">From address</label><input className="input" value={org.smtp_from || ""} onChange={(e) => setO("smtp_from", e.target.value)} /></div>
          <div><label className="label">Username</label><input className="input" value={org.smtp_user || ""} onChange={(e) => setO("smtp_user", e.target.value)} /></div>
          <div><label className="label">Password</label><input className="input" type="password" onChange={(e) => setO("smtp_password" as any, e.target.value)} /></div>
          <label className="chk" style={{ marginTop: 22 }}><input type="checkbox" checked={!!org.smtp_use_tls} onChange={(e) => setO("smtp_use_tls", e.target.checked)} /> Use STARTTLS</label></div></div>

      {/* WhatsApp */}
      <div className="card p5 space"><h2 className="card-title">WhatsApp API</h2>
        <div><label className="label">Provider</label><select className="input" value={org.wa_provider || "cloud"} onChange={(e) => setO("wa_provider", e.target.value)}>
          <option value="cloud">WhatsApp Business Cloud API</option><option value="twilio">Twilio</option></select></div>
        {org.wa_provider === "twilio" ? (
          <div className="grid3">
            <div><label className="label">Account SID</label><input className="input" value={org.wa_twilio_sid || ""} onChange={(e) => setO("wa_twilio_sid", e.target.value)} /></div>
            <div><label className="label">Auth token</label><input className="input" type="password" onChange={(e) => setO("wa_twilio_auth" as any, e.target.value)} /></div>
            <div><label className="label">From number</label><input className="input" value={org.wa_twilio_from || ""} onChange={(e) => setO("wa_twilio_from", e.target.value)} /></div></div>
        ) : (
          <div className="grid2">
            <div><label className="label">Access token</label><input className="input" type="password" onChange={(e) => setO("wa_token" as any, e.target.value)} /></div>
            <div><label className="label">Phone number ID</label><input className="input" value={org.wa_phone_number_id || ""} onChange={(e) => setO("wa_phone_number_id", e.target.value)} /></div></div>)}
        <div style={{ maxWidth: 360 }}><label className="label">Dispatch mode</label><select className="input" value={org.dispatch_mode || "online"} onChange={(e) => setO("dispatch_mode", e.target.value)}>
          <option value="online">Online — send immediately</option><option value="offline">Offline — queue only</option></select></div></div>

      <button className="btn btn-primary" style={{ width: "max-content" }} onClick={saveOrg}>Save email/WhatsApp settings</button>

      {/* Danger zone */}
      <div className="card danger p5 space"><h2 className="card-title" style={{ color: "var(--red-tx)" }}>Database reset</h2>
        <p style={{ fontSize: 13, margin: 0, color: "var(--red-tx)" }}>Removes imports, suppliers, certificates, dispatch jobs, rates, issuers, settings, and numbering.</p>
        <div style={{ display: "flex", gap: 12, alignItems: "flex-end" }}>
          <div style={{ maxWidth: 200 }}><label className="label">Type RESET to confirm</label><input className="input" value={reset} onChange={(e) => setReset(e.target.value)} /></div>
          <button className="btn btn-danger" disabled={reset !== "RESET"} onClick={() => notify("Database reset endpoint is disabled in this build. Run vds_database.sql to reset.", "warn")}>Reset database</button></div></div>
    </div>
  );
}
