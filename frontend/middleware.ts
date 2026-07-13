import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  // Auth is handled client-side via Supabase (localStorage, not cookies)
  // Middleware cannot access localStorage, so we allow all routes through
  // The AuthProvider handles redirects to /login when no session is found
  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
