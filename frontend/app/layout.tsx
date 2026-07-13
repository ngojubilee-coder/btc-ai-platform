import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/components/auth-provider";
import { ToastProvider } from "@/components/ui/toast";
import { ErrorBoundary } from "@/components/ui/error-boundary";
import { LoadingBar } from "@/components/loading-bar";
import { LanguageProvider } from "@/lib/i18n";
import { DeployPopup } from "@/components/deploy-popup";

export const metadata: Metadata = {
  title: "BTC AI Platform",
  description: "AI Quantitative Analyst for Bitcoin",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: `
          (function() {
            try {
              var stored = localStorage.getItem('btc-ai-prefs');
              var theme = stored ? JSON.parse(stored).theme : 'dark';
              if (!theme || theme === 'system') {
                theme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
              }
              if (theme === 'dark') document.documentElement.classList.add('dark');
            } catch(e) {
              document.documentElement.classList.add('dark');
            }
          })();
        `}} />
      </head>
      <body className="min-h-screen bg-background antialiased">
        <ErrorBoundary>
          <LanguageProvider>
            <AuthProvider>
              <ToastProvider>
                <LoadingBar />
                {children}
                <DeployPopup />
              </ToastProvider>
            </AuthProvider>
          </LanguageProvider>
        </ErrorBoundary>
      </body>
    </html>
  );
}
