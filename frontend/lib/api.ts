const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const DEFAULT_TIMEOUT = 30000;

async function getAuthHeaders(): Promise<Record<string, string>> {
  if (typeof window === "undefined") return {};
  try {
    const { supabase } = await import("@/lib/supabase");
    const { data } = await supabase.auth.getSession();
    if (data.session?.access_token) {
      return { Authorization: `Bearer ${data.session.access_token}` };
    }
  } catch {}
  return {};
}

export async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const authHeaders = await getAuthHeaders();
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT);
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, {
      ...options,
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        ...authHeaders,
        ...options?.headers,
      },
    });
  } catch (err: any) {
    if (err.name === "AbortError") throw new Error("Request timeout");
    throw new Error(`Network error: ${err.message || "Unable to reach server"}`);
  } finally {
    clearTimeout(timeoutId);
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.error || body.detail || detail;
    } catch {}
    throw new Error(`API error: ${res.status} ${detail}`);
  }
  const text = await res.text();
  if (!text) return {} as T;
  try {
    return JSON.parse(text) as T;
  } catch {
    return text as unknown as T;
  }
}

export async function apiPost<T>(path: string, body: any): Promise<T> {
  return apiFetch<T>(path, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function apiFetchText(path: string): Promise<string> {
  const authHeaders = await getAuthHeaders();
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT);
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, {
      signal: controller.signal,
      headers: { ...authHeaders },
    });
  } catch (err: any) {
    if (err.name === "AbortError") throw new Error("Request timeout");
    throw new Error(`Network error: ${err.message || "Unable to reach server"}`);
  } finally {
    clearTimeout(timeoutId);
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.error || body.detail || detail;
    } catch {}
    throw new Error(`API error: ${res.status} ${detail}`);
  }
  return res.text();
}

export async function streamChat(
  body: { message: string; conversation_id?: string; user_id: string; complexity?: string; lang?: string },
  onToken: (token: string) => void,
  onDone: (full: string, conversationId?: string) => void,
  onError: (err: string) => void
) {
  const controller = new AbortController();
  const authHeaders = await getAuthHeaders();

  fetch(`${API_URL}/api/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders },
    body: JSON.stringify(body),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        let detail = response.statusText;
        try {
          const errBody = await response.json();
          detail = errBody.error || errBody.detail || detail;
        } catch {}
        onError(`API error: ${response.status} ${detail}`);
        return;
      }
      const reader = response.body?.getReader();
      if (!reader) return;
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.type === "token") onToken(data.content);
              else if (data.type === "done") onDone(data.content, data.conversation_id);
              else if (data.type === "error") onError(data.content);
            } catch {}
          }
        }
      }
    })
    .catch((err) => {
      if (err.name !== "AbortError") onError(err.message);
    });

  return () => controller.abort();
}
