"use client";

import { Component, ReactNode } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

const errorMessages = {
  fr: { title: "Une erreur est survenue", fallback: "Erreur inattendue", reload: "Recharger" },
  en: { title: "An error occurred", fallback: "Unexpected error", reload: "Reload" },
};

function getLang(): "fr" | "en" {
  try {
    const stored = localStorage.getItem("btc-ai-prefs");
    if (stored) {
      const p = JSON.parse(stored);
      if (p.lang === "en") return "en";
    }
  } catch {}
  return "fr";
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<{ children: ReactNode }, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-[400px] items-center justify-center p-8">
          <div className="max-w-md text-center space-y-4">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-destructive/10">
              <AlertTriangle className="h-8 w-8 text-destructive" />
            </div>
            <h2 className="text-xl font-bold text-foreground">{errorMessages[getLang()].title}</h2>
            <p className="text-sm text-muted-foreground">
              {this.state.error?.message || errorMessages[getLang()].fallback}
            </p>
            <button
              onClick={() => window.location.reload()}
              className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
            >
              <RefreshCw className="h-4 w-4" />
              {errorMessages[getLang()].reload}
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
