"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Bitcoin, LayoutDashboard, MessageSquare, Newspaper, BarChart3, FileText, Settings, CandlestickChart, LogOut, TrendingUp, Menu, X, Database, Waves, Globe, Cpu } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/components/auth-provider";
import { useI18n } from "@/lib/i18n";

const navItems = [
  { href: "/dashboard", key: "nav.dashboard", icon: LayoutDashboard },
  { href: "/dashboard/data", key: "nav.dataExplorer", icon: Database },
  { href: "/dashboard/chart", key: "nav.chart", icon: CandlestickChart },
  { href: "/dashboard/correlations", key: "nav.correlations", icon: TrendingUp },
  { href: "/dashboard/whales", key: "nav.whales", icon: Waves },
  { href: "/dashboard/training", key: "nav.training", icon: Cpu },
  { href: "/chat", key: "nav.chat", icon: MessageSquare },
  { href: "/news", key: "nav.news", icon: Newspaper },
  { href: "/models", key: "nav.models", icon: BarChart3 },
  { href: "/reports", key: "nav.reports", icon: FileText },
  { href: "/settings", key: "nav.settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, signOut } = useAuth();
  const { t, lang, setLang } = useI18n();
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleSignOut = async () => {
    await signOut();
    router.push("/login");
  };

  const sidebarContent = (
    <>
      <div className="flex h-16 items-center gap-2 border-b border-border px-6">
        <Bitcoin className="h-7 w-7 text-primary" />
        <span className="text-lg font-bold text-foreground">BTC AI</span>
        <button onClick={() => setMobileOpen(false)} className="ml-auto lg:hidden text-muted-foreground hover:text-foreground">
          <X className="h-5 w-5" />
        </button>
      </div>

      <nav className="flex-1 space-y-1 p-3 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.href || pathname.startsWith(item.href + "/");
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setMobileOpen(false)}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                active
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-secondary hover:text-foreground"
              )}
            >
              <Icon className="h-4 w-4" />
              {t(item.key)}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-border p-4">
        <div className="flex items-center gap-2 mb-3">
          <button
            onClick={() => setLang(lang === "fr" ? "en" : "fr")}
            className="flex items-center gap-1.5 rounded-lg border border-border px-2.5 py-1.5 text-xs text-muted-foreground hover:bg-secondary hover:text-foreground transition-colors"
          >
            <Globe className="h-3.5 w-3.5" />
            {lang === "fr" ? "EN" : "FR"}
          </button>
        </div>
        <div className="flex items-center gap-3 mb-3">
          <div className="h-8 w-8 rounded-full bg-primary/20 flex items-center justify-center text-primary text-sm font-medium">
            {(user?.email?.[0] || "A").toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-foreground truncate">
              {user?.email || t("nav.analyst")}
            </p>
            <p className="text-xs text-muted-foreground truncate">{t("nav.btcAnalyst")}</p>
          </div>
        </div>
        <button
          onClick={handleSignOut}
          className="flex items-center gap-2 w-full rounded-lg px-3 py-2 text-xs text-muted-foreground hover:bg-secondary hover:text-foreground transition-colors"
        >
          <LogOut className="h-3.5 w-3.5" />
          {t("nav.signOut")}
        </button>
      </div>
    </>
  );

  return (
    <>
      {/* Mobile hamburger */}
      <button
        onClick={() => setMobileOpen(true)}
        className="fixed top-4 left-4 z-40 lg:hidden h-10 w-10 rounded-lg border border-border bg-card flex items-center justify-center"
      >
        <Menu className="h-5 w-5 text-foreground" />
      </button>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Desktop sidebar */}
      <aside className="fixed left-0 top-0 z-30 hidden h-screen w-60 flex-col border-r border-border bg-card lg:flex">
        {sidebarContent}
      </aside>

      {/* Mobile sidebar */}
      {mobileOpen && (
        <aside className="fixed left-0 top-0 z-50 flex h-screen w-64 flex-col border-r border-border bg-card lg:hidden animate-fade-in">
          {sidebarContent}
        </aside>
      )}
    </>
  );
}
