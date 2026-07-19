"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, setToken } from "@/lib/api";
import { useApp } from "@/lib/auth";
import VdsMark from "@/components/VdsMark";

export default function LoginPage() {
  const router = useRouter();
  const { refreshIssuers } = useApp();
  const [u, setU] = useState("admin");
  const [p, setP] = useState("admin");
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit() {
    setBusy(true); setErr(null);
    try {
      const res = await api.login(u, p);
      setToken(res.access_token);
      await refreshIssuers();
      router.replace("/dashboard");
    } catch (e: any) { setErr(e.message || "Login failed"); }
    finally { setBusy(false); }
  }

  return (
    <div className="login">
      <div className="login-card">
        <VdsMark size={60} />
        <h1>VDS</h1>
        <p>VAT Deduction at Source · Mushak-6.6 certificates</p>
        <input className="input" placeholder="Username" value={u} onChange={(e) => setU(e.target.value)} />
        <input className="input" type="password" placeholder="Password" value={p}
          onChange={(e) => setP(e.target.value)} onKeyDown={(e) => e.key === "Enter" && submit()} />
        {err && <div className="notice n-err" style={{ marginTop: 10 }}>{err}</div>}
        <button className="btn btn-primary" style={{ width: "100%", marginTop: 12, padding: 11 }}
          disabled={busy} onClick={submit}>{busy ? "Signing in..." : "Sign in"}</button>
      </div>
    </div>
  );
}
