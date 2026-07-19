"use client";
import { money } from "@/lib/validators";
import type { ImportResult } from "@/types/models";

const COLS = ["SL", "Supplier's Name", "BIN", "Challan No.", "Service", "Deducted VAT", "Rate", "Value (Excl.)", "Value (Incl.)", "Status"];

export default function ValidationReport({ batch }: { batch: ImportResult }) {
  return (
    <div className="card">
      <div className="card-head">
        <span className="card-title">{batch.filename}</span>
        <span className="badge-green">{batch.ok_rows} imported</span>
        {batch.error_rows > 0 && <span className="badge-red">{batch.error_rows} skipped</span>}
        <span className="grow" /><span className="muted">{batch.total_rows} rows</span>
      </div>
      <div style={{ overflow: "auto" }}>
        <table className="tbl" style={{ minWidth: "max-content" }}>
          <thead><tr>{COLS.map((c) => <th key={c}>{c}</th>)}</tr></thead>
          <tbody>
            {batch.rows.map((r) => (
              <tr key={r.excel_row} className={r.error ? "err-row" : ""} title={r.error || ""}>
                <td>{r.excel_row}</td><td>{r.supplier_name}</td><td>{r.supplier_bin || "—"}</td>
                <td className="mono">{r.treasury_challan_no || "—"}</td><td>{r.category}</td>
                <td className="mono">{money(r.deducted_vat)}</td>
                <td className="mono">{r.vat_rate != null ? (r.vat_rate * 100).toFixed(1) + "%" : ""}</td>
                <td className="mono">{r.value_excl != null ? money(r.value_excl) : "—"}</td>
                <td className="mono">{r.value_incl != null ? money(r.value_incl) : "—"}</td>
                <td>{r.error ? <span className="badge-red">{r.error}</span> : <span className="badge-green">valid</span>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
