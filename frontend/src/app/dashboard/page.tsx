"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { bdt } from "@/lib/validators";
import type { DashboardData } from "@/types/models";

function Stat({ v, l, t }: { v: any; l: string; t: string }) {
  return (
    <div className="card p5"><div className="row-between" style={{ alignItems: "flex-start" }}>
      <div><div className="mono" style={{ fontSize: 24 }}>{v}</div><div className="muted" style={{ marginTop: 4, fontSize: 13 }}>{l}</div></div>
      <span className="badge-rule">{t}</span></div></div>
  );
}

export default function Dashboard() {
  const [d, setD] = useState<DashboardData | null>(null);
  const [err, setErr] = useState<string | null>(null);
  useEffect(() => { api.dashboard().then(setD).catch((e) => setErr(e.message)); }, []);
  if (err) return <div className="notice n-err">Couldn&apos;t load summary: {err}</div>;
  if (!d) return <p className="muted">Loading…</p>;

  const issued = d.certificates.generated + d.certificates.sent;
  const total = issued + d.pending_groups;
  const comp = total ? Math.min(100, (issued / total) * 100) : 0;

  return (
    <div className="stack">
      <div className="grid3">
        <div className="card p5" style={{ gridColumn: "span 2" }}>
          <div className="row-between" style={{ alignItems: "flex-start" }}>
            <div><p className="muted" style={{ fontWeight: 500 }}>Current workload</p>
              <div style={{ display: "flex", alignItems: "flex-end", gap: 12, marginTop: 10 }}>
                <span className="mono" style={{ fontSize: 44, lineHeight: 1 }}>{d.pending_groups}</span>
                <span className="muted" style={{ paddingBottom: 5 }}>supplier groups awaiting certificate</span></div></div>
            <span className={`badge ${d.pending_groups ? "badge-amber" : "badge-green"}`}>{d.pending_groups ? "Issue pending" : "No backlog"}</span>
          </div>
          <div style={{ height: 8, borderRadius: 5, background: "var(--rule)", marginTop: 16, overflow: "hidden" }}>
            <div style={{ height: 8, background: "var(--accent)", width: `${comp}%` }} /></div>
          <div className="row-between muted" style={{ marginTop: 8, fontSize: 12 }}>
            <span className="grow">{issued} issued</span><span>{d.pending_groups} remaining</span></div>
        </div>
        <div className="card p5"><p className="muted" style={{ fontWeight: 500 }}>Generated status</p>
          <div style={{ marginTop: 10 }} className="space">
            <div className="row-between"><span className="grow">Generated</span><span className="mono">{d.certificates.generated}</span></div>
            <div className="row-between"><span className="grow">Sent</span><span className="mono">{d.certificates.sent}</span></div>
            <div className="row-between" style={{ borderTop: "1px solid var(--rule)", paddingTop: 8, fontWeight: 600 }}>
              <span className="grow">Total</span><span className="mono">{issued}</span></div></div></div>
      </div>
      <div className="grid3">
        <Stat v={d.imported_lines} l="Imported invoice lines" t="Ready" />
        <Stat v={d.suppliers} l="Suppliers on file" t="Validated" />
        <Stat v={issued} l="Certificates issued" t={`${d.certificates.sent} sent`} />
        <Stat v={d.pending_groups} l="Pending groups" t="Awaiting issue" />
        <Stat v={bdt(d.total_vat_withheld)} l="Total VAT withheld" t="Source total" />
        <Stat v={d.queued_dispatches} l="Dispatch queue" t={d.queued_dispatches ? "Action needed" : "Clear"} />
      </div>
    </div>
  );
}
