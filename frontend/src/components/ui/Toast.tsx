"use client";
import { createContext, useCallback, useContext, useState, ReactNode } from "react";

type Kind = "ok" | "warn" | "err";
const ToastCtx = createContext<(msg: string, kind?: Kind) => void>(() => {});
export const useToast = () => useContext(ToastCtx);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toast, setToast] = useState<{ msg: string; kind: Kind } | null>(null);
  const notify = useCallback((msg: string, kind: Kind = "ok") => {
    setToast({ msg, kind });
    setTimeout(() => setToast(null), 3500);
  }, []);
  return (
    <ToastCtx.Provider value={notify}>
      {children}
      {toast && <div className={`toast notice n-${toast.kind}`}>{toast.msg}</div>}
    </ToastCtx.Provider>
  );
}
