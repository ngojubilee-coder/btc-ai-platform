"use client";

import { createClient, SupabaseClient } from "@supabase/supabase-js";

let _client: SupabaseClient | null = null;

function getSupabaseUrl(): string {
  return process.env.NEXT_PUBLIC_SUPABASE_URL || "https://placeholder.supabase.co";
}

function getSupabaseKey(): string {
  return process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "placeholder-anon-key";
}

export const supabase = createClient(getSupabaseUrl(), getSupabaseKey());
