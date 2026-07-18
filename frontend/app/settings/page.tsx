"use client";

import { useState, useEffect } from "react";
import { Settings as SettingsIcon, User, Bell, Shield, Database, Save, Check, Moon, Sun, Monitor, KeyRound, LogOut, MonitorSmartphone } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input, Select } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/components/auth-provider";
import { useToast } from "@/components/ui/toast";
import { useI18n } from "@/lib/i18n";
import { supabase } from "@/lib/supabase";

export default function SettingsPage() {
  const { user } = useAuth();
  const { toast } = useToast();
  const { t, lang, setLang } = useI18n();
  const [saved, setSaved] = useState(false);

  const [profile, setProfile] = useState({
    name: "",
    email: "",
  });

  const [prefs, setPrefs] = useState({
    llm: "gemini-2.0-flash",
    complexity: "simple",
    temperature: 0.7,
  });

  const [notifications, setNotifications] = useState({
    whale: true,
    price: true,
    news: false,
    training: true,
  });

  const [theme, setTheme] = useState("dark");
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [newPassword, setNewPassword] = useState("");
  const [changingPassword, setChangingPassword] = useState(false);

  useEffect(() => {
    if (!showPasswordModal) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") { setShowPasswordModal(false); setNewPassword(""); }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [showPasswordModal]);

  useEffect(() => {
    const stored = localStorage.getItem("btc-ai-prefs");
    if (stored) {
      const p = JSON.parse(stored);
      setPrefs(p.prefs || { llm: "gemini-2.0-flash", complexity: "simple", temperature: 0.7 });
      setNotifications(p.notifications || { whale: true, price: true, news: false, training: true });
      if (p.theme) setTheme(p.theme);
    }
    if (user) {
      setProfile({ name: user.user_metadata?.name || t("nav.analyst"), email: user.email || "" });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  async function handleChangePassword() {
    if (!newPassword || newPassword.length < 6) {
      toast(t("settings.passwordTooShort"), "error");
      return;
    }
    setChangingPassword(true);
    try {
      const { error } = await supabase.auth.updateUser({ password: newPassword });
      if (error) throw error;
      toast(t("settings.passwordChanged"), "success");
      setShowPasswordModal(false);
      setNewPassword("");
    } catch (err: any) {
      toast(err.message || t("settings.passwordError"), "error");
    }
    setChangingPassword(false);
  }

  async function handleSignOutAll() {
    try {
      await supabase.auth.signOut({ scope: "global" });
      toast(t("settings.signedOutAll"), "success");
      window.location.href = "/login";
    } catch (err: any) {
      toast(err.message || t("common.error"), "error");
    }
  }

  function handleSave() {
    localStorage.setItem("btc-ai-prefs", JSON.stringify({ prefs, notifications, profile, theme, lang }));
    setSaved(true);
    toast(t("settings.savedToast"), "success");
    setTimeout(() => setSaved(false), 2000);
  }

  function applyTheme(newTheme: string) {
    setTheme(newTheme);
    const html = document.documentElement;
    const apply = (isDark: boolean) => {
      if (isDark) html.classList.add("dark");
      else html.classList.remove("dark");
    };
    if (newTheme === "system") {
      apply(window.matchMedia("(prefers-color-scheme: dark)").matches);
    } else {
      apply(newTheme === "dark");
    }
  }

  useEffect(() => {
    if (theme !== "system") return;
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const handler = (e: MediaQueryListEvent) => {
      if (e.matches) document.documentElement.classList.add("dark");
      else document.documentElement.classList.remove("dark");
    };
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, [theme]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
            <SettingsIcon className="h-6 w-6 text-primary" />
            {t("settings.title")}
          </h1>
          <p className="text-sm text-muted-foreground mt-1">{t("settings.subtitle")}</p>
        </div>
        <Button onClick={handleSave} variant={saved ? "secondary" : "default"}>
          {saved ? <><Check className="h-4 w-4 mr-1" /> {t("settings.saved")}</> : <><Save className="h-4 w-4 mr-1" /> {t("settings.save")}</>}
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Profile */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <User className="h-5 w-5 text-primary" />
              <CardTitle>{t("settings.profile")}</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div>
                <label className="text-sm text-muted-foreground">{t("settings.name")}</label>
                <Input
                  value={profile.name}
                  onChange={(e) => setProfile({ ...profile, name: e.target.value })}
                  className="mt-1"
                />
              </div>
              <div>
                <label className="text-sm text-muted-foreground">{t("settings.email")}</label>
                <Input
                  value={profile.email}
                  onChange={(e) => setProfile({ ...profile, email: e.target.value })}
                  className="mt-1"
                  disabled
                />
                <p className="text-xs text-muted-foreground mt-1">{t("settings.emailDisabled")}</p>
              </div>
              <div className="flex items-center gap-2 pt-2">
                <Badge variant="secondary">{t("settings.plan")}: {t("settings.planFree")}</Badge>
                <Badge variant="outline">{t("settings.role")}: {t("settings.roleAnalyst")}</Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* AI Model */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Database className="h-5 w-5 text-purple-400" />
              <CardTitle>{t("settings.aiModel")}</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div>
                <label className="text-sm text-muted-foreground">{t("settings.defaultLlm")}</label>
                <Select
                  value={prefs.llm}
                  onChange={(e) => setPrefs({ ...prefs, llm: e.target.value })}
                  className="mt-1"
                >
                  <option value="gemini-2.0-flash">Gemini 2.0 Flash ({t("settings.fast")})</option>
                  <option value="gemini-2.0-pro">Gemini 2.0 Pro ({t("settings.inDepth")})</option>
                  <option value="claude-3.5-sonnet">Claude 3.5 Sonnet</option>
                  <option value="gpt-4o">GPT-4o</option>
                  <option value="ollama">Ollama ({t("settings.local")})</option>
                </Select>
              </div>
              <div>
                <label className="text-sm text-muted-foreground">{t("settings.defaultComplexity")}</label>
                <Select
                  value={prefs.complexity}
                  onChange={(e) => setPrefs({ ...prefs, complexity: e.target.value })}
                  className="mt-1"
                >
                  <option value="simple">{t("settings.simple")}</option>
                  <option value="complex">{t("settings.complex")}</option>
                </Select>
              </div>
              <div>
                <label className="text-sm text-muted-foreground">
                  {t("settings.temperature")}: {prefs.temperature.toFixed(1)}
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={prefs.temperature}
                  onChange={(e) => setPrefs({ ...prefs, temperature: Number(e.target.value) })}
                  className="w-full mt-2 accent-primary"
                />
                <div className="flex justify-between text-xs text-muted-foreground mt-1">
                  <span>{t("settings.precise")}</span>
                  <span>{t("settings.creative")}</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Notifications */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Bell className="h-5 w-5 text-orange-400" />
              <CardTitle>{t("settings.notifications")}</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {[
                { key: "whale", label: t("settings.whaleAlerts"), desc: t("settings.whaleAlertsDesc") },
                { key: "price", label: t("settings.priceMovements"), desc: t("settings.priceMovementsDesc") },
                { key: "news", label: t("settings.newsAlerts"), desc: t("settings.newsAlertsDesc") },
                { key: "training", label: t("settings.trainingAlerts"), desc: t("settings.trainingAlertsDesc") },
              ].map((item) => (
                <label key={item.key} className="flex items-center justify-between cursor-pointer">
                  <div>
                    <span className="text-sm text-foreground">{item.label}</span>
                    <p className="text-xs text-muted-foreground">{item.desc}</p>
                  </div>
                  <button
                    onClick={() => setNotifications({ ...notifications, [item.key]: !notifications[item.key as keyof typeof notifications] })}
                    className={`relative h-6 w-11 rounded-full transition-colors ${notifications[item.key as keyof typeof notifications] ? "bg-primary" : "bg-secondary"}`}
                  >
                    <span className={`absolute top-0.5 h-5 w-5 rounded-full bg-white transition-transform ${notifications[item.key as keyof typeof notifications] ? "translate-x-5" : "translate-x-0.5"}`} />
                  </button>
                </label>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Security */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Shield className="h-5 w-5 text-green-400" />
              <CardTitle>{t("settings.security")}</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <button
                onClick={() => setShowPasswordModal(true)}
                className="flex items-center justify-between w-full rounded-lg bg-secondary/50 p-3 text-sm text-foreground hover:bg-secondary transition-colors"
              >
                {t("settings.changePassword")}
                <Badge variant="outline">{t("settings.recommended")}</Badge>
              </button>
              <button className="flex items-center justify-between w-full rounded-lg bg-secondary/50 p-3 text-sm text-foreground hover:bg-secondary transition-colors">
                {t("settings.enable2fa")}
                <Badge variant="warning">{t("settings.notEnabled")}</Badge>
              </button>
              <button
                onClick={handleSignOutAll}
                className="flex items-center justify-between w-full rounded-lg bg-secondary/50 p-3 text-sm text-foreground hover:bg-secondary transition-colors"
              >
                {t("settings.signOutAll")}
                <Badge variant="success">{t("settings.activeSessions")}</Badge>
              </button>
              <button
                onClick={() => toast(t("settings.deleteAccountContact"), "info")}
                className="flex items-center justify-between w-full rounded-lg bg-destructive/10 p-3 text-sm text-destructive hover:bg-destructive/20 transition-colors mt-4"
              >
                {t("settings.deleteAccount")}
              </button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Theme */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Moon className="h-5 w-5 text-primary" />
            <CardTitle>{t("settings.appearance")}</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex gap-3">
            {[
              { value: "dark", label: t("settings.dark"), icon: Moon },
              { value: "light", label: t("settings.light"), icon: Sun },
              { value: "system", label: t("settings.system"), icon: Monitor },
            ].map((th) => {
              const Icon = th.icon;
              const isActive = theme === th.value;
              return (
                <button
                  key={th.value}
                  onClick={() => applyTheme(th.value)}
                  className={`flex items-center gap-2 rounded-lg border p-3 text-sm transition-colors ${
                    isActive
                      ? "border-primary bg-primary/10 text-primary"
                      : "border-border bg-secondary/50 text-foreground hover:bg-secondary"
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  {th.label}
                </button>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Language */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <MonitorSmartphone className="h-5 w-5 text-primary" />
            <CardTitle>{t("settings.language")}</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex gap-3">
            {[
              { value: "fr", label: "Français" },
              { value: "en", label: "English" },
            ].map((l) => (
              <button
                key={l.value}
                onClick={() => setLang(l.value as any)}
                className={`flex items-center gap-2 rounded-lg border p-3 text-sm transition-colors ${
                  lang === l.value
                    ? "border-primary bg-primary/10 text-primary"
                    : "border-border bg-secondary/50 text-foreground hover:bg-secondary"
                }`}
              >
                {l.label}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Password change modal */}
      {showPasswordModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={() => setShowPasswordModal(false)}>
          <div className="w-full max-w-md rounded-xl border border-border bg-card p-6 space-y-4" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center gap-2">
              <KeyRound className="h-5 w-5 text-primary" />
              <h3 className="font-semibold text-foreground">{t("settings.changePassword")}</h3>
            </div>
            <div>
              <label className="text-sm text-muted-foreground">{t("settings.newPassword")}</label>
              <Input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="••••••••"
                className="mt-1"
              />
              <p className="text-xs text-muted-foreground mt-1">{t("settings.minChars")}</p>
            </div>
            <div className="flex gap-3">
              <Button variant="outline" className="flex-1" onClick={() => { setShowPasswordModal(false); setNewPassword(""); }}>
                {t("settings.cancel")}
              </Button>
              <Button className="flex-1" onClick={handleChangePassword} disabled={changingPassword || newPassword.length < 6}>
                {changingPassword ? "..." : t("settings.confirm")}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
