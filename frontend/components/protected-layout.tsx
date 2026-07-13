"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/auth-provider";
import { Sidebar } from "@/components/sidebar";
import { Loader2 } from "lucide-react";

interface ProtectedLayoutProps {
  children: React.ReactNode;
  fullHeight?: boolean;
}

export function ProtectedLayout({ children, fullHeight }: ProtectedLayoutProps) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/login");
    }
  }, [user, loading, router]);

  if (loading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <main className="ml-60 min-h-screen pt-14 lg:pt-0">
        <div className={`p-4 lg:p-8 ${fullHeight ? "h-[calc(100vh-3.5rem)] lg:h-screen flex flex-col" : ""}`}>
          {children}
        </div>
      </main>
    </div>
  );
}
