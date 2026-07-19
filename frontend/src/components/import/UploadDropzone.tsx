"use client";
import { useRef } from "react";

export default function UploadDropzone({ busy, hasData, onFile }:
  { busy: boolean; hasData: boolean; onFile: (f: File) => void }) {
  const ref = useRef<HTMLInputElement>(null);
  return (
    <>
      <button className="btn btn-primary" disabled={busy} onClick={() => ref.current?.click()}>
        {busy ? "Parsing..." : hasData ? "Replace file" : "Upload .xlsx file"}
      </button>
      <input ref={ref} type="file" accept=".xlsx" className="hidden"
        onChange={(e) => { const f = e.target.files?.[0]; if (f) onFile(f); e.currentTarget.value = ""; }} />
    </>
  );
}
