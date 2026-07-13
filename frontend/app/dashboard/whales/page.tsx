"use client";

import { useEffect, useState, useRef } from "react";
import { apiFetch } from "@/lib/api";
import { useDebounce } from "@/lib/hooks";
import { Waves, Search, Loader2, ExternalLink } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SkeletonCard } from "@/components/ui/skeleton";
import { formatNumber } from "@/lib/utils";
import { useI18n } from "@/lib/i18n";

interface WhaleWallet {
  address: string;
  category: string;
  name: string;
  entity: string;
  type: string;
  estimated_btc: number | null;
  source: string;
}

interface WhaleStats {
  total_wallets: number;
  total_btc: number;
  categories: Record<string, number>;
  top_entities: Record<string, number>;
}

const CATEGORY_COLORS: Record<string, string> = {
  EXCHANGE: "text-blue-400",
  MINING: "text-green-400",
  GOV: "text-purple-400",
  FUND: "text-orange-400",
  INDIVIDUAL: "text-pink-400",
  UNKNOWN: "text-muted-foreground",
};

export default function WhalesPage() {
  const { t } = useI18n();
  const [wallets, setWallets] = useState<WhaleWallet[]>([]);
  const [stats, setStats] = useState<WhaleStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [page, setPage] = useState(0);
  const pageSize = 50;
  const [hasMore, setHasMore] = useState(true);
  const debouncedSearch = useDebounce(search, 400);
  const isFirstRender = useRef(true);

  useEffect(() => {
    Promise.all([
      apiFetch<WhaleStats>("/api/whales/stats").catch(() => null),
      apiFetch<WhaleWallet[]>(`/api/whales/?limit=${pageSize}`).catch(() => []),
    ]).then(([s, w]) => {
      setStats(s);
      setWallets(w || []);
      setHasMore((w || []).length >= pageSize);
      setLoading(false);
    });
  }, []);

  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }
    doSearch(debouncedSearch);
  }, [debouncedSearch]);

  async function doSearch(query?: string) {
    const q = query ?? search;
    setLoading(true);
    setPage(0);
    if (q.trim()) {
      const results = await apiFetch<WhaleWallet[]>(`/api/whales/search?q=${encodeURIComponent(q)}&limit=${pageSize}`).catch(() => []);
      setWallets(results || []);
      setHasMore((results || []).length >= pageSize);
    } else {
      const results = await apiFetch<WhaleWallet[]>(`/api/whales/?limit=${pageSize}`).catch(() => []);
      setWallets(results || []);
      setHasMore((results || []).length >= pageSize);
    }
    setLoading(false);
  }

  async function loadMore() {
    const next = page + 1;
    const offset = next * pageSize;
    setLoading(true);
    if (search.trim()) {
      const results = await apiFetch<WhaleWallet[]>(`/api/whales/search?q=${encodeURIComponent(search)}&limit=${pageSize}&offset=${offset}`).catch(() => []);
      setWallets((prev) => [...prev, ...(results || [])]);
      setHasMore((results || []).length >= pageSize);
    } else {
      const results = await apiFetch<WhaleWallet[]>(`/api/whales/?limit=${pageSize}&offset=${offset}`).catch(() => []);
      setWallets((prev) => [...prev, ...(results || [])]);
      setHasMore((results || []).length >= pageSize);
    }
    setPage(next);
    setLoading(false);
  }

  const filtered = wallets.filter((w) => {
    if (categoryFilter && w.category !== categoryFilter) return false;
    return true;
  });

  const categories = stats ? Object.keys(stats.categories) : [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
            <Waves className="h-6 w-6 text-primary" />
            {t("whales.title")}
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            {t("whales.subtitle")}
          </p>
        </div>
      </div>

      {/* Stats cards */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <Card className="p-5">
            <p className="text-2xl font-bold text-foreground">{formatNumber(stats.total_wallets, 0)}</p>
            <p className="text-xs text-muted-foreground mt-1">{t("whales.trackedWallets")}</p>
          </Card>
          <Card className="p-5">
            <p className="text-2xl font-bold text-foreground">{formatNumber(stats.total_btc, 0)}</p>
            <p className="text-xs text-muted-foreground mt-1">{t("whales.totalBtc")}</p>
          </Card>
          <Card className="p-5">
            <p className="text-2xl font-bold text-foreground">{Object.keys(stats.top_entities).length}</p>
            <p className="text-xs text-muted-foreground mt-1">{t("whales.distinctEntities")}</p>
          </Card>
          <Card className="p-5">
            <p className="text-2xl font-bold text-foreground">{categories.length}</p>
            <p className="text-xs text-muted-foreground mt-1">{t("whales.categories")}</p>
          </Card>
        </div>
      )}

      {/* Category breakdown */}
      {stats && categories.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>{t("whales.categoryBreakdown")}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-3">
              {categories.map((cat) => (
                <button
                  key={cat}
                  onClick={() => setCategoryFilter(categoryFilter === cat ? "" : cat)}
                  className={`flex items-center gap-2 rounded-lg border p-3 text-sm transition-colors ${
                    categoryFilter === cat
                      ? "border-primary bg-primary/10 text-primary"
                      : "border-border bg-secondary/50 text-foreground hover:bg-secondary"
                  }`}
                >
                  <span className={`font-medium ${CATEGORY_COLORS[cat] || ""}`}>{t(`whales.cat_${cat}`)}</span>
                  <Badge variant="secondary">{stats.categories[cat]}</Badge>
                </button>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Search + filter */}
      <div className="flex gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder={t("whales.searchPlaceholder")}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && doSearch()}
            className="pl-9"
          />
        </div>
        <Button onClick={() => doSearch()} variant="default" size="md">
          <Search className="h-4 w-4 mr-1" />
          {t("whales.searchBtn")}
        </Button>
        {categoryFilter && (
          <Button onClick={() => setCategoryFilter("")} variant="outline" size="md">
            {t("whales.clearFilter")}
          </Button>
        )}
      </div>

      {/* Whale wallets table */}
      {loading ? (
        <div className="space-y-3">
          {Array.from({ length: 6 }).map((_, i) => <SkeletonCard key={i} />)}
        </div>
      ) : filtered.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Waves className="mx-auto h-10 w-10 text-muted-foreground mb-3" />
            <p className="text-foreground font-medium">{t("whales.noWallets")}</p>
            <p className="text-sm text-muted-foreground mt-1">
              {t("whales.noWalletsDesc")}
            </p>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>{t("whales.wallets")} ({filtered.length})</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left">
                    <th className="py-2 px-3 text-muted-foreground font-medium">{t("whales.name")}</th>
                    <th className="py-2 px-3 text-muted-foreground font-medium">{t("whales.entity")}</th>
                    <th className="py-2 px-3 text-muted-foreground font-medium">{t("whales.category")}</th>
                    <th className="py-2 px-3 text-muted-foreground font-medium">{t("whales.type")}</th>
                    <th className="py-2 px-3 text-muted-foreground font-medium text-right">{t("whales.estimatedBtc")}</th>
                    <th className="py-2 px-3 text-muted-foreground font-medium">{t("whales.address")}</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((w, i) => (
                    <tr key={i} className="border-b border-border/50 hover:bg-secondary/30 transition-colors">
                      <td className="py-2.5 px-3 text-foreground font-medium">{w.name}</td>
                      <td className="py-2.5 px-3 text-muted-foreground">{w.entity}</td>
                      <td className="py-2.5 px-3">
                        <Badge variant="outline" className={CATEGORY_COLORS[w.category] || ""}>
                          {t(`whales.cat_${w.category}`)}
                        </Badge>
                      </td>
                      <td className="py-2.5 px-3 text-muted-foreground">{t(`whales.type_${w.type}`)}</td>
                      <td className="py-2.5 px-3 text-right text-foreground font-medium">
                        {w.estimated_btc ? formatNumber(w.estimated_btc, 0) : "N/A"}
                      </td>
                      <td className="py-2.5 px-3">
                        <a
                          href={`https://blockchain.info/address/${w.address}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-primary hover:underline font-mono text-xs flex items-center gap-1"
                        >
                          {w.address ? `${w.address.slice(0, 8)}...${w.address.slice(-6)}` : "N/A"}
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Load more */}
      {!loading && filtered.length > 0 && hasMore && (
        <div className="flex justify-center">
          <Button onClick={loadMore} variant="outline" size="md" disabled={loading}>
            {t("whales.loadMore")}
          </Button>
        </div>
      )}
    </div>
  );
}
