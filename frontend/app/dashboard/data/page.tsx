"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { useDebounce } from "@/lib/hooks";
import { Table, Search, ChevronLeft, ChevronRight, Database, Clock, BarChart3, X } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input, Select } from "@/components/ui/input";
import { SkeletonCard, SkeletonRow } from "@/components/ui/skeleton";
import { formatNumber } from "@/lib/utils";
import { useI18n } from "@/lib/i18n";

export default function DataExplorerPage() {
  const { t } = useI18n();
  const [schema, setSchema] = useState<any>(null);
  const [rows, setRows] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(50);
  const [searchCol, setSearchCol] = useState("");
  const [searchVal, setSearchVal] = useState("");
  const [mode, setMode] = useState<"sample" | "search" | "time">("sample");
  const [timeStart, setTimeStart] = useState("");
  const [timeEnd, setTimeEnd] = useState("");
  const [colStats, setColStats] = useState<any>(null);
  const [colStatsCol, setColStatsCol] = useState("");
  const [colStatsLoading, setColStatsLoading] = useState(false);
  const debouncedSearchVal = useDebounce(searchVal, 300);

  useEffect(() => {
    if (!colStatsCol) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") { setColStatsCol(""); setColStats(null); }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [colStatsCol]);

  useEffect(() => {
    apiFetch<any>("/api/data/schema").then((data) => {
      setSchema(data);
      if (data?.columns?.length > 0) {
        setSearchCol(data.columns[0].name);
      }
    }).catch(() => {});
  }, []);

  useEffect(() => {
    loadRows();
  }, [page, pageSize, searchCol, debouncedSearchVal, mode]);

  async function loadRows() {
    setLoading(true);
    try {
      let query: string;
      if (mode === "time" && timeStart && timeEnd) {
        query = `/api/data/time-range?start=${encodeURIComponent(timeStart)}&end=${encodeURIComponent(timeEnd)}&limit=${pageSize}`;
      } else if (mode === "search" && searchCol && debouncedSearchVal) {
        query = `/api/data/search?column=${encodeURIComponent(searchCol)}&value=${encodeURIComponent(debouncedSearchVal)}&limit=${pageSize}&offset=${page * pageSize}`;
      } else {
        query = `/api/data/sample?n=${pageSize}&offset=${page * pageSize}`;
      }
      const data = await apiFetch<any[]>(query);
      setRows(data || []);
    } catch {
      setRows([]);
    }
    setLoading(false);
  }

  async function loadColStats(col: string) {
    if (!col) return;
    setColStatsLoading(true);
    setColStatsCol(col);
    try {
      const data = await apiFetch<any>(`/api/data/column/${encodeURIComponent(col)}/stats`);
      setColStats(data);
    } catch {
      setColStats(null);
    }
    setColStatsLoading(false);
  }

  const columns = schema?.columns || [];
  const displayCols = columns.slice(0, 12);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
          <Database className="h-6 w-6 text-primary" />
          {t("data.title")}
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          {t("data.subtitle")} ({schema?.n_rows?.toLocaleString() || "?"} {t("data.rows")}, {columns.length} {t("dashboard.columns")})
        </p>
      </div>

      {/* Mode selector */}
      <div className="flex gap-2">
        <button
          onClick={() => { setMode("sample"); setPage(0); }}
          className={`rounded-lg px-3 py-1.5 text-xs font-medium ${mode === "sample" ? "bg-primary text-primary-foreground" : "bg-secondary text-foreground hover:bg-secondary/80"}`}
        >
          {t("data.sample")}
        </button>
        <button
          onClick={() => { setMode("search"); setPage(0); }}
          className={`rounded-lg px-3 py-1.5 text-xs font-medium ${mode === "search" ? "bg-primary text-primary-foreground" : "bg-secondary text-foreground hover:bg-secondary/80"}`}
        >
          {t("data.search")}
        </button>
        <button
          onClick={() => { setMode("time"); setPage(0); }}
          className={`rounded-lg px-3 py-1.5 text-xs font-medium ${mode === "time" ? "bg-primary text-primary-foreground" : "bg-secondary text-foreground hover:bg-secondary/80"}`}
        >
          {t("data.timePeriod")}
        </button>
      </div>

      {/* Search / filter bar */}
      <Card>
        <CardContent className="pt-6">
          {mode === "search" && (
            <div className="flex items-end gap-3">
              <div className="flex-1">
                <label className="text-xs text-muted-foreground mb-1 block">{t("data.column")}</label>
                <Select value={searchCol} onChange={(e) => setSearchCol(e.target.value)}>
                  {columns.map((c: any) => (
                    <option key={c.name} value={c.name}>{c.name}</option>
                  ))}
                </Select>
              </div>
              <div className="flex-1">
                <label className="text-xs text-muted-foreground mb-1 block">{t("data.value")}</label>
                <div className="relative">
                  <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder={t("data.searchPlaceholder")}
                    value={searchVal}
                    onChange={(e) => { setSearchVal(e.target.value); setPage(0); }}
                    className="pl-9"
                  />
                </div>
              </div>
              <div>
                <label className="text-xs text-muted-foreground mb-1 block">{t("data.rowsPerPage")}</label>
                <Select value={String(pageSize)} onChange={(e) => { setPageSize(Number(e.target.value)); setPage(0); }}>
                  <option value="25">25</option>
                  <option value="50">50</option>
                  <option value="100">100</option>
                  <option value="200">200</option>
                </Select>
              </div>
            </div>
          )}
          {mode === "time" && (
            <div className="flex items-end gap-3">
              <div className="flex-1">
                <label className="text-xs text-muted-foreground mb-1 block">{t("data.start")} (ISO)</label>
                <Input
                  type="datetime-local"
                  value={timeStart}
                  onChange={(e) => setTimeStart(e.target.value)}
                />
              </div>
              <div className="flex-1">
                <label className="text-xs text-muted-foreground mb-1 block">{t("data.end")} (ISO)</label>
                <Input
                  type="datetime-local"
                  value={timeEnd}
                  onChange={(e) => setTimeEnd(e.target.value)}
                />
              </div>
              <Button onClick={() => { if (page === 0) loadRows(); else setPage(0); }} variant="default" size="md">
                <Clock className="h-4 w-4 mr-1" />
                {t("data.load")}
              </Button>
            </div>
          )}
          {mode === "sample" && (
            <div className="flex items-end gap-3">
              <div>
                <label className="text-xs text-muted-foreground mb-1 block">{t("data.rowsPerPage")}</label>
                <Select value={String(pageSize)} onChange={(e) => { setPageSize(Number(e.target.value)); setPage(0); }}>
                  <option value="25">25</option>
                  <option value="50">50</option>
                  <option value="100">100</option>
                  <option value="200">200</option>
                </Select>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Data table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">
            {loading ? t("data.loading") : `${rows.length} ${t("data.rowsShown")} (${t("data.page")} ${page + 1})`}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-2">
              {Array.from({ length: 8 }).map((_, i) => <SkeletonRow key={i} cols={6} />)}
            </div>
          ) : rows.length === 0 ? (
            <div className="text-center py-12">
              <Database className="mx-auto h-8 w-8 text-muted-foreground mb-2 opacity-50" />
              <p className="text-sm text-muted-foreground">{t("data.noData")}</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left py-2 px-3 text-xs text-muted-foreground font-medium">#</th>
                    {displayCols.map((col: any) => (
                      <th key={col.name} className="text-left py-2 px-3 text-xs text-muted-foreground font-medium whitespace-nowrap">
                        <button
                          onClick={() => loadColStats(col.name)}
                          className="hover:text-primary inline-flex items-center gap-1"
                        >
                          {col.name}
                          <BarChart3 className="h-3 w-3 opacity-50" />
                        </button>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row, i) => (
                    <tr key={i} className="border-b border-border/50 hover:bg-secondary/30">
                      <td className="py-2 px-3 text-xs text-muted-foreground">{page * pageSize + i + 1}</td>
                      {displayCols.map((col: any) => {
                        const val = row[col.name];
                        const display = val === null || val === undefined
                          ? "—"
                          : typeof val === "number"
                            ? formatNumber(val, 4)
                            : typeof val === "string" && val.length > 30
                              ? val.slice(0, 30) + "…"
                              : String(val);
                        return (
                          <td key={col.name} className="py-2 px-3 text-xs text-foreground whitespace-nowrap font-mono">
                            {display}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination */}
          {!loading && rows.length > 0 && (
            <div className="flex items-center justify-between mt-4">
              <p className="text-xs text-muted-foreground">
                {t("data.page")} {page + 1} · {pageSize} {t("data.rowsPerPage")}
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.max(0, p - 1))}
                  disabled={page === 0}
                >
                  <ChevronLeft className="h-4 w-4" />
                  {t("data.previous")}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => p + 1)}
                  disabled={rows.length < pageSize}
                >
                  {t("data.next")}
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Column stats modal */}
      {colStatsCol && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={() => { setColStatsCol(""); setColStats(null); }}>
          <div className="w-full max-w-md rounded-xl border border-border bg-card p-6 space-y-4" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-primary" />
                <h3 className="font-semibold text-foreground font-mono text-sm">{colStatsCol}</h3>
              </div>
              <button onClick={() => { setColStatsCol(""); setColStats(null); }} className="text-muted-foreground hover:text-foreground">
                <X className="h-5 w-5" />
              </button>
            </div>
            {colStatsLoading ? (
              <div className="h-32 flex items-center justify-center">
                <div className="h-6 w-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
              </div>
            ) : colStats && !colStats.error ? (
              <div className="space-y-2">
                {Object.entries(colStats).map(([key, val]) => (
                  <div key={key} className="flex items-center justify-between border-b border-border/50 pb-1">
                    <span className="text-sm text-muted-foreground">{key}</span>
                    <span className="text-sm font-mono text-foreground">
                      {typeof val === "number" ? formatNumber(val, 4) : String(val ?? "N/A")}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground text-center py-4">
                {colStats?.error || t("data.statsUnavailable")}
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
