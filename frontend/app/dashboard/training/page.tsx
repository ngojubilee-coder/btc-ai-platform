"use client";

import { useEffect, useState, useCallback } from "react";
import { apiFetch } from "@/lib/api";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Cpu, Play, RefreshCw, TrendingUp, Clock, Target, Trophy, BarChart3 } from "lucide-react";

interface ModelResult {
  model: string;
  accuracy: number;
  f1: number;
  precision: number;
  recall: number;
  train_time_sec: number;
  backtest?: {
    win_rate: number;
    correct: number;
    total: number;
    pnl: number;
  };
  top_features?: Record<string, number>;
}

interface TrainingStatus {
  dataset: { exists: boolean; size_mb: number; path: string };
  models: { count: number; files: string[] };
  results: { count: number; csv_count: number; last: any };
}

export default function TrainingPage() {
  const [results, setResults] = useState<ModelResult[]>([]);
  const [status, setStatus] = useState<TrainingStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [training, setTraining] = useState(false);
  const [health, setHealth] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchResults = useCallback(async () => {
    setLoading(true);
    try {
      const [h, s, r] = await Promise.all([
        apiFetch<any>("/health").catch(() => null),
        apiFetch<any>("/api/training/status").catch(() => null),
        apiFetch<any>("/api/training/results?limit=10").catch(() => null),
      ]);
      setHealth(h);
      setStatus(s);
      setResults(r?.results || []);
    } catch {}
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchResults();
  }, [fetchResults]);

  const startTraining = async (model: string) => {
    setTraining(true);
    setError(null);
    try {
      await apiFetch<any>(`/api/models/reports/generate`, {
        method: "POST",
        body: JSON.stringify({ type: "training", lang: "fr" }),
      });
      fetchResults();
    } catch (err: any) {
      setError(err.message);
    }
    setTraining(false);
  };

  const components = health?.components || {};
  const llmInfo = components.llm || {};
  const duckdbOk = components.duckdb?.status === "ok";
  const datasetRows = components.duckdb?.rows || 0;

  const models = [
    {
      name: "xgboost",
      label: "XGBoost",
      desc: "Gradient Boosting - rapide et performant",
      color: "text-blue-400",
      icon: TrendingUp,
    },
    {
      name: "random_forest",
      label: "Random Forest",
      desc: "Robuste, bon pour baseline",
      color: "text-green-400",
      icon: BarChart3,
    },
    {
      name: "lstm",
      label: "LSTM",
      desc: "Deep Learning TensorFlow/Keras",
      color: "text-purple-400",
      icon: Cpu,
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Entrainement des Modeles</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Pipeline ML local - XGBoost, Random Forest, LSTM
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchResults} disabled={loading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} />
          Actualiser
        </Button>
      </div>

      {/* System status */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center gap-2 mb-2">
            <Target className="h-4 w-4 text-blue-400" />
            <span className="text-sm text-muted-foreground">Dataset</span>
          </div>
          <p className="text-xl font-bold text-foreground">{datasetRows.toLocaleString()}</p>
          <p className="text-xs text-muted-foreground">{status?.dataset?.size_mb || 0} MB</p>
          <Badge variant={duckdbOk ? "success" : "destructive"} className="mt-2">
            {duckdbOk ? "OK" : "Absent"}
          </Badge>
        </Card>

        <Card className="p-4">
          <div className="flex items-center gap-2 mb-2">
            <Cpu className="h-4 w-4 text-purple-400" />
            <span className="text-sm text-muted-foreground">Modeles sauves</span>
          </div>
          <p className="text-xl font-bold text-foreground">{status?.models?.count || 0}</p>
          <p className="text-xs text-muted-foreground">fichiers</p>
          <div className="mt-2 flex flex-wrap gap-1">
            {(status?.models?.files || []).map((f: string) => (
              <Badge key={f} variant="outline" className="text-xs">{f}</Badge>
            ))}
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center gap-2 mb-2">
            <Trophy className="h-4 w-4 text-orange-400" />
            <span className="text-sm text-muted-foreground">Resultats</span>
          </div>
          <p className="text-xl font-bold text-foreground">{status?.results?.count || 0}</p>
          <p className="text-xs text-muted-foreground">{status?.results?.csv_count || 0} comparaisons CSV</p>
        </Card>

        <Card className="p-4">
          <div className="flex items-center gap-2 mb-2">
            <Clock className="h-4 w-4 text-green-400" />
            <span className="text-sm text-muted-foreground">Statut API</span>
          </div>
          <p className="text-xl font-bold text-foreground">{health?.status || "..."}</p>
          <Badge variant={health?.status === "ok" ? "success" : "secondary"} className="mt-2">
            {health?.status || "Chargement"}
          </Badge>
        </Card>
      </div>

      {/* Training buttons */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Play className="h-5 w-5 text-primary" />
            Lancer un entrainement
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {models.map((m) => {
              const Icon = m.icon;
              return (
                <div
                  key={m.name}
                  className="border border-border rounded-lg p-4 hover:bg-secondary/50 transition-colors"
                >
                  <div className="flex items-center gap-2 mb-2">
                    <Icon className={`h-5 w-5 ${m.color}`} />
                    <span className="font-medium text-foreground">{m.label}</span>
                  </div>
                  <p className="text-xs text-muted-foreground mb-3">{m.desc}</p>
                  <Button
                    size="sm"
                    className="w-full"
                    disabled={training}
                    onClick={() => startTraining(m.name)}
                  >
                    {training ? "En cours..." : `Entrainer ${m.label}`}
                  </Button>
                </div>
              );
            })}
          </div>
          {error && (
            <div className="mt-4 p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-sm text-destructive">
              {error}
            </div>
          )}
          <div className="mt-4 p-3 rounded-lg bg-secondary/50 text-xs text-muted-foreground">
            Pour un entrainement complet en local, lancez <code className="text-primary">train-vps.bat</code> depuis le dossier du projet.
            Le frontend affiche ici les rapports et resultats via l API backend.
          </div>
        </CardContent>
      </Card>

      {/* Results table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-primary" />
            Resultats d entrainement
          </CardTitle>
        </CardHeader>
        <CardContent>
          {results.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left py-2 px-3 text-muted-foreground">Modele</th>
                    <th className="text-right py-2 px-3 text-muted-foreground">Accuracy</th>
                    <th className="text-right py-2 px-3 text-muted-foreground">F1</th>
                    <th className="text-right py-2 px-3 text-muted-foreground">Win Rate</th>
                    <th className="text-right py-2 px-3 text-muted-foreground">PnL</th>
                    <th className="text-right py-2 px-3 text-muted-foreground">Temps</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((r, i) => (
                    <tr key={i} className="border-b border-border/50 hover:bg-secondary/30">
                      <td className="py-2 px-3 font-medium text-foreground">{r.model}</td>
                      <td className="text-right py-2 px-3 text-foreground">{(r.accuracy * 100).toFixed(2)}%</td>
                      <td className="text-right py-2 px-3 text-foreground">{r.f1 ? r.f1.toFixed(4) : "N/A"}</td>
                      <td className="text-right py-2 px-3 text-foreground">
                        {r.backtest ? `${r.backtest.win_rate.toFixed(2)}%` : "N/A"}
                      </td>
                      <td className={`text-right py-2 px-3 ${r.backtest && r.backtest.pnl >= 0 ? "text-green-400" : "text-red-400"}`}>
                        {r.backtest ? `${r.backtest.pnl >= 0 ? "+" : ""}${r.backtest.pnl}` : "N/A"}
                      </td>
                      <td className="text-right py-2 px-3 text-muted-foreground">{r.train_time_sec}s</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <p>Aucun resultat d entrainement disponible.</p>
              <p className="text-xs mt-2">Lancez <code className="text-primary">train-vps.bat</code> pour entrainer les modeles.</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
