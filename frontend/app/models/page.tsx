"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { BarChart3, GitCompare, ArrowRight, Search } from "lucide-react";
import { formatDate } from "@/lib/utils";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SkeletonCard } from "@/components/ui/skeleton";
import Link from "next/link";
import { useI18n } from "@/lib/i18n";

export default function ModelsPage() {
  const { t } = useI18n();
  const [models, setModels] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  useEffect(() => {
    apiFetch<any[]>("/api/models/").then((data) => {
      setModels(data || []);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const filtered = models.filter((m) => {
    const matchSearch = !search || m.model_name?.toLowerCase().includes(search.toLowerCase()) || m.model_type?.toLowerCase().includes(search.toLowerCase());
    const matchStatus = !statusFilter || m.status === statusFilter;
    return matchSearch && matchStatus;
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
            <BarChart3 className="h-6 w-6 text-primary" />
            {t("models.title")}
          </h1>
          <p className="text-sm text-muted-foreground mt-1">{t("models.subtitle")}</p>
        </div>
        {models.length >= 2 && (
          <Link href="/models/compare">
            <Button variant="outline" size="sm">
              <GitCompare className="h-4 w-4 mr-1" />
              {t("models.compare")}
            </Button>
          </Link>
        )}
      </div>

      {/* Filters */}
      <div className="flex gap-3">
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder={t("models.search")}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-lg border border-input bg-background px-3 py-2 text-sm text-foreground focus:border-primary focus:outline-none"
        >
          <option value="">{t("models.allStatuses")}</option>
          <option value="completed">{t("models.statusCompleted")}</option>
          <option value="running">{t("models.statusRunning")}</option>
          <option value="failed">{t("models.statusFailed")}</option>
        </select>
      </div>

      {loading ? (
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)}
        </div>
      ) : filtered.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <BarChart3 className="mx-auto h-10 w-10 text-muted-foreground mb-3" />
            <p className="text-foreground font-medium">{models.length === 0 ? t("models.noModels") : t("models.noResults")}</p>
            <p className="text-sm text-muted-foreground mt-1">
              {models.length === 0 ? t("models.noModelsDesc") : t("models.noResultsDesc")}
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {filtered.map((model) => {
            const metrics = model.metrics || {};
            const hasMetrics = Object.keys(metrics).length > 0;
            return (
              <Link key={model.id} href={`/models/${model.id}`}>
                <Card className="p-5 animate-fade-in hover:border-primary/50 transition-colors cursor-pointer group">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-foreground">{model.model_name}</h3>
                        <Badge variant="secondary">v{model.version}</Badge>
                        <Badge variant={
                          model.status === "completed" ? "success" :
                          model.status === "running" ? "default" :
                          model.status === "failed" ? "destructive" : "outline"
                        }>{t(`models.status${(model.status || "unknown").charAt(0).toUpperCase() + (model.status || "unknown").slice(1)}`)}</Badge>
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">
                        {model.model_type} · {model.asset} · {formatDate(model.created_at)}
                      </p>
                    </div>
                    <ArrowRight className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
                  </div>

                  {hasMetrics && (
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4">
                      {Object.entries(metrics).slice(0, 4).map(([k, v]: any) => (
                        <div key={k} className="rounded-lg bg-secondary/50 p-3">
                          <p className="text-xs text-muted-foreground">{k}</p>
                          <p className="text-sm font-medium text-foreground mt-1">
                            {typeof v === "number" ? v.toFixed(4) : String(v)}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}

                  {(model.train_loss != null || model.val_loss != null) && (
                    <div className="flex gap-6 mt-3 text-sm">
                      {model.train_loss != null && (
                        <span className="text-muted-foreground">
                          {t("models.trainLoss")}: <span className="text-foreground font-medium">{Number(model.train_loss).toFixed(4)}</span>
                        </span>
                      )}
                      {model.val_loss != null && (
                        <span className="text-muted-foreground">
                          {t("models.valLoss")}: <span className="text-foreground font-medium">{Number(model.val_loss).toFixed(4)}</span>
                        </span>
                      )}
                    </div>
                  )}
                </Card>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
