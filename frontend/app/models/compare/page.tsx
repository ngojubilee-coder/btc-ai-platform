"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { GitCompare } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Select } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { formatDate } from "@/lib/utils";
import { useI18n } from "@/lib/i18n";

const C = {
  grid: "hsl(217 33% 20%)",
  axis: "hsl(215 20% 65%)",
  text: "hsl(213 31% 91%)",
  cardBg: "hsl(222 47% 11%)",
  border: "hsl(217 33% 20%)",
};

export default function CompareModelsPage() {
  const { t } = useI18n();
  const [models, setModels] = useState<any[]>([]);
  const [id1, setId1] = useState("");
  const [id2, setId2] = useState("");
  const [comparison, setComparison] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    apiFetch<any[]>("/api/models/").then((data) => {
      setModels(data || []);
      if (data && data.length >= 2) {
        setId1(data[0].id);
        setId2(data[1].id);
      }
    }).catch(() => {});
  }, []);

  async function compare() {
    if (!id1 || !id2 || id1 === id2) return;
    setLoading(true);
    try {
      const data = await apiFetch<any>(`/api/models/compare/${id1}/${id2}`);
      setComparison(data);
    } catch {}
    setLoading(false);
  }

  const m1 = comparison?.model_1;
  const m2 = comparison?.model_2;
  const f1 = comparison?.features_1 || [];
  const f2 = comparison?.features_2 || [];

  const featureMap = new Map<string, { f1?: number; f2?: number }>();
  f1.forEach((f: any) => featureMap.set(f.feature_name, { f1: f.importance }));
  f2.forEach((f: any) => {
    const existing = featureMap.get(f.feature_name) || {};
    featureMap.set(f.feature_name, { ...existing, f2: f.importance });
  });
  const chartData = Array.from(featureMap.entries())
    .map(([name, v]) => ({ feature: name, model_1: v.f1 || 0, model_2: v.f2 || 0 }))
    .sort((a, b) => (b.model_1 + b.model_2) - (a.model_1 + a.model_2))
    .slice(0, 15);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
          <GitCompare className="h-6 w-6 text-primary" />
          {t("models.comparison")}
        </h1>
        <p className="text-sm text-muted-foreground mt-1">{t("models.comparisonDesc")}</p>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="flex items-end gap-4">
            <div className="flex-1">
              <label className="text-sm text-muted-foreground mb-1 block">{t("models.model")} 1</label>
              <Select value={id1} onChange={(e) => setId1(e.target.value)}>
                {models.map((m) => (
                  <option key={m.id} value={m.id}>{m.model_name} v{m.version}</option>
                ))}
              </Select>
            </div>
            <div className="flex-1">
              <label className="text-sm text-muted-foreground mb-1 block">{t("models.model")} 2</label>
              <Select value={id2} onChange={(e) => setId2(e.target.value)}>
                {models.map((m) => (
                  <option key={m.id} value={m.id}>{m.model_name} v{m.version}</option>
                ))}
              </Select>
            </div>
            <Button onClick={compare} disabled={!id1 || !id2 || id1 === id2 || loading}>
              <GitCompare className="h-4 w-4 mr-1" />
              {t("models.compare")}
            </Button>
          </div>
        </CardContent>
      </Card>

      {comparison && m1 && m2 && (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>{m1.model_name}</CardTitle>
                  <Badge variant="secondary">v{m1.version}</Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm">
                  <Row label={t("whales.type")} value={m1.model_type} />
                  <Row label={t("models.status")} value={t(`models.status${(m1.status || "unknown").charAt(0).toUpperCase() + (m1.status || "unknown").slice(1)}`)} />
                  <Row label={t("models.target")} value={m1.target_col || "N/A"} />
                  <Row label={t("models.trainLoss")} value={m1.train_loss != null ? Number(m1.train_loss).toFixed(4) : "N/A"} />
                  <Row label={t("models.valLoss")} value={m1.val_loss != null ? Number(m1.val_loss).toFixed(4) : "N/A"} />
                  <Row label={t("news.date")} value={formatDate(m1.created_at)} />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>{m2.model_name}</CardTitle>
                  <Badge variant="secondary">v{m2.version}</Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm">
                  <Row label={t("whales.type")} value={m2.model_type} />
                  <Row label={t("models.status")} value={t(`models.status${(m2.status || "unknown").charAt(0).toUpperCase() + (m2.status || "unknown").slice(1)}`)} />
                  <Row label={t("models.target")} value={m2.target_col || "N/A"} />
                  <Row label={t("models.trainLoss")} value={m2.train_loss != null ? Number(m2.train_loss).toFixed(4) : "N/A"} />
                  <Row label={t("models.valLoss")} value={m2.val_loss != null ? Number(m2.val_loss).toFixed(4) : "N/A"} />
                  <Row label={t("news.date")} value={formatDate(m2.created_at)} />
                </div>
              </CardContent>
            </Card>
          </div>

          {chartData.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>{t("models.featureImportance")} — {t("models.comparison")}</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={450}>
                  <BarChart data={chartData} layout="vertical" margin={{ left: 100 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={C.grid} />
                    <XAxis type="number" tick={{ fill: C.axis, fontSize: 11 }} stroke={C.grid} />
                    <YAxis type="category" dataKey="feature" tick={{ fill: C.text, fontSize: 10 }} stroke={C.grid} width={100} />
                    <Tooltip
                      contentStyle={{ backgroundColor: C.cardBg, border: `1px solid ${C.border}`, borderRadius: "8px", color: C.text }}
                      formatter={(v: any) => Number(v).toFixed(4)}
                    />
                    <Legend />
                    <Bar dataKey="model_1" name={m1.model_name} fill="#3b82f6" radius={[0, 4, 4, 0]} />
                    <Bar dataKey="model_2" name={m2.model_name} fill="#f59e0b" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          )}
        </>
      )}

      {!comparison && models.length < 2 && (
        <Card>
          <CardContent className="py-12 text-center">
            <GitCompare className="mx-auto h-10 w-10 text-muted-foreground mb-3" />
            <p className="text-foreground font-medium">{t("models.notEnoughModels")}</p>
            <p className="text-sm text-muted-foreground mt-1">{t("models.selectModels")}</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between py-1.5 px-2 rounded hover:bg-secondary/50">
      <span className="text-muted-foreground">{label}</span>
      <span className="text-foreground font-medium">{value}</span>
    </div>
  );
}
