"use client";
import { usePathname, useRouter } from "next/navigation";
import Link from "next/link";
import { ReactNode, useEffect } from "react";
import { getToken, clearToken } from "@/lib/api";
import { useApp } from "@/lib/auth";
import VdsMark from "./VdsMark";

const NAV = [
  { href: "/dashboard", lab: "Dashboard", kick: "Control center" },
  { href: "/settings/organization", lab: "Settings", kick: "Issuer & rates" },
  { href: "/import", lab: "Import", kick: "Mushak-6.6 intake" },
  { href: "/certificates", lab: "Certificate Issue", kick: "Generate & send" },
];
const TITLES: Record<string, [string, string]> = {
  "/dashboard": ["Dashboard", "Overview of VDS deductions and issued Mushak-6.6 certificates."],
  "/settings/organization": ["Settings", "Issuer identity, VDS rate master, numbering, dispatch, and data controls."],
  "/import": ["Import", "Load the Mushak-6.6 Summary workbook with row-level validation."],
  "/certificates": ["Certificate Issue", "Generate, preview, print, and dispatch Mushak-6.6 certificates."],
};

export default function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { issuers, issuerId, setIssuer } = useApp();

  useEffect(() => {
    if (pathname !== "/login" && !getToken()) router.replace("/login");
  }, [pathname]);

  if (pathname === "/login") return <>{children}</>;

  const active = NAV.find((n) => pathname.startsWith(n.href))?.href || "/dashboard";
  const [title, desc] = TITLES[active] || TITLES["/dashboard"];

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="sb-top"><VdsMark /><div><div className="t">VDS</div><div className="s">VAT Deduction at Source</div></div></div>
        <div className="sb-badge"><span className="dot" /> Mushak-6.6 workflow</div>
        <nav className="nav">
          {NAV.map((n) => (
            <Link key={n.href} href={n.href} className={pathname.startsWith(n.href) ? "active" : ""}>
              <span className="lab">{n.lab}</span><span className="kick">{n.kick}</span>
            </Link>
          ))}
        </nav>
        <div className="sb-foot">Local VDS module<span className="mono">localhost:3000</span>
          <a style={{ cursor: "pointer", display: "block", marginTop: 6 }}
             onClick={() => { clearToken(); router.replace("/login"); }}>Log out</a></div>
      </aside>
      <div className="body">
        <header className="topbar">
          <div><div className="k">VDS certificate module</div><h1>{title}</h1><p>{desc}</p></div>
          <div className="right">
            <div style={{ textAlign: "right" }}>
              <span className="label" style={{ marginBottom: 2 }}>Issuer</span>
              <select className="input" style={{ width: 230, padding: "6px 9px" }} value={issuerId ?? ""}
                onChange={(e) => { setIssuer(Number(e.target.value)); location.reload(); }}>
                {issuers.map((i) => <option key={i.id} value={i.id}>{i.name}{i.is_default ? " (default)" : ""}</option>)}
              </select>
            </div>
            <div className="sys"><b>System ready</b>API connected</div>
          </div>
        </header>
        <main className="main">{children}</main>
      </div>
    </div>
  );
}
