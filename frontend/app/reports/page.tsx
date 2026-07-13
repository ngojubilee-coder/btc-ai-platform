"use client";

import { useEffect, useState } from "react";
import { apiFetch, apiPost, apiFetchText } from "@/lib/api";
import { FileText, Download, FileCode, BarChart3, TrendingUp, Clock, CheckCircle, Loader2, FileBarChart, Newspaper, Eye, X } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { SkeletonCard } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { useI18n } from "@/lib/i18n";
import { formatDate } from "@/lib/utils";

interface Report {
  id: string;
  title: string;
  report_type: string;
  type?: string;
  status: string;
  created_at: string;
  url?: string;
}

const REPORT_TYPES = [
  {
    type: "training",
    titleKey: "reports.training",
    descKey: "reports.trainingDesc",
    icon: FileText,
    color: "text-primary",
  },
  {
    type: "comparison",
    titleKey: "reports.comparison",
    descKey: "reports.comparisonDesc",
    icon: FileCode,
    color: "text-purple-400",
  },
  {
    type: "dataset",
    titleKey: "reports.dataset",
    descKey: "reports.datasetDesc",
    icon: BarChart3,
    color: "text-green-400",
  },
  {
    type: "market",
    titleKey: "reports.market",
    descKey: "reports.marketDesc",
    icon: TrendingUp,
    color: "text-orange-400",
  },
];

export default function ReportsPage() {
  const { toast } = useToast();
  const { t, lang } = useI18n();
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState<string | null>(null);
  const [selectedReport, setSelectedReport] = useState<any>(null);

  useEffect(() => {
    if (!selectedReport) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") setSelectedReport(null);
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [selectedReport]);

  useEffect(() => {
    loadReports();
  }, []);

  async function loadReports() {
    setLoading(true);
    try {
      const data = await apiFetch<Report[]>("/api/models/reports").catch(() => []);
      setReports(data || []);
    } catch {}
    setLoading(false);
  }

  async function generateReport(type: string) {
    setGenerating(type);
    try {
      const result = await apiPost<any>("/api/models/reports/generate", { type, lang });
      toast(t("reports.generated"), "success");
      loadReports();
    } catch {
      toast(t("reports.generatedDemo"), "info");
      const newReport: Report = {
        id: Math.random().toString(36).slice(2),
        title: t(REPORT_TYPES.find((r) => r.type === type)?.titleKey || "reports.training"),
        report_type: type,
        status: "completed",
        created_at: new Date().toISOString(),
      };
      setReports((prev) => [newReport, ...prev]);
    }
    setGenerating(null);
  }

  async function downloadReport(report: Report) {
    const rType = report.report_type || report.type || "unknown";
    try {
      const content = await apiFetchText(`/api/models/reports/${report.id}/download`);
      const blob = new Blob([content], { type: "text/markdown" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `report-${rType}-${new Date(report.created_at).toISOString().slice(0, 10)}.md`;
      a.click();
      URL.revokeObjectURL(url);
      toast(t("reports.downloaded"), "success");
    } catch {
      const content = `# ${report.title}\n\n${t("reports.type")}: ${rType}\n${t("reports.date")}: ${formatDate(report.created_at)}\n\n## ${t("reports.content")}\n\n${t("reports.generatedBy")}`;
      const blob = new Blob([content], { type: "text/markdown" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `report-${rType}-${new Date(report.created_at).toISOString().slice(0, 10)}.md`;
      a.click();
      URL.revokeObjectURL(url);
      toast(t("reports.downloadedLocal"), "info");
    }
  }

  async function viewReport(report: Report) {
    try {
      const data = await apiFetch<any>(`/api/models/reports/${report.id}`);
      if (data && !data.error) {
        setSelectedReport(data);
      } else {
        toast(t("reports.contentUnavailable"), "error");
      }
    } catch {
      toast(t("reports.loadError"), "error");
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
          <FileText className="h-6 w-6 text-primary" />
          {t("reports.title")}
        </h1>
        <p className="text-sm text-muted-foreground mt-1">{t("reports.subtitle")}</p>
      </div>

      {/* Report types */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {REPORT_TYPES.map((r) => {
          const Icon = r.icon;
          const isGenerating = generating === r.type;
          return (
            <Card key={r.type} className="p-6">
              <Icon className={`h-8 w-8 ${r.color} mb-3`} />
              <h3 className="font-semibold text-foreground">{t(r.titleKey)}</h3>
              <p className="text-sm text-muted-foreground mt-1">{t(r.descKey)}</p>
              <Button
                onClick={() => generateReport(r.type)}
                disabled={isGenerating}
                variant="default"
                size="sm"
                className="mt-4"
              >
                {isGenerating ? (
                  <><Loader2 className="h-4 w-4 mr-1 animate-spin" /> {t("reports.generating")}</>
                ) : (
                  <><FileBarChart className="h-4 w-4 mr-1" /> {t("reports.generate")}</>
                )}
              </Button>
            </Card>
          );
        })}
      </div>

      {/* Recent reports */}
      <Card>
        <CardHeader>
          <CardTitle>{t("reports.recentReports")}</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-3">
              {Array.from({ length: 3 }).map((_, i) => <SkeletonCard key={i} />)}
            </div>
          ) : reports.length === 0 ? (
            <div className="text-center py-8">
              <FileText className="mx-auto h-8 w-8 text-muted-foreground mb-2 opacity-50" />
              <p className="text-sm text-muted-foreground">{t("reports.noReports")}</p>
            </div>
          ) : (
            <div className="space-y-2">
              {reports.map((report) => (
                <div
                  key={report.id}
                  className="flex items-center gap-4 rounded-lg border border-border p-3 hover:bg-secondary/30 transition-colors"
                >
                  <div className="flex-shrink-0">
                    {report.status === "completed" ? (
                      <CheckCircle className="h-5 w-5 text-green-400" />
                    ) : report.status === "running" ? (
                      <Loader2 className="h-5 w-5 text-blue-400 animate-spin" />
                    ) : (
                      <FileText className="h-5 w-5 text-muted-foreground" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-foreground">{report.title}</p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <Badge variant="outline" className="text-xs">{t(`reports.type_${report.report_type || report.type}`)}</Badge>
                      <span className="text-xs text-muted-foreground flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {formatDate(report.created_at)}
                      </span>
                    </div>
                  </div>
                  {report.status === "completed" && (
                    <div className="flex gap-1">
                      <Button variant="ghost" size="sm" onClick={() => viewReport(report)}>
                        <Eye className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => downloadReport(report)}>
                        <Download className="h-4 w-4" />
                      </Button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Report viewer modal */}
      {selectedReport && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={() => setSelectedReport(null)}>
          <div className="w-full max-w-3xl max-h-[80vh] overflow-hidden rounded-xl border border-border bg-card flex flex-col" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between border-b border-border p-4">
              <div>
                <h3 className="font-semibold text-foreground">{selectedReport.title}</h3>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {t(`reports.type_${selectedReport.report_type}`)} · {formatDate(selectedReport.created_at)}
                </p>
              </div>
              <button onClick={() => setSelectedReport(null)} className="text-muted-foreground hover:text-foreground">
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="overflow-y-auto p-6">
              <pre className="text-sm text-foreground whitespace-pre-wrap font-mono">{selectedReport.content || t("reports.noContent")}</pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
