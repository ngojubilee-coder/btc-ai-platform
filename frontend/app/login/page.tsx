"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";
import { useAuth, isLocalMode, LOCAL_EMAIL, LOCAL_PASSWORD } from "@/components/auth-provider";
import { useI18n } from "@/lib/i18n";
import { Bitcoin, Mail, Lock, Loader2, Info } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const { user, loading } = useAuth();
  const { t } = useI18n();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!loading && user) {
      router.push("/dashboard");
    }
  }, [user, loading, router]);

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      if (isLocalMode) {
        if (email === LOCAL_EMAIL && password === LOCAL_PASSWORD) {
          localStorage.setItem("btc-ai-local-auth", "true");
          router.push("/dashboard");
        } else {
          setError("Invalid credentials. Use the local credentials shown below.");
        }
      } else {
        const { error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) throw error;
        router.push("/dashboard");
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  async function handleSignUp(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      if (isLocalMode) {
        setError("Sign-up is disabled in local mode. Use the credentials shown below.");
      } else {
        const { error } = await supabase.auth.signUp({ email, password });
        if (error) throw error;
        setError(t("login.accountCreated"));
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-background via-background to-primary/5 p-4">
      <div className="w-full max-w-md space-y-8 rounded-xl border border-border bg-card p-8 shadow-2xl">
        <div className="text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary/10 ring-4 ring-primary/5">
            <Bitcoin className="h-8 w-8 text-primary" />
          </div>
          <h1 className="text-2xl font-bold text-foreground">{t("login.title")}</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            {t("login.subtitle")}
          </p>
        </div>

        <div className="grid grid-cols-3 gap-2 text-center">
          {[
            { label: t("login.dataset"), value: t("login.datasetValue") },
            { label: t("login.features"), value: "200+" },
            { label: t("login.llm"), value: "Multi" },
          ].map((s) => (
            <div key={s.label} className="rounded-lg bg-secondary/30 p-2">
              <p className="text-xs font-medium text-foreground">{s.value}</p>
              <p className="text-[10px] text-muted-foreground mt-0.5">{s.label}</p>
            </div>
          ))}
        </div>

        <form className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">{t("login.email")}</label>
            <div className="relative">
              <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-lg border border-input bg-background py-2 pl-10 pr-3 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none"
                placeholder="you@example.com"
                required
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">{t("login.password")}</label>
            <div className="relative">
              <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-lg border border-input bg-background py-2 pl-10 pr-3 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none"
                placeholder="••••••••"
                required
              />
            </div>
          </div>

          {error && (
            <p className="text-sm text-destructive">{error}</p>
          )}

          {isLocalMode && (
            <div className="rounded-lg border border-blue-500/30 bg-blue-500/10 p-3 text-xs text-blue-400">
              <div className="flex items-center gap-2 font-medium mb-1">
                <Info className="h-4 w-4" />
                Mode Local (sans Supabase)
              </div>
              <p>Email: <code className="text-blue-300">{LOCAL_EMAIL}</code></p>
              <p>Mot de passe: <code className="text-blue-300">{LOCAL_PASSWORD}</code></p>
            </div>
          )}

          <div className="flex gap-3">
            <button
              onClick={handleLogin}
              disabled={submitting}
              className="flex-1 rounded-lg bg-primary py-2.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              {submitting ? <Loader2 className="mx-auto h-4 w-4 animate-spin" /> : t("login.login")}
            </button>
            <button
              onClick={handleSignUp}
              disabled={submitting}
              className="flex-1 rounded-lg border border-border bg-secondary py-2.5 text-sm font-medium text-secondary-foreground hover:bg-secondary/80 disabled:opacity-50"
            >
              {t("login.signup")}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
