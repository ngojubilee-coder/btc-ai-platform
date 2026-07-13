"use client";

import { TradingViewWidget } from "@/components/tradingview-widget";
import { CandlestickChart } from "lucide-react";
import { useI18n } from "@/lib/i18n";

export default function ChartPage() {
  const { t } = useI18n();
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
          <CandlestickChart className="h-6 w-6 text-primary" />
          {t("nav.chart")}
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          {t("chart.subtitle")}
        </p>
      </div>

      <div className="rounded-xl border border-border bg-card p-4">
        <TradingViewWidget symbol="BINANCE:BTCUSDT" height={600} />
      </div>
    </div>
  );
}
