import type { ReactNode } from "react";
import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";
import { Providers } from "./providers";
import { TopBar } from "./topbar";

export const metadata: Metadata = { title: "J.A.R.V.I.S. — Incident Intelligence", description: "Ten alerts, one cause." };

const NAV = [
  { href: "/", label: "Overview" },
  { href: "/sources", label: "Sources" },
  { href: "/benchmark", label: "Benchmark" },
  { href: "/topology", label: "Topology" },
];

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body>
        <Providers>
          <div className="flex min-h-screen">
            <aside className="w-56 shrink-0 border-r border-border bg-card p-4">
              <Link href="/" className="text-lg font-bold tracking-wide">J.A.R.V.I.S.</Link>
              <p className="mt-1 text-xs text-muted">Incident intelligence</p>
              <nav className="mt-6 space-y-1" aria-label="Main navigation">
                {NAV.map((n) => (
                  <Link key={n.href} href={n.href} className="block rounded-md px-3 py-2 text-sm hover:bg-raised focus:outline-none focus:ring-2 focus:ring-trace">{n.label}</Link>
                ))}
              </nav>
            </aside>
            <div className="min-w-0 flex-1">
              <TopBar />
              <main className="p-6">{children}</main>
            </div>
          </div>
        </Providers>
      </body>
    </html>
  );
}
