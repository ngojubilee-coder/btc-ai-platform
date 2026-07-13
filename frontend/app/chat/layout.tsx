import { ProtectedLayout } from "@/components/protected-layout";

export default function ChatLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <ProtectedLayout fullHeight>{children}</ProtectedLayout>;
}
