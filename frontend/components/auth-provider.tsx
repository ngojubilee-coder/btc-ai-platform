"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { Session, User } from "@supabase/supabase-js";
import { supabase } from "@/lib/supabase";

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL || "";
const SUPABASE_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";
const isLocalMode = !SUPABASE_URL || !SUPABASE_KEY || SUPABASE_URL.includes("placeholder");

const LOCAL_USER: User = {
  id: "local-user-001",
  aud: "authenticated",
  role: "authenticated",
  email: "admin@btc-ai.local",
  app_metadata: { provider: "local" },
  user_metadata: { full_name: "Admin Local" },
  identities: [],
  created_at: new Date().toISOString(),
} as unknown as User;

const LOCAL_EMAIL = "admin@btc-ai.local";
const LOCAL_PASSWORD = "btc2025";

interface AuthContextType {
  user: User | null;
  session: Session | null;
  loading: boolean;
  signOut: () => Promise<void>;
  isLocalMode: boolean;
  setLocalUser: (user: User | null) => void;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  session: null,
  loading: true,
  signOut: async () => {},
  isLocalMode: false,
  setLocalUser: () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isLocalMode) {
      try {
        const stored = localStorage.getItem("btc-ai-local-auth");
        if (stored === "true") setUser(LOCAL_USER);
      } catch {}
      setLoading(false);
      return;
    }

    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setUser(session?.user ?? null);
      setLoading(false);
    }).catch(() => {
      setLoading(false);
    });

    const { data: listener } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
      setUser(session?.user ?? null);
      setLoading(false);
    });

    return () => listener.subscription.unsubscribe();
  }, []);

  const signOut = async () => {
    if (isLocalMode) {
      localStorage.removeItem("btc-ai-local-auth");
      setUser(null);
      return;
    }
    await supabase.auth.signOut();
    setUser(null);
    setSession(null);
  };

  const setLocalUser = (u: User | null) => {
    setUser(u);
  };

  return (
    <AuthContext.Provider value={{ user, session, loading, signOut, isLocalMode, setLocalUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}

export { isLocalMode, LOCAL_EMAIL, LOCAL_PASSWORD, LOCAL_USER };
