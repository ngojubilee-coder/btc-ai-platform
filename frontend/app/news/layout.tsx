import { ProtectedLayout } from "@/components/protected-layout";

export default function NewsLayout({ children }: { children: React.ReactNode }) {
  return <ProtectedLayout>{children}</ProtectedLayout>;
}
