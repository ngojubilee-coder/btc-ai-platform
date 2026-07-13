"use client";

import { useState, useRef, useEffect } from "react";
import { streamChat, apiFetch, apiPost } from "@/lib/api";
import { Send, Loader2, Bot, User, Sparkles, Copy, Check, Plus, MessageSquare, Trash2, Zap, Download, Eraser, ArrowDown } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useToast } from "@/components/ui/toast";
import { useAuth } from "@/components/auth-provider";
import { useI18n } from "@/lib/i18n";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface Conversation {
  id: string;
  title: string;
  created_at: string;
}

const SUGGESTIONS_FR = [
  "Quelles sont les statistiques du dataset ?",
  "Quelles features ont le plus de corrélation avec target_return_15m ?",
  "Pourquoi le BTC a chuté en mars 2024 ?",
  "Génère un schéma des colonnes du dataset",
  "Quelle est la couverture temporelle des données ?",
];

const SUGGESTIONS_EN = [
  "What are the dataset statistics?",
  "Which features have the highest correlation with target_return_15m?",
  "Why did BTC drop in March 2024?",
  "Generate a schema of the dataset columns",
  "What is the temporal coverage of the data?",
];

export default function ChatPage() {
  const { toast } = useToast();
  const { user } = useAuth();
  const { t, lang } = useI18n();
  const userId = user?.id || "anonymous";
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [streamContent, setStreamContent] = useState("");
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConv, setActiveConv] = useState<string | null>(null);
  const [complexity, setComplexity] = useState("simple");
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null);
  const abortRef = useRef<(() => void) | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const [showScrollBtn, setShowScrollBtn] = useState(false);

  useEffect(() => {
    loadConversations();
    try {
      const stored = localStorage.getItem("btc-ai-prefs");
      if (stored) {
        const p = JSON.parse(stored);
        if (p.prefs?.complexity) setComplexity(p.prefs.complexity);
      }
    } catch {}
  }, []);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    const isNearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 100;
    if (isNearBottom) {
      el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
    }
  }, [messages, streamContent]);

  function handleScroll() {
    const el = scrollRef.current;
    if (!el) return;
    const isNearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 100;
    setShowScrollBtn(!isNearBottom && messages.length > 0);
  }

  function scrollToBottom() {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }

  async function loadConversations() {
    try {
      const data = await apiFetch<Conversation[]>(`/api/chat/conversations/${userId}`);
      setConversations(data || []);
    } catch {}
  }

  async function loadConversation(id: string) {
    try {
      const msgs = await apiFetch<Message[]>(`/api/chat/messages/${id}`);
      setMessages(msgs || []);
      setActiveConv(id);
    } catch {
      toast(t("chat.errorLoad"), "error");
    }
  }

  async function newConversation() {
    try {
      const conv = await apiPost<Conversation>("/api/chat/conversations", {
        title: t("chat.newConversation"),
        asset: "BTC",
        user_id: userId,
      });
      setMessages([]);
      setActiveConv(conv.id);
      setConversations((prev) => [conv, ...prev]);
    } catch {
      toast(t("chat.errorCreate"), "error");
    }
  }

  function copyMessage(idx: number, content: string) {
    navigator.clipboard.writeText(content);
    setCopiedIdx(idx);
    toast(t("chat.copied"), "success");
    setTimeout(() => setCopiedIdx(null), 2000);
  }

  async function handleSend(text?: string) {
    const msg = text || input.trim();
    if (!msg || streaming) return;

    setMessages((prev) => [...prev, { role: "user", content: msg }]);
    setInput("");
    setStreaming(true);
    setStreamContent("");

    abortRef.current = await streamChat(
      { message: msg, conversation_id: activeConv || undefined, user_id: userId, complexity, lang },
      (token) => {
        setStreamContent((prev) => prev + token);
      },
      (full, convId) => {
        setMessages((prev) => [...prev, { role: "assistant", content: full }]);
        setStreamContent("");
        setStreaming(false);
        if (convId && !activeConv) {
          setActiveConv(convId);
        }
        loadConversations();
      },
      (err) => {
        setMessages((prev) => [...prev, { role: "assistant", content: `${t("common.error")}: ${err}` }]);
        setStreamContent("");
        setStreaming(false);
        toast(err, "error");
      }
    );
  }

  function handleStop() {
    abortRef.current?.();
    setStreaming(false);
    setStreamContent("");
  }

  function handleClear() {
    setMessages([]);
    setStreamContent("");
    setActiveConv(null);
    toast(t("chat.conversationCleared"), "info");
  }

  function handleExport() {
    if (messages.length === 0) {
      toast(t("chat.noMessagesExport"), "warning");
      return;
    }
    const text = messages
      .map((m) => `## ${m.role === "user" ? t("chat.question") : t("chat.aiResponse")}\n\n${m.content}`)
      .join("\n\n---\n\n");
    const blob = new Blob([`# ${t("chat.exportTitle")}\n\n${text}`], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `conversation-${new Date().toISOString().slice(0, 10)}.md`;
    a.click();
    URL.revokeObjectURL(url);
    toast(t("chat.exported"), "success");
  }

  return (
    <div className="flex h-[calc(100vh-3.5rem)] lg:h-screen gap-4 -m-4 lg:-m-8">
      {/* Conversations sidebar */}
      <div className="w-64 flex-shrink-0 flex flex-col border-r border-border pr-4">
        <Button onClick={newConversation} variant="default" size="sm" className="mb-3">
          <Plus className="h-4 w-4 mr-1" />
          {t("chat.newConversation")}
        </Button>
        <div className="flex-1 overflow-y-auto space-y-1">
          {conversations.length === 0 ? (
            <p className="text-xs text-muted-foreground text-center py-4">{t("chat.noConversation")}</p>
          ) : (
            conversations.map((conv) => (
              <div
                key={conv.id}
                className={`group w-full text-left flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition-colors ${
                  activeConv === conv.id
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:bg-secondary hover:text-foreground"
                }`}
              >
                <MessageSquare className="h-3.5 w-3.5 flex-shrink-0" />
                <button
                  onClick={() => loadConversation(conv.id)}
                  className="flex-1 truncate text-left"
                >
                  {conv.title}
                </button>
                <button
                  onClick={async (e) => {
                    e.stopPropagation();
                    try {
                      await apiFetch(`/api/chat/conversations/${conv.id}`, { method: "DELETE" });
                      setConversations((prev) => prev.filter((c) => c.id !== conv.id));
                      if (activeConv === conv.id) {
                        setMessages([]);
                        setActiveConv(null);
                      }
                      toast(t("chat.conversationCleared"), "info");
                    } catch {
                      toast(t("chat.errorDelete"), "error");
                    }
                  }}
                  className="opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-destructive transition-opacity flex-shrink-0"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Chat area */}
      <div className="flex-1 flex flex-col min-w-0">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
            <Sparkles className="h-6 w-6 text-primary" />
            {t("chat.title")}
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            {t("chat.subtitle")}{messages.length > 0 && ` · ${messages.length} ${t("chat.messages")}`}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={complexity === "complex" ? "warning" : "secondary"} className="flex items-center gap-1">
            <Zap className="h-3 w-3" />
            {complexity === "complex" ? t("chat.deep") : t("chat.quick")}
          </Badge>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setComplexity((c) => (c === "simple" ? "complex" : "simple"))}
          >
            {t("chat.toggle")}
          </Button>
          <Button variant="ghost" size="icon" onClick={handleExport} title={t("chat.export")}>
            <Download className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" onClick={handleClear} title={t("chat.clear")}>
            <Eraser className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <div ref={scrollRef} onScroll={handleScroll} className="flex-1 overflow-y-auto space-y-4 pb-4 relative">
        {messages.length === 0 && !streaming && (
          <div className="flex flex-col items-center justify-center h-full space-y-6">
            <div className="text-center">
              <Bot className="mx-auto h-12 w-12 text-primary mb-3" />
              <p className="text-lg font-medium text-foreground">{t("chat.firstQuestion")}</p>
              <p className="text-sm text-muted-foreground mt-1">{t("chat.aiHasAccess")}</p>
            </div>
            <div className="grid grid-cols-1 gap-2 max-w-2xl w-full">
              {(lang === "fr" ? SUGGESTIONS_FR : SUGGESTIONS_EN).map((s) => (
                <button
                  key={s}
                  onClick={() => handleSend(s)}
                  className="text-left rounded-lg border border-border bg-card p-3 text-sm text-foreground hover:bg-secondary transition-colors"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            {msg.role === "assistant" && (
              <div className="flex-shrink-0 mt-1">
                <Bot className="h-7 w-7 text-primary" />
              </div>
            )}
            <div
              className={`max-w-[80%] rounded-xl p-4 group ${
                msg.role === "user"
                  ? "bg-primary text-primary-foreground"
                  : "bg-card border border-border"
              }`}
            >
              {msg.role === "assistant" ? (
                <>
                  <div className="prose prose-sm prose-invert max-w-none">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {msg.content}
                    </ReactMarkdown>
                  </div>
                  <button
                    onClick={() => copyMessage(i, msg.content)}
                    className="mt-2 flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    {copiedIdx === i ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
                    {copiedIdx === i ? t("chat.copied") : t("chat.copy")}
                  </button>
                </>
              ) : (
                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
              )}
            </div>
            {msg.role === "user" && (
              <div className="flex-shrink-0 mt-1">
                <User className="h-7 w-7 text-muted-foreground" />
              </div>
            )}
          </div>
        ))}

        {streaming && (
          <div className="flex gap-3 justify-start">
            <div className="flex-shrink-0 mt-1">
              <Bot className="h-7 w-7 text-primary" />
            </div>
            <div className="max-w-[80%] rounded-xl p-4 bg-card border border-border">
              {streamContent ? (
                <div className="prose prose-sm prose-invert max-w-none">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {streamContent}
                  </ReactMarkdown>
                </div>
              ) : (
                <div className="flex items-center gap-1.5 py-1">
                  <span className="h-2 w-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: "0ms" }} />
                  <span className="h-2 w-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: "150ms" }} />
                  <span className="h-2 w-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: "300ms" }} />
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {showScrollBtn && (
        <button
          onClick={scrollToBottom}
          className="absolute right-4 bottom-20 z-10 flex h-9 w-9 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-lg hover:bg-primary/90 transition-colors animate-fade-in"
        >
          <ArrowDown className="h-4 w-4" />
        </button>
      )}

      <div className="border-t border-border pt-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder={t("chat.placeholder")}
            className="flex-1 rounded-lg border border-input bg-background px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none"
            disabled={streaming}
          />
          {streaming ? (
            <Button onClick={handleStop} variant="destructive">
              {t("chat.stop")}
            </Button>
          ) : (
            <Button onClick={() => handleSend()} disabled={!input.trim()} size="md">
              <Send className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
      </div>
    </div>
  );
}
