"use client";

import { useEffect, useState } from "react";
import { TrendingUp, TrendingDown, Bitcoin } from "lucide-react";
import { formatNumber } from "@/lib/utils";

interface PriceData {
  price: number;
  change_24h: number;
  change_pct_24h: number;
}

export function PriceTicker() {
  const [data, setData] = useState<PriceData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchPrice() {
      try {
        const res = await fetch(
          "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true"
        );
        if (!res.ok) throw new Error(`CoinGecko API error: ${res.status}`);
        const json = await res.json();
        setData({
          price: json.bitcoin?.usd || 0,
          change_24h: json.bitcoin?.usd_24h_change || 0,
          change_pct_24h: json.bitcoin?.usd_24h_change || 0,
        });
        setLoading(false);
      } catch {
        setLoading(false);
      }
    }
    fetchPrice();
    const interval = setInterval(fetchPrice, 60000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="rounded-xl border border-border bg-card p-4 animate-pulse">
        <div className="h-12 bg-secondary/50 rounded" />
      </div>
    );
  }

  const isUp = (data?.change_pct_24h || 0) >= 0;

  return (
    <div className="rounded-xl border border-border bg-card p-4 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
          <Bitcoin className="h-5 w-5 text-primary" />
        </div>
        <div>
          <p className="text-xs text-muted-foreground">BTC / USD</p>
          <p className="text-xl font-bold text-foreground">
            ${formatNumber(data?.price || 0, 0)}
          </p>
        </div>
      </div>
      <div className={`flex items-center gap-1.5 ${isUp ? "text-green-400" : "text-red-400"}`}>
        {isUp ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
        <span className="text-sm font-medium">
          {isUp ? "+" : ""}{(data?.change_pct_24h || 0).toFixed(2)}%
        </span>
      </div>
    </div>
  );
}
