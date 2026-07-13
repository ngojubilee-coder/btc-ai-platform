import { ProtectedLayout } from "@/components/protected-layout";

export default function ModelsLayout({ children }: { children: React.ReactNode }) {
  return <ProtectedLayout>{children}</ProtectedLayout>;
}
