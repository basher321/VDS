"use client";
import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { api, getActiveIssuer, setActiveIssuer } from "./api";
import type { Issuer } from "@/types/models";

interface Ctx {
  issuers: Issuer[]; issuerId: number | null; setIssuer: (id: number) => void;
  refreshIssuers: () => Promise<Issuer[]>; ready: boolean;
}
const AuthCtx = createContext<Ctx>({} as any);
export const useApp = () => useContext(AuthCtx);

export function AppProvider({ children }: { children: ReactNode }) {
  const [issuers, setIssuers] = useState<Issuer[]>([]);
  const [issuerId, setIssuerId] = useState<number | null>(null);
  const [ready, setReady] = useState(false);

  const refreshIssuers = async () => {
    const list: Issuer[] = await api.listIssuers();
    setIssuers(list);
    const active = getActiveIssuer();
    const chosen = list.find((i) => i.id === active) || list.find((i) => i.is_default) || list[0];
    if (chosen) { setIssuerId(chosen.id); setActiveIssuer(chosen.id); }
    return list;
  };

  useEffect(() => {
    if (typeof window === "undefined") return;
    if (!localStorage.getItem("vds_token")) { setReady(true); return; }
    refreshIssuers().finally(() => setReady(true));
  }, []);

  const setIssuer = (id: number) => { setActiveIssuer(id); setIssuerId(id); };
  return <AuthCtx.Provider value={{ issuers, issuerId, setIssuer, refreshIssuers, ready }}>{children}</AuthCtx.Provider>;
}
