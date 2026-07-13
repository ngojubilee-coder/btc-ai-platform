"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from "recharts";
import { ArrowLeft, BarChart3, TrendingUp, Clock, Target, Cpu, Activity } from "lucide-react";

const C = {
  grid: "hsl(217 33% 20%)",
  axis: "hsl(215 20% 65%)",
  text: "hsl(213 31% 91%)",
  bar: "hsl(199 89% 48%)",
  cardBg: "hsl(222 47% 11%)",
  border: "hsl(217 33% 20%)",
};
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { SkeletonCard, SkeletonRow } from "@/components/ui/skeleton";
import { formatDate } from "@/lib/utils";
import { useI18n } from "@/lib/i18n";

export default function ModelDetailPage() {
  const { t } = useI18n();
  const params = useParams();
  const router = useRouter();
  const [model, setModel] = useState<any>(null);
  const [features, setFeatures] = useState<any[]>([]);
  const [backtests, setBacktests] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const id = params.id as string;
    Promise.all([
      apiFetch<any>(`/api/models/${id}`).catch(() => null),
      apiFetch<any[]>(`/api/models/${id}/features`).catch(() => []),
      apiFetch<any[]>(`/api/models/${id}/backtests`).catch(() => []),
    ]).then(([m, f, b]) => {
      setModel(m);
      setFeatures(f || []);
      setBacktests(b || []);
      setLoading(false);
    });
  }, [params.id]);

  if (loading) {
    return (
      <div className="space-y-6">
        <SkeletonCard />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <SkeletonCard />
          <SkeletonCard />
        </div>
      </div>
    );
  }

  if (!model || model.error) {
    return (
      <div className="text-center py-20">
        <BarChart3 className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
        <p className="text-foreground font-medium">{t("models.notFound")}</p>
        <Button variant="outline" size="sm" className="mt-4" onClick={() => router.push("/models")}>
          <ArrowLeft className="h-4 w-4 mr-1" /> {t("models.backToModels")}
        </Button>
      </div>
    );
  }

  const metrics = model.metrics || {};
  const metricEntries = Object.entries(metrics).filter(([, v]) => typeof v === "number");
  const radarData = metricEntries.slice(0, 6).map(([k, v]: any) => ({
    metric: k,
    value: Math.min(Math.abs(v) * 100, 100),
  }));

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.push("/models")}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-foreground">{model.model_name}</h1>
            <Badge variant="secondary">v{model.version}</Badge>
            <Badge variant={model.status === "completed" ? "success" : model.status === "failed" ? "destructive" : "warning"}>
              {t(`models.status${(model.status || "unknown").charAt(0).toUpperCase() + (model.status || "unknown").slice(1)}`)}
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            {model.model_type} · {model.asset} · {formatDate(model.created_at)}
          </p>
        </div>
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: t("models.trainLoss"), value: model.train_loss != null ? Number(model.train_loss).toFixed(4) : "N/A", icon: TrendingUp, color: "text-blue-400" },
          { label: t("models.valLoss"), value: model.val_loss != null ? Number(model.val_loss).toFixed(4) : "N/A", icon: Activity, color: "text-orange-400" },
          { label: t("models.target"), value: model.target_col || "N/A", icon: Target, color: "text-purple-400" },
          { label: t("models.features"), value: model.features_used?.length || 0, icon: Cpu, color: "text-green-400" },
        ].map((s) => {
          const Icon = s.icon;
          return (
            <Card key={s.label} className="p-4">
              <Icon className={`h-4 w-4 ${s.color} mb-2`} />
              <p className="text-lg font-bold text-foreground">{s.value}</p>
              <p className="text-xs text-muted-foreground">{s.label}</p>
            </Card>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Feature importance chart */}
        <Card>
          <CardHeader>
            <CardTitle>{t("models.featureImportance")}</CardTitle>
          </CardHeader>
          <CardContent>
            {features.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-8">{t("models.noFeatures")}</p>
            ) : (
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={features.slice(0, 15)} layout="vertical" margin={{ left: 100 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={C.grid} />
                  <XAxis type="number" tick={{ fill: C.axis, fontSize: 11 }} stroke={C.grid} />
                  <YAxis type="category" dataKey="feature_name" tick={{ fill: C.text, fontSize: 10 }} stroke={C.grid} width={100} />
                  <Tooltip
                    contentStyle={{ backgroundColor: C.cardBg, border: `1px solid ${C.border}`, borderRadius: "8px", color: C.text }}
                    formatter={(v: any) => Number(v).toFixed(4)}
                  />
                  <Bar dataKey="importance" fill={C.bar} radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        {/* Metrics radar */}
        <Card>
          <CardHeader>
            <CardTitle>{t("models.metrics")}</CardTitle>
          </CardHeader>
          <CardContent>
            {radarData.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-8">{t("models.noMetrics")}</p>
            ) : (
              <ResponsiveContainer width="100%" height={400}>
                <RadarChart data={radarData}>
                  <PolarGrid stroke={C.grid} />
                  <PolarAngleAxis dataKey="metric" tick={{ fill: C.text, fontSize: 11 }} />
                  <PolarRadiusAxis tick={{ fill: C.axis, fontSize: 10 }} />
                  <Radar dataKey="value" stroke={C.bar} fill={C.bar} fillOpacity={0.3} />
                  <Tooltip
                    contentStyle={{ backgroundColor: C.cardBg, border: `1px solid ${C.border}`, borderRadius: "8px", color: C.text }}
                  />
                </RadarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Hyperparams + Training periods */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>{t("models.hyperparameters")}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-1">
              {Object.entries(model.hyperparams || {}).length === 0 ? (
                <p className="text-sm text-muted-foreground">{t("models.noHyperparams")}</p>
              ) : (
                Object.entries(model.hyperparams).map(([k, v]) => (
                  <div key={k} className="flex items-center justify-between py-1.5 px-2 rounded hover:bg-secondary/50 text-sm">
                    <span className="text-muted-foreground font-mono">{k}</span>
                    <span className="text-foreground font-mono">{String(v)}</span>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t("models.trainingPeriods")}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {[
                { label: t("models.train"), start: model.train_start, end: model.train_end, color: "bg-blue-500" },
                { label: t("models.validation"), start: model.val_start, end: model.val_end, color: "bg-orange-500" },
                { label: t("models.test"), start: model.test_start, end: model.test_end, color: "bg-green-500" },
              ].map((p) => (
                <div key={p.label} className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${p.color}`} />
                  <span className="text-sm text-foreground font-medium w-20">{p.label}</span>
                  <span className="text-sm text-muted-foreground">
                    {p.start ? formatDate(p.start) : "N/A"} → {p.end ? formatDate(p.end) : "N/A"}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Backtests */}
      {backtests.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>{t("models.backtests")} ({backtests.length})</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {backtests.map((bt) => (
                <div key={bt.id} className="rounded-lg border border-border p-4">
                  <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
                    {[
                      { label: t("models.return"), value: bt.total_return != null ? `${Number(bt.total_return).toFixed(2)}%` : "N/A" },
                      { label: t("models.sharpe"), value: bt.sharpe_ratio != null ? Number(bt.sharpe_ratio).toFixed(2) : "N/A" },
                      { label: t("models.maxDrawdown"), value: bt.max_drawdown != null ? `${Number(bt.max_drawdown).toFixed(2)}%` : "N/A" },
                      { label: t("models.winRate"), value: bt.win_rate != null ? `${Number(bt.win_rate).toFixed(1)}%` : "N/A" },
                      { label: t("models.trades"), value: bt.n_trades || 0 },
                    ].map((s) => (
                      <div key={s.label}>
                        <p className="text-xs text-muted-foreground">{s.label}</p>
                        <p className="text-sm font-medium text-foreground mt-1">{s.value}</p>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
