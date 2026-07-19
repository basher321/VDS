import "./globals.css";
import type { Metadata } from "next";
import { AppProvider } from "@/lib/auth";
import { ToastProvider } from "@/components/ui/Toast";
import AppShell from "@/components/AppShell";

export const metadata: Metadata = { title: "VDS — VAT Deduction at Source", description: "Mushak-6.6 certificates" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AppProvider>
          <ToastProvider>
            <AppShell>{children}</AppShell>
          </ToastProvider>
        </AppProvider>
      </body>
    </html>
  );
}
