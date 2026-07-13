"use client";

import { useEffect, useRef, useState } from "react";

interface TradingViewWidgetProps {
  symbol?: string;
  height?: number;
}

function getTheme(): "dark" | "light" {
  if (typeof window === "undefined") return "dark";
  try {
    const stored = localStorage.getItem("btc-ai-prefs");
    let theme = stored ? JSON.parse(stored).theme : "dark";
    if (!theme || theme === "system") {
      theme = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    }
    return theme === "dark" ? "dark" : "light";
  } catch {
    return "dark";
  }
}

function getLocale(): string {
  if (typeof window === "undefined") return "fr";
  try {
    const stored = localStorage.getItem("btc-ai-prefs");
    if (stored) {
      const p = JSON.parse(stored);
      if (p.lang === "en") return "en";
    }
  } catch {}
  return "fr";
}

export function TradingViewWidget({
  symbol = "BINANCE:BTCUSDT",
  height = 500,
}: TradingViewWidgetProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [theme, setTheme] = useState<"dark" | "light">("dark");

  useEffect(() => {
    setTheme(getTheme());
    const handler = () => setTheme(getTheme());
    window.addEventListener("storage", handler);
    return () => window.removeEventListener("storage", handler);
  }, []);

  useEffect(() => {
    if (!containerRef.current) return;
    containerRef.current.innerHTML = "";

    const script = document.createElement("script");
    script.src = "https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js";
    script.type = "text/javascript";
    script.async = true;
    script.innerHTML = JSON.stringify({
      autosize: true,
      symbol,
      interval: "60",
      timezone: "UTC",
      theme,
      style: "1",
      locale: getLocale(),
      enable_publishing: false,
      hide_side_toolbar: false,
      allow_symbol_change: true,
      details: true,
      studies: ["STD;RSI", "STD;MACD", "STD;EMA"],
      support_host: "https://www.tradingview.com",
    });

    containerRef.current.appendChild(script);
  }, [symbol, theme]);

  return (
    <div
      className="tradingview-widget-container rounded-xl overflow-hidden border border-border"
      ref={containerRef}
      style={{ height: `${height}px`, width: "100%" }}
    />
  );
}
