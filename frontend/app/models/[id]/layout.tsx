import { ProtectedLayout } from "@/components/protected-layout";

export default function ModelDetailLayout({ children }: { children: React.ReactNode }) {
  return <ProtectedLayout>{children}</ProtectedLayout>;
}
