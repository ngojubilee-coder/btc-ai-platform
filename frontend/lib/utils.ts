import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: string | Date): string {
  const d = typeof date === "string" ? new Date(date) : date;
  let locale = "fr-FR";
  try {
    const stored = localStorage.getItem("btc-ai-prefs");
    if (stored) {
      const p = JSON.parse(stored);
      if (p.lang === "en") locale = "en-US";
    }
  } catch {}
  return d.toLocaleDateString(locale, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatNumber(n: number | null | undefined, decimals: number = 2): string {
  if (n === null || n === undefined) return "N/A";
  if (Math.abs(n) >= 1e9) return (n / 1e9).toFixed(decimals) + "B";
  if (Math.abs(n) >= 1e6) return (n / 1e6).toFixed(decimals) + "M";
  if (Math.abs(n) >= 1e3) return (n / 1e3).toFixed(decimals) + "K";
  return n.toFixed(decimals);
}
