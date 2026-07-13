"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { Database, Columns, HardDrive, TrendingUp, Activity, Wifi, WifiOff, BarChart3, MessageSquare, Newspaper, CandlestickChart, Cpu, CheckCircle, XCircle, Waves } from "lucide-react";
import { formatNumber } from "@/lib/utils";
import { PriceTicker } from "@/components/price-ticker";
import { useI18n } from "@/lib/i18n";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SkeletonCard } from "@/components/ui/skeleton";
import Link from "next/link";

export default function DashboardPage() {
  const { t } = useI18n();
  const [stats, setStats] = useState<any>(null);
  const [schema, setSchema] = useState<any>(null);
  const [health, setHealth] = useState<any>(null);
  const [correlations, setCorrelations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      apiFetch<any>("/api/data/stats").catch(() => null),
      apiFetch<any>("/api/data/schema").catch(() => null),
      apiFetch<any>("/health").catch(() => null),
      apiFetch<any[]>("/api/data/correlations?top_n=5").catch(() => []),
    ]).then(([s, sch, h, corrs]) => {
      setStats(s);
      setSchema(sch);
      setHealth(h);
      setCorrelations(corrs || []);
      setLoading(false);
    });
  }, []);

  const apiOnline = health?.status === "ok";
  const components = health?.components || {};
  const llmInfo = components?.llm || {};

  const cards = [
    { label: t("dashboard.totalRows"), value: formatNumber(stats?.n_rows || 0, 0), icon: Database, color: "text-blue-400" },
    { label: t("dashboard.columns"), value: stats?.n_columns || 0, icon: Columns, color: "text-purple-400" },
    { label: t("dashboard.fileSize"), value: `${stats?.file_size_mb || 0} MB`, icon: HardDrive, color: "text-green-400" },
    { label: t("dashboard.features"), value: (schema?.columns?.filter((c: any) => !c.name.startsWith("target_") && c.name !== "timestamp").length) || 0, icon: TrendingUp, color: "text-orange-400" },
    { label: t("dashboard.targets"), value: (schema?.columns?.filter((c: any) => c.name.startsWith("target_")).length) || 0, icon: Activity, color: "text-red-400" },
  ];

  const quickActions = [
    { href: "/chat", icon: MessageSquare, title: t("dashboard.actChat"), desc: t("dashboard.actChatDesc") },
    { href: "/dashboard/correlations", icon: BarChart3, title: t("dashboard.actCorrelations"), desc: t("dashboard.actCorrelationsDesc") },
    { href: "/dashboard/chart", icon: CandlestickChart, title: t("dashboard.actChart"), desc: t("dashboard.actChartDesc") },
    { href: "/news", icon: Newspaper, title: t("dashboard.actNews"), desc: t("dashboard.actNewsDesc") },
    { href: "/dashboard/data", icon: Database, title: t("dashboard.actData"), desc: t("dashboard.actDataDesc") },
    { href: "/dashboard/whales", icon: Waves, title: t("dashboard.actWhales"), desc: t("dashboard.actWhalesDesc") },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">{t("dashboard.title")}</h1>
          <p className="text-sm text-muted-foreground mt-1">{t("dashboard.subtitle")}</p>
        </div>
        <Badge variant={apiOnline ? "success" : "destructive"} className="flex items-center gap-1.5">
          {apiOnline ? <Wifi className="h-3 w-3" /> : <WifiOff className="h-3 w-3" />}
          {apiOnline ? t("dashboard.apiOnline") : t("dashboard.apiOffline")}
        </Badge>
      </div>

      <PriceTicker />

      {/* Stats cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {loading
          ? Array.from({ length: 5 }).map((_, i) => <SkeletonCard key={i} />)
          : cards.map((card) => {
              const Icon = card.icon;
              return (
                <Card key={card.label} className="p-5 animate-fade-in">
                  <div className="flex items-center justify-between mb-3">
                    <Icon className={`h-5 w-5 ${card.color}`} />
                  </div>
                  <p className="text-2xl font-bold text-foreground">{card.value}</p>
                  <p className="text-xs text-muted-foreground mt-1">{card.label}</p>
                </Card>
              );
            })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Top correlations */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-primary" />
              {t("dashboard.topCorrelations")}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-2">
                {Array.from({ length: 5 }).map((_, i) => (
                  <div key={i} className="h-8 bg-secondary/50 rounded animate-pulse" />
                ))}
              </div>
            ) : correlations.length > 0 ? (
              <div className="space-y-2">
                {correlations.map((c, i) => (
                  <div key={i} className="flex items-center gap-3">
                    <span className="text-xs text-muted-foreground w-4">{i + 1}</span>
                    <span className="text-sm text-foreground flex-1 truncate font-mono">{c.feature}</span>
                    <div className="flex items-center gap-2 w-28">
                      <div className="flex-1 h-2 bg-secondary rounded-full overflow-hidden">
                        <div
                          className="h-full bg-primary rounded-full"
                          style={{ width: `${Math.min(Math.abs(c.correlation || 0) * 100, 100)}%` }}
                        />
                      </div>
                      <span className="text-xs font-medium text-foreground w-12 text-right">
                        {c.correlation != null ? Number(c.correlation).toFixed(3) : "N/A"}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground text-center py-4">{t("dashboard.noCorrelations")}</p>
            )}
          </CardContent>
        </Card>

        {/* System health */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Cpu className="h-5 w-5 text-primary" />
              {t("dashboard.systemHealth")}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-2">
                {Array.from({ length: 4 }).map((_, i) => (
                  <div key={i} className="h-6 bg-secondary/50 rounded animate-pulse" />
                ))}
              </div>
            ) : (
              <div className="space-y-2">
                {[
                  { name: "DuckDB", status: components.duckdb?.status === "ok" },
                  { name: "Supabase", status: components.supabase?.status === "ok" },
                  { name: "Gemini LLM", status: !!llmInfo.gemini },
                  { name: "Anthropic", status: !!llmInfo.anthropic },
                  { name: "Whale DB", status: components.whales?.status === "ok" },
                ].map((svc) => (
                  <div key={svc.name} className="flex items-center justify-between">
                    <span className="text-sm text-foreground">{svc.name}</span>
                    {svc.status ? (
                      <Badge variant="success" className="flex items-center gap-1">
                        <CheckCircle className="h-3 w-3" />
                        {t("dashboard.ok")}
                      </Badge>
                    ) : (
                      <Badge variant="destructive" className="flex items-center gap-1">
                        <XCircle className="h-3 w-3" />
                        {t("dashboard.off")}
                      </Badge>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Quick actions */}
        <Card>
          <CardHeader>
            <CardTitle>{t("dashboard.quickActions")}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {quickActions.map((action) => {
                const Icon = action.icon;
                return (
                  <Link key={action.href} href={action.href} className="block rounded-lg border border-border bg-secondary/50 p-3 hover:bg-secondary transition-colors group">
                    <div className="flex items-center gap-3">
                      <Icon className="h-4 w-4 text-primary flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-foreground">{action.title}</p>
                        <p className="text-xs text-muted-foreground truncate">{action.desc}</p>
                      </div>
                    </div>
                  </Link>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Columns list */}
      <Card>
        <CardHeader>
          <CardTitle>{t("dashboard.columnsDataset")} ({schema?.columns?.length || 0})</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-1 max-h-80 overflow-y-auto">
            {loading ? (
              Array.from({ length: 12 }).map((_, i) => (
                <div key={i} className="h-8 bg-secondary/50 rounded animate-pulse" />
              ))
            ) : (
              schema?.columns?.map((col: any) => (
                <div
                  key={col.name}
                  className="flex items-center justify-between py-1.5 px-2 rounded hover:bg-secondary/50 text-sm"
                >
                  <span className={`truncate ${col.name.startsWith("target_") ? "text-orange-400" : "text-foreground"}`}>
                    {col.name}
                  </span>
                  <Badge variant="outline" className="font-mono text-xs ml-1 flex-shrink-0">{col.type}</Badge>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
