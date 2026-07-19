"use client";
import { useState } from "react";
import { api } from "@/lib/api";
import { useApp } from "@/lib/auth";
import { useToast } from "@/components/ui/Toast";
import UploadDropzone from "@/components/import/UploadDropzone";
import ValidationReport from "@/components/import/ValidationReport";
import type { ImportResult } from "@/types/models";

export default function ImportPage() {
  const { issuerId } = useApp();
  const notify = useToast();
  const [batch, setBatch] = useState<ImportResult | null>(null);
  const [busy, setBusy] = useState(false);

  async function onFile(file: File) {
    if (!issuerId) return notify("Select an issuer first.", "warn");
    setBusy(true);
    try { setBatch(await api.importFile(issuerId, file)); notify("Workbook parsed."); }
    catch (e: any) { notify(e.message, "err"); }
    finally { setBusy(false); }
  }

  return (
    <div className="stack">
      <div className="card p5 row-between">
        <div><div className="card-title">Mushak-6.6 Summary workbook</div>
          <p className="muted" style={{ margin: "6px 0 0" }}>
            Upload the .xlsx. Rows are parsed and validated; Value (Excl.) = VAT ÷ rate, Value (Incl.) = Excl. + VAT.</p></div>
        <UploadDropzone busy={busy} hasData={!!batch} onFile={onFile} />
      </div>
      {!batch && !busy && <div className="card p5" style={{ textAlign: "center", color: "var(--muted)" }}>No file uploaded yet — choose an .xlsx to review the parsed sheet.</div>}
      {batch && <ValidationReport batch={batch} />}
    </div>
  );
}
