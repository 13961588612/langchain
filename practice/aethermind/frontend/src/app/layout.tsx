import type { Metadata } from "next";
import "./globals.css";
import Link from "next/link";

export const metadata: Metadata = {
  title: "AetherMind - Agent Work Platform",
  description: "Create, configure, and orchestrate AI agents",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body>
        <nav className="sticky top-0 z-50 border-b border-gray-200 bg-white/80 backdrop-blur-sm">
          <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4">
            <Link href="/" className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-600 text-white font-bold text-sm">
                AM
              </div>
              <span className="text-lg font-semibold text-gray-900">
                AetherMind
              </span>
            </Link>
            <div className="flex items-center gap-3">
              <Link href="/agents" className="text-sm text-gray-600 hover:text-gray-900 transition-colors">
                Agents
              </Link>
              <Link href="/agents/new" className="btn-primary text-xs">
                + New Agent
              </Link>
            </div>
          </div>
        </nav>
        <main className="mx-auto max-w-7xl px-4 py-6">{children}</main>
      </body>
    </html>
  );
}
