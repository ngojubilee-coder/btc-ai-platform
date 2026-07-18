"use client";

import { useEffect, useState, useCallback } from "react";
import { apiFetch, apiPost } from "@/lib/api";
import { Newspaper, RefreshCw, Search, TrendingUp, TrendingDown, ExternalLink, Calendar, ChevronLeft, ChevronRight } from "lucide-react";
import { formatDate } from "@/lib/utils";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { SkeletonCard } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { useI18n } from "@/lib/i18n";

const EVENT_TYPES = ["fed", "cpi", "rate", "etf", "halving", "liquidation", "hack", "regulation", "market", "whale", "mining"];

const TYPE_COLORS: Record<string, string> = {
  fed: "bg-red-500/20 text-red-400",
  cpi: "bg-orange-500/20 text-orange-400",
  rate: "bg-yellow-500/20 text-yellow-400",
  etf: "bg-purple-500/20 text-purple-400",
  halving: "bg-green-500/20 text-green-400",
  liquidation: "bg-pink-500/20 text-pink-400",
  hack: "bg-red-600/20 text-red-500",
  regulation: "bg-blue-500/20 text-blue-400",
  market: "bg-gray-500/20 text-gray-400",
  whale: "bg-cyan-500/20 text-cyan-400",
  mining: "bg-amber-500/20 text-amber-400",
};

export default function NewsPage() {
  const { toast } = useToast();
  const { t } = useI18n();
  const [news, setNews] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [filterType, setFilterType] = useState("");
  const [correlations, setCorrelations] = useState<any[]>([]);
  const [page, setPage] = useState(0);
  const pageSize = 10;

  const loadNews = useCallback(async () => {
    setLoading(true);
    try {
      const limit = pageSize;
      const offset = page * pageSize;
      const typeParam = filterType ? `&event_type=${filterType}` : "";
      const data = await apiFetch<any[]>(`/api/news/search?limit=${limit}&offset=${offset}${typeParam}`);
      setNews(data || []);
    } catch {
      setNews([]);
    }
    setLoading(false);
  }, [page, filterType, pageSize]);

  async function loadCorrelations() {
    try {
      const data = await apiFetch<any[]>(`/api/news/correlate?limit=10`);
      setCorrelations(data || []);
    } catch {
      setCorrelations([]);
    }
  }

  async function handleRefresh() {
    setRefreshing(true);
    try {
      await apiPost("/api/news/refresh", {});
      await loadNews();
      await loadCorrelations();
      toast(t("news.refreshed"), "success");
    } catch {
      toast(t("news.refreshError"), "error");
    }
    setRefreshing(false);
  }

  useEffect(() => {
    loadCorrelations();
  }, []);

  useEffect(() => {
    loadNews();
  }, [loadNews]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
            <Newspaper className="h-6 w-6 text-primary" />
            {t("news.title")}
          </h1>
          <p className="text-sm text-muted-foreground mt-1">{t("news.subtitle")}</p>
        </div>
        <Button
          onClick={handleRefresh}
          disabled={refreshing}
          variant="secondary"
          size="md"
        >
          <RefreshCw className={`h-4 w-4 mr-1 ${refreshing ? "animate-spin" : ""}`} />
          {refreshing ? t("news.refreshing") : t("news.refresh")}
        </Button>
      </div>

      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => { setFilterType(""); setPage(0); }}
          className={`rounded-lg px-3 py-1.5 text-xs font-medium ${!filterType ? "bg-primary text-primary-foreground" : "bg-secondary text-foreground hover:bg-secondary/80"}`}
        >
          {t("common.all")}
        </button>
        {EVENT_TYPES.map((et) => (
          <button
            key={et}
            onClick={() => { setFilterType(et); setPage(0); }}
            className={`rounded-lg px-3 py-1.5 text-xs font-medium ${filterType === et ? "bg-primary text-primary-foreground" : "bg-secondary text-foreground hover:bg-secondary/80"}`}
          >
            {t(`news.type_${et}`)}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)}
        </div>
      ) : news.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Search className="mx-auto h-8 w-8 mb-2 opacity-50 text-muted-foreground" />
            <p className="text-foreground font-medium">{t("news.noNews")}</p>
            <p className="text-sm text-muted-foreground mt-1">
              {t("news.refreshHint")}
            </p>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Correlations section */}
          {correlations.length > 0 && !filterType && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-primary" />
                  {t("news.correlations")}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {correlations.map((c, i) => {
                    const isUp = Number(c.price_change_pct || 0) >= 0;
                    return (
                      <div key={i} className="flex items-center gap-4 rounded-lg border border-border p-3">
                        <div className={`flex items-center gap-1 flex-shrink-0 w-24 ${isUp ? "text-green-400" : "text-red-400"}`}>
                          {isUp ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
                          <span className="text-sm font-medium">
                            {isUp ? "+" : ""}{Number(c.price_change_pct || 0).toFixed(2)}%
                          </span>
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-foreground truncate">{c.title}</p>
                          <p className="text-xs text-muted-foreground">{formatDate(c.event_date)}</p>
                        </div>
                        <Badge variant="outline" className="flex-shrink-0">{t(`news.type_${c.event_type}`)}</Badge>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          )}

          {/* News list */}
          <div className="space-y-3">
            {news.map((item, i) => (
              <Card key={i} className="p-4 animate-fade-in">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <Badge variant="secondary" className={TYPE_COLORS[item.event_type] || TYPE_COLORS.market}>
                        {t(`news.type_${item.event_type}`)}
                      </Badge>
                      <span className="text-xs text-muted-foreground">{item.source}</span>
                    </div>
                    <h3 className="font-medium text-foreground">{item.title}</h3>
                    {item.summary && (
                      <p className="text-sm text-muted-foreground mt-1 line-clamp-2">{item.summary}</p>
                    )}
                    <div className="flex items-center gap-1 mt-2 text-xs text-muted-foreground">
                      <Calendar className="h-3 w-3" />
                      {formatDate(item.event_date)}
                    </div>
                  </div>
                  {item.url && (
                    <a href={item.url} target="_blank" rel="noopener noreferrer" className="text-xs text-primary hover:underline flex-shrink-0 flex items-center gap-1">
                      <ExternalLink className="h-3 w-3" />
                      {t("news.view")}
                    </a>
                  )}
                </div>
              </Card>
            ))}
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between pt-2">
            <span className="text-xs text-muted-foreground">
              {t("data.page")} {page + 1}
            </span>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={page === 0 || loading}
                onClick={() => setPage((p) => Math.max(0, p - 1))}
              >
                <ChevronLeft className="h-4 w-4" />
                {t("data.previous")}
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={news.length < pageSize || loading}
                onClick={() => setPage((p) => p + 1)}
              >
                {t("data.next")}
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
