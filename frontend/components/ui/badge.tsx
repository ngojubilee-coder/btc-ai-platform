import { cn } from "@/lib/utils";
import { HTMLAttributes } from "react";

type BadgeVariant = "default" | "secondary" | "outline" | "success" | "warning" | "destructive";

const variants: Record<BadgeVariant, string> = {
  default: "bg-primary/20 text-primary border-primary/30",
  secondary: "bg-secondary text-secondary-foreground border-border",
  outline: "border-border text-foreground",
  success: "bg-green-500/20 text-green-400 border-green-500/30",
  warning: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
  destructive: "bg-red-500/20 text-red-400 border-red-500/30",
};

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
}

export function Badge({ className, variant = "default", ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium",
        variants[variant],
        className
      )}
      {...props}
    />
  );
}
