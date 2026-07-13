"use client";

import Link from "next/link";
import { Bitcoin, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useI18n } from "@/lib/i18n";

export default function NotFound() {
  const { t } = useI18n();
  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-background via-background to-primary/5 p-4">
      <div className="text-center space-y-6">
        <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-primary/10 ring-4 ring-primary/5">
          <Bitcoin className="h-10 w-10 text-primary" />
        </div>
        <div>
          <h1 className="text-6xl font-bold text-foreground">404</h1>
          <p className="text-lg text-muted-foreground mt-2">{t("common.notFound")}</p>
          <p className="text-sm text-muted-foreground mt-1">
            {t("common.notFoundDesc")}
          </p>
        </div>
        <Link href="/dashboard">
          <Button variant="default" size="md">
            <ArrowLeft className="h-4 w-4 mr-1" />
            {t("common.backToDashboard")}
          </Button>
        </Link>
      </div>
    </div>
  );
}
