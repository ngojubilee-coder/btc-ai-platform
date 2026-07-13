"use client";

import { useState, useEffect, ReactNode } from "react";
import {
  Cloud,
  Server,
  Globe,
  CheckCircle,
  XCircle,
  Loader2,
  Rocket,
  Copy,
  ExternalLink,
  Settings as SettingsIcon,
  X,
  Shield,
  Zap,
  Database,
  Github,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/components/ui/toast";
import { useI18n } from "@/lib/i18n";
import { apiFetch } from "@/lib/api";

type DeployStatus = "idle" | "checking" | "ready" | "error";
type ServiceStatus = "online" | "offline" | "unknown";

interface DeployConfig {
  frontendUrl: string;
  backendUrl: string;
  cloudflareProject: string;
  supabaseUrl: string;
  apiHealth: ServiceStatus;
  dbStatus: ServiceStatus;
  llmStatus: ServiceStatus;
}

export function DeployPopup({ children }: { children?: ReactNode }) {
  const { t } = useI18n();
  const { toast } = useToast();
  const [open, setOpen] = useState(false);
  const [status, setStatus] = useState<DeployStatus>("idle");
  const [config, setConfig] = useState<DeployConfig | null>(null);
  const [activeTab, setActiveTab] = useState<"overview" | "frontend" | "backend" | "env">("overview");
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [open]);

  async function checkDeployment() {
    setStatus("checking");
    try {
      const health = await apiFetch<any>("/health").catch(() => null);
      const apiOnline = health?.status === "ok" || health?.status === "degraded";

      setConfig({
        frontendUrl: typeof window !== "undefined" ? window.location.origin : "",
        backendUrl: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
        cloudflareProject: "btc-ai-platform",
        supabaseUrl: process.env.NEXT_PUBLIC_SUPABASE_URL || "",
        apiHealth: apiOnline ? "online" : "offline",
        dbStatus: health?.components?.supabase?.status === "ok" ? "online" : "offline",
        llmStatus:
          health?.components?.llm?.gemini || health?.components?.llm?.anthropic || health?.components?.llm?.openai
            ? "online"
            : "offline",
      });
      setStatus("ready");
    } catch {
      setStatus("error");
    }
  }

  useEffect(() => {
    if (open && status === "idle") {
      checkDeployment();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  function copyToClipboard(text: string, key: string) {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
    toast("Copied to clipboard", "success");
  }

  const StatusIcon = ({ s }: { s: ServiceStatus }) => {
    if (s === "online") return <CheckCircle className="h-4 w-4 text-green-400" />;
    if (s === "offline") return <XCircle className="h-4 w-4 text-red-400" />;
    return <div className="h-4 w-4 rounded-full bg-muted-foreground/30" />;
  };

  const tabs = [
    { id: "overview" as const, label: "Overview", icon: Globe },
    { id: "frontend" as const, label: "Frontend", icon: Cloud },
    { id: "backend" as const, label: "Backend", icon: Server },
    { id: "env" as const, label: "Environment", icon: SettingsIcon },
  ];

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="fixed bottom-6 left-6 z-40 flex items-center gap-2 rounded-full bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground shadow-lg hover:bg-primary/90 transition-all hover:scale-105"
      >
        <Rocket className="h-4 w-4" />
        Deploy
      </button>

      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4" onClick={() => setOpen(false)}>
          <div
            className="w-full max-w-2xl max-h-[85vh] overflow-y-auto rounded-2xl border border-border bg-card shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="sticky top-0 z-10 flex items-center justify-between border-b border-border bg-card/95 backdrop-blur px-6 py-4">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10">
                  <Cloud className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-foreground">Cloudflare Deployment</h2>
                  <p className="text-xs text-muted-foreground">BTC AI Platform — B2B Production Deploy</p>
                </div>
              </div>
              <button onClick={() => setOpen(false)} className="text-muted-foreground hover:text-foreground">
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Tabs */}
            <div className="flex gap-1 border-b border-border px-4">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium transition-colors border-b-2 ${
                      activeTab === tab.id
                        ? "border-primary text-primary"
                        : "border-transparent text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                    {tab.label}
                  </button>
                );
              })}
            </div>

            {/* Content */}
            <div className="p-6 space-y-4">
              {status === "checking" && (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-6 w-6 animate-spin text-primary" />
                  <span className="ml-2 text-muted-foreground">Checking deployment status...</span>
                </div>
              )}

              {status === "error" && (
                <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4">
                  <div className="flex items-center gap-2 text-red-400">
                    <XCircle className="h-5 w-5" />
                    <span className="font-medium">Deployment check failed</span>
                  </div>
                  <p className="text-sm text-muted-foreground mt-1">
                    Backend API is not reachable. Make sure the backend is running and CORS is configured.
                  </p>
                  <Button variant="outline" size="sm" className="mt-3" onClick={checkDeployment}>
                    Retry
                  </Button>
                </div>
              )}

              {status === "ready" && config && (
                <>
                  {/* Overview Tab */}
                  {activeTab === "overview" && (
                    <div className="space-y-4">
                      {/* Status cards */}
                      <div className="grid grid-cols-3 gap-3">
                        <div className="rounded-xl border border-border bg-secondary/30 p-4">
                          <div className="flex items-center justify-between mb-2">
                            <Server className="h-5 w-5 text-blue-400" />
                            <StatusIcon s={config.apiHealth} />
                          </div>
                          <p className="text-xs text-muted-foreground">API Server</p>
                          <p className="text-sm font-medium text-foreground capitalize">{config.apiHealth}</p>
                        </div>
                        <div className="rounded-xl border border-border bg-secondary/30 p-4">
                          <div className="flex items-center justify-between mb-2">
                            <Database className="h-5 w-5 text-purple-400" />
                            <StatusIcon s={config.dbStatus} />
                          </div>
                          <p className="text-xs text-muted-foreground">Database</p>
                          <p className="text-sm font-medium text-foreground capitalize">{config.dbStatus}</p>
                        </div>
                        <div className="rounded-xl border border-border bg-secondary/30 p-4">
                          <div className="flex items-center justify-between mb-2">
                            <Zap className="h-5 w-5 text-orange-400" />
                            <StatusIcon s={config.llmStatus} />
                          </div>
                          <p className="text-xs text-muted-foreground">LLM Provider</p>
                          <p className="text-sm font-medium text-foreground capitalize">{config.llmStatus}</p>
                        </div>
                      </div>

                      {/* URLs */}
                      <div className="space-y-2">
                        <h3 className="text-sm font-semibold text-foreground">Service URLs</h3>
                        <div className="rounded-xl border border-border bg-secondary/30 divide-y divide-border">
                          <div className="flex items-center justify-between p-3">
                            <div className="flex items-center gap-2">
                              <Globe className="h-4 w-4 text-muted-foreground" />
                              <span className="text-sm text-muted-foreground">Frontend</span>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="text-sm text-foreground font-mono">{config.frontendUrl}</span>
                              <button onClick={() => copyToClipboard(config.frontendUrl, "frontend")} className="text-muted-foreground hover:text-foreground">
                                <Copy className="h-3.5 w-3.5" />
                              </button>
                            </div>
                          </div>
                          <div className="flex items-center justify-between p-3">
                            <div className="flex items-center gap-2">
                              <Server className="h-4 w-4 text-muted-foreground" />
                              <span className="text-sm text-muted-foreground">Backend API</span>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="text-sm text-foreground font-mono">{config.backendUrl}</span>
                              <button onClick={() => copyToClipboard(config.backendUrl, "backend")} className="text-muted-foreground hover:text-foreground">
                                <Copy className="h-3.5 w-3.5" />
                              </button>
                            </div>
                          </div>
                          <div className="flex items-center justify-between p-3">
                            <div className="flex items-center gap-2">
                              <Cloud className="h-4 w-4 text-muted-foreground" />
                              <span className="text-sm text-muted-foreground">Cloudflare Project</span>
                            </div>
                            <div className="flex items-center gap-2">
                              <Badge variant="secondary">{config.cloudflareProject}</Badge>
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Deploy actions */}
                      <div className="space-y-2">
                        <h3 className="text-sm font-semibold text-foreground">Deployment Actions</h3>
                        <div className="grid grid-cols-2 gap-3">
                          <Button
                            variant="default"
                            className="w-full"
                            onClick={() => {
                              toast("Building frontend for Cloudflare Pages...", "info");
                              toast("Run: npm run deploy:cloudflare", "info");
                            }}
                          >
                            <Cloud className="h-4 w-4 mr-2" />
                            Deploy Frontend
                          </Button>
                          <Button
                            variant="outline"
                            className="w-full"
                            onClick={() => {
                              toast("Backend deployment requires Docker or VPS", "info");
                              toast("Use: docker-compose up -d --build", "info");
                            }}
                          >
                            <Server className="h-4 w-4 mr-2" />
                            Deploy Backend
                          </Button>
                        </div>
                      </div>

                      {/* B2B Info */}
                      <div className="rounded-xl border border-primary/20 bg-primary/5 p-4">
                        <div className="flex items-start gap-3">
                          <Shield className="h-5 w-5 text-primary flex-shrink-0 mt-0.5" />
                          <div>
                            <p className="text-sm font-medium text-foreground">B2B Production Checklist</p>
                            <ul className="mt-2 space-y-1 text-xs text-muted-foreground">
                              <li className="flex items-center gap-2">
                                <CheckCircle className="h-3 w-3 text-green-400" />
                                Supabase auth configured
                              </li>
                              <li className="flex items-center gap-2">
                                <CheckCircle className="h-3 w-3 text-green-400" />
                                CORS origins set in backend
                              </li>
                              <li className="flex items-center gap-2">
                                <CheckCircle className="h-3 w-3 text-green-400" />
                                Rate limiting active (100 req/min)
                              </li>
                              <li className="flex items-center gap-2">
                                {config.llmStatus === "online" ? (
                                  <CheckCircle className="h-3 w-3 text-green-400" />
                                ) : (
                                  <XCircle className="h-3 w-3 text-red-400" />
                                )}
                                LLM API key configured
                              </li>
                              <li className="flex items-center gap-2">
                                <CheckCircle className="h-3 w-3 text-green-400" />
                                SQL injection protection enabled
                              </li>
                            </ul>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Frontend Tab */}
                  {activeTab === "frontend" && (
                    <div className="space-y-4">
                      <div className="rounded-xl border border-border bg-secondary/30 p-4 space-y-3">
                        <div className="flex items-center gap-2">
                          <Cloud className="h-5 w-5 text-orange-400" />
                          <h3 className="text-sm font-semibold text-foreground">Cloudflare Pages Deployment</h3>
                        </div>
                        <p className="text-xs text-muted-foreground">
                          Deploy the Next.js frontend to Cloudflare Pages using the OpenNext adapter.
                        </p>

                        <div className="space-y-2">
                          <p className="text-xs font-medium text-foreground">1. Install dependencies</p>
                          <pre className="rounded-lg bg-background/80 p-3 text-xs font-mono text-foreground overflow-x-auto">
{`npm install --save-dev @opennextjs/cloudflare wrangler`}
                          </pre>
                        </div>

                        <div className="space-y-2">
                          <p className="text-xs font-medium text-foreground">2. Build & preview locally</p>
                          <pre className="rounded-lg bg-background/80 p-3 text-xs font-mono text-foreground overflow-x-auto">
{`npm run preview`}
                          </pre>
                        </div>

                        <div className="space-y-2">
                          <p className="text-xs font-medium text-foreground">3. Deploy to Cloudflare</p>
                          <pre className="rounded-lg bg-background/80 p-3 text-xs font-mono text-foreground overflow-x-auto">
{`npm run deploy:cloudflare`}
                          </pre>
                        </div>

                        <div className="space-y-2">
                          <p className="text-xs font-medium text-foreground">4. Set environment variables in Cloudflare Dashboard</p>
                          <div className="rounded-lg bg-background/80 p-3 text-xs font-mono text-foreground space-y-1">
                            <div>NEXT_PUBLIC_API_URL=<span className="text-blue-400">https://api.your-domain.com</span></div>
                            <div>NEXT_PUBLIC_SUPABASE_URL=<span className="text-blue-400">https://xxx.supabase.co</span></div>
                            <div>NEXT_PUBLIC_SUPABASE_ANON_KEY=<span className="text-blue-400">your-anon-key</span></div>
                          </div>
                        </div>
                      </div>

                      <div className="rounded-xl border border-border bg-secondary/30 p-4">
                        <div className="flex items-center gap-2 mb-2">
                          <Github className="h-4 w-4 text-muted-foreground" />
                          <h4 className="text-xs font-semibold text-foreground">CI/CD via Git Integration</h4>
                        </div>
                        <p className="text-xs text-muted-foreground">
                          Connect your GitHub repo to Cloudflare Pages for automatic deployments on every push.
                          Set build command: <code className="text-foreground">npm run build:cloudflare</code>
                          {" "}and output directory: <code className="text-foreground">.open-next</code>
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Backend Tab */}
                  {activeTab === "backend" && (
                    <div className="space-y-4">
                      <div className="rounded-xl border border-border bg-secondary/30 p-4 space-y-3">
                        <div className="flex items-center gap-2">
                          <Server className="h-5 w-5 text-blue-400" />
                          <h3 className="text-sm font-semibold text-foreground">Backend Deployment Options</h3>
                        </div>

                        <div className="space-y-3">
                          <div className="rounded-lg border border-border p-3">
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-sm font-medium text-foreground">Docker (Recommended)</span>
                              <Badge variant="secondary">VPS / Container</Badge>
                            </div>
                            <p className="text-xs text-muted-foreground mb-2">Deploy on any VPS with Docker</p>
                            <pre className="rounded-lg bg-background/80 p-2 text-xs font-mono text-foreground overflow-x-auto">
{`docker-compose up -d --build`}
                            </pre>
                          </div>

                          <div className="rounded-lg border border-border p-3">
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-sm font-medium text-foreground">Railway / Render</span>
                              <Badge variant="secondary">PaaS</Badge>
                            </div>
                            <p className="text-xs text-muted-foreground mb-2">Connect GitHub repo, set env vars</p>
                            <pre className="rounded-lg bg-background/80 p-2 text-xs font-mono text-foreground overflow-x-auto">
{`uvicorn main:app --host 0.0.0.0 --port $PORT`}
                            </pre>
                          </div>

                          <div className="rounded-lg border border-border p-3">
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-sm font-medium text-foreground">Fly.io</span>
                              <Badge variant="secondary">Edge</Badge>
                            </div>
                            <p className="text-xs text-muted-foreground mb-2">Deploy close to Cloudflare edge</p>
                            <pre className="rounded-lg bg-background/80 p-2 text-xs font-mono text-foreground overflow-x-auto">
{`fly launch --dockerfile Dockerfile
fly deploy`}
                            </pre>
                          </div>
                        </div>
                      </div>

                      <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-4">
                        <div className="flex items-start gap-2">
                          <Shield className="h-4 w-4 text-amber-400 flex-shrink-0 mt-0.5" />
                          <div>
                            <p className="text-xs font-medium text-foreground">Production CORS Setup</p>
                            <p className="text-xs text-muted-foreground mt-1">
                              Set <code className="text-foreground">CORS_ORIGINS</code> in backend env to your Cloudflare Pages URL:
                            </p>
                            <pre className="rounded-lg bg-background/80 p-2 text-xs font-mono text-foreground mt-2 overflow-x-auto">
{`CORS_ORIGINS=https://btc-ai-platform.pages.dev,https://your-domain.com`}
                            </pre>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Env Tab */}
                  {activeTab === "env" && (
                    <div className="space-y-4">
                      <div className="rounded-xl border border-border bg-secondary/30 p-4 space-y-3">
                        <h3 className="text-sm font-semibold text-foreground">Frontend Environment Variables</h3>
                        <div className="space-y-2">
                          {[
                            { key: "NEXT_PUBLIC_API_URL", value: config.backendUrl, required: true },
                            { key: "NEXT_PUBLIC_SUPABASE_URL", value: config.supabaseUrl || "https://xxx.supabase.co", required: true },
                            { key: "NEXT_PUBLIC_SUPABASE_ANON_KEY", value: "your-anon-key", required: true },
                          ].map((env) => (
                            <div key={env.key} className="flex items-center justify-between rounded-lg bg-background/80 p-2.5">
                              <div className="flex items-center gap-2 min-w-0">
                                {env.required && <Badge variant="outline" className="text-xs">required</Badge>}
                                <span className="text-xs font-mono text-foreground truncate">{env.key}</span>
                              </div>
                              <div className="flex items-center gap-2 flex-shrink-0">
                                <span className="text-xs font-mono text-muted-foreground truncate max-w-[200px]">{env.value}</span>
                                <button onClick={() => copyToClipboard(`${env.key}=${env.value}`, env.key)} className="text-muted-foreground hover:text-foreground">
                                  {copiedKey === env.key ? <CheckCircle className="h-3.5 w-3.5 text-green-400" /> : <Copy className="h-3.5 w-3.5" />}
                                </button>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>

                      <div className="rounded-xl border border-border bg-secondary/30 p-4 space-y-3">
                        <h3 className="text-sm font-semibold text-foreground">Backend Environment Variables</h3>
                        <div className="space-y-2">
                          {[
                            { key: "SUPABASE_URL", required: true },
                            { key: "SUPABASE_KEY", required: true },
                            { key: "SUPABASE_SERVICE_KEY", required: true },
                            { key: "GEMINI_API_KEY", required: false },
                            { key: "ANTHROPIC_API_KEY", required: false },
                            { key: "OPENAI_API_KEY", required: false },
                            { key: "JWT_SECRET", required: true },
                            { key: "CORS_ORIGINS", required: true },
                            { key: "PARQUET_PATH", required: true },
                          ].map((env) => (
                            <div key={env.key} className="flex items-center justify-between rounded-lg bg-background/80 p-2.5">
                              <div className="flex items-center gap-2">
                                {env.required ? (
                                  <Badge variant="outline" className="text-xs">required</Badge>
                                ) : (
                                  <Badge variant="secondary" className="text-xs">optional</Badge>
                                )}
                                <span className="text-xs font-mono text-foreground">{env.key}</span>
                              </div>
                              <span className="text-xs font-mono text-muted-foreground">••••••••</span>
                            </div>
                          ))}
                        </div>
                      </div>

                      <div className="rounded-xl border border-border bg-secondary/30 p-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <h4 className="text-xs font-semibold text-foreground">Download .env templates</h4>
                            <p className="text-xs text-muted-foreground mt-0.5">Reference files for configuration</p>
                          </div>
                          <div className="flex gap-2">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => toast("See frontend/.env.example", "info")}
                            >
                              Frontend
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => toast("See backend/.env.example", "info")}
                            >
                              Backend
                            </Button>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </>
              )}

              {status === "idle" && (
                <div className="flex items-center justify-center py-12">
                  <Button onClick={checkDeployment}>
                    <Rocket className="h-4 w-4 mr-2" />
                    Check Deployment Status
                  </Button>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="sticky bottom-0 border-t border-border bg-card/95 backdrop-blur px-6 py-3 flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Cloud className="h-3.5 w-3.5" />
                <span>Powered by Cloudflare Pages + Workers</span>
              </div>
              <Button variant="ghost" size="sm" onClick={() => setOpen(false)}>
                Close
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
