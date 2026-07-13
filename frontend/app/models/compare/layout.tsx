import { ProtectedLayout } from "@/components/protected-layout";

export default function CompareLayout({ children }: { children: React.ReactNode }) {
  return <ProtectedLayout>{children}</ProtectedLayout>;
}
