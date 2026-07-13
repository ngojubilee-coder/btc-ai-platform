"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { TrendingUp, Loader2 } from "lucide-react";
import { useI18n } from "@/lib/i18n";

const CHART_COLORS = {
  grid: "hsl(217 33% 20%)",
  axis: "hsl(215 20% 65%)",
  text: "hsl(213 31% 91%)",
  bar: "hsl(199 89% 48%)",
  cardBg: "hsl(222 47% 11%)",
  border: "hsl(217 33% 20%)",
};

export default function CorrelationsPage() {
  const { t } = useI18n();
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [target, setTarget] = useState("target_return_15m");

  useEffect(() => {
    setLoading(true);
    apiFetch<any[]>(`/api/data/correlations?target=${target}&top_n=25`)
      .then((d) => {
        setData(d || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [target]);

  const targets = [
    "target_return_5m",
    "target_return_15m",
    "target_return_60m",
    "target_return_240m",
    "target_direction_15m",
    "target_direction_60m",
    "target_volatility_60m",
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
            <TrendingUp className="h-6 w-6 text-primary" />
            {t("nav.correlations")}
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            {t("dashboard.actCorrelationsDesc")}
          </p>
        </div>
        <select
          value={target}
          onChange={(e) => setTarget(e.target.value)}
          className="rounded-lg border border-input bg-background px-3 py-2 text-sm text-foreground focus:border-primary focus:outline-none"
        >
          {targets.map((tg) => (
            <option key={tg} value={tg}>{tg}</option>
          ))}
        </select>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : data.length === 0 ? (
        <div className="rounded-xl border border-border bg-card p-12 text-center text-muted-foreground">
          {t("dashboard.noCorrelations")}
        </div>
      ) : (
        <div className="rounded-xl border border-border bg-card p-6">
          <ResponsiveContainer width="100%" height={500}>
            <BarChart data={data} layout="vertical" margin={{ left: 120, right: 20, top: 10, bottom: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.grid} />
              <XAxis
                type="number"
                domain={[0, "auto"]}
                tick={{ fill: CHART_COLORS.axis, fontSize: 12 }}
                stroke={CHART_COLORS.grid}
              />
              <YAxis
                type="category"
                dataKey="feature"
                tick={{ fill: CHART_COLORS.text, fontSize: 11 }}
                stroke={CHART_COLORS.grid}
                width={120}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: CHART_COLORS.cardBg,
                  border: `1px solid ${CHART_COLORS.border}`,
                  borderRadius: "8px",
                  color: CHART_COLORS.text,
                }}
                formatter={(v: any) => Number(v).toFixed(4)}
              />
              <Bar
                dataKey="correlation"
                fill={CHART_COLORS.bar}
                radius={[0, 4, 4, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {data.length > 0 && (
        <div className="rounded-xl border border-border bg-card p-6">
          <h2 className="text-lg font-semibold text-foreground mb-4">{t("correlations.detail")}</h2>
          <div className="space-y-1">
            {data.map((row, i) => (
              <div
                key={i}
                className="flex items-center justify-between py-2 px-3 rounded hover:bg-secondary/50 text-sm"
              >
                <span className="text-foreground font-mono">{row.feature}</span>
                <span className="text-primary font-medium">{row.correlation != null ? Number(row.correlation).toFixed(4) : "N/A"}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
