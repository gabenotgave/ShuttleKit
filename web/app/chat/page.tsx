"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import { Navbar } from "@/components/navbar"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Spinner } from "@/components/ui/spinner"
import {
  CHAT_SESSION_STORAGE_KEY,
  getChatHistory,
  getChatModelDisplay,
  getConfig,
  getStatus,
  postChat,
  type AppConfig,
  type ChatHistoryApiMessage,
  type ShuttleStatus,
} from "@/lib/shuttle-api"
import { cn } from "@/lib/utils"
import { AlertCircle, Bot, SendHorizontal, Sparkles, User } from "lucide-react"
import ReactMarkdown from "react-markdown"

type ChatRole = "user" | "assistant"

interface ChatMessage {
  id: string
  role: ChatRole
  content: string
}

function newId() {
  return crypto.randomUUID()
}

/** Map GET /api/chat/history rows to UI bubbles (tool/system rows are omitted; matches pre-refresh chat view). */
function historyToChatMessages(rows: ChatHistoryApiMessage[]): ChatMessage[] {
  const out: ChatMessage[] = []
  for (const row of rows) {
    if (row.role === "user") {
      const content = typeof row.content === "string" ? row.content : ""
      out.push({ id: newId(), role: "user", content })
      continue
    }
    if (row.role === "assistant") {
      const content = typeof row.content === "string" ? row.content : ""
      if (!content.trim()) {
        continue
      }
      out.push({ id: newId(), role: "assistant", content })
    }
  }
  return out
}

export default function ChatPage() {
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [modelDisplay, setModelDisplay] = useState<string | null>(null)
  const [modelLoadFailed, setModelLoadFailed] = useState(false)
  const [status, setStatus] = useState<ShuttleStatus | null>(null)
  const [appConfig, setAppConfig] = useState<AppConfig | null>(null)
  const [historyLoading, setHistoryLoading] = useState(false)
  const [historyError, setHistoryError] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  const focusChatInput = useCallback(() => {
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        inputRef.current?.focus()
      })
    })
  }, [])

  useEffect(() => {
    getStatus().then(setStatus)
    getConfig().then((config) => {
      setAppConfig(config)
      if (config?.campus) {
        document.title = `${config.campus} ShuttleKit · Assistant`
      }
    })
  }, [])

  useEffect(() => {
    if (typeof window === "undefined") return
    let id = localStorage.getItem(CHAT_SESSION_STORAGE_KEY)
    if (!id) {
      id = crypto.randomUUID()
      localStorage.setItem(CHAT_SESSION_STORAGE_KEY, id)
    }
    setSessionId(id)
  }, [])

  useEffect(() => {
    if (!sessionId) return

    let cancelled = false
    setHistoryLoading(true)
    setHistoryError(null)

    getChatHistory(sessionId).then((result) => {
      if (cancelled) return
      if (!result.ok) {
        setHistoryError(result.error)
        setMessages([])
      } else {
        setMessages(historyToChatMessages(result.data.messages))
      }
      setHistoryLoading(false)
    })

    return () => {
      cancelled = true
    }
  }, [sessionId])

  useEffect(() => {
    getChatModelDisplay().then((label) => {
      if (label) {
        setModelDisplay(label)
        setModelLoadFailed(false)
      } else {
        setModelLoadFailed(true)
      }
    })
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, loading])

  const handleNewChat = useCallback(() => {
    const id = crypto.randomUUID()
    localStorage.setItem(CHAT_SESSION_STORAGE_KEY, id)
    setSessionId(id)
    setMessages([])
    setError(null)
    setHistoryError(null)
    setInput("")
    focusChatInput()
  }, [focusChatInput])

  const sendMessage = async () => {
    const text = input.trim()
    if (!text || !sessionId || loading) return

    setInput("")
    setError(null)
    const userMsg: ChatMessage = { id: newId(), role: "user", content: text }
    setMessages((prev) => [...prev, userMsg])
    setLoading(true)

    try {
      const result = await postChat(sessionId, text)
      if (!result.ok) {
        setError(result.error)
        return
      }

      setModelDisplay(result.data.model_display)
      setModelLoadFailed(false)
      setMessages((prev) => [
        ...prev,
        { id: newId(), role: "assistant", content: result.data.reply },
      ])
    } finally {
      setLoading(false)
      focusChatInput()
    }
  }

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      void sendMessage()
    }
  }

  const canSend = Boolean(sessionId && input.trim() && !loading && !historyLoading)

  return (
    <main className="min-h-screen flex flex-col bg-background">
      <Navbar schoolName={appConfig?.campus ?? ""} status={status} />

      <div className="flex flex-1 flex-col min-h-0 pt-[calc(3.5rem+var(--sk-disruption-banner,0px))] pb-[calc(3.5rem+max(0.35rem,env(safe-area-inset-bottom)))]">
        <div className="mx-auto flex w-full max-w-2xl flex-1 flex-col min-h-0 px-4">
          <div className="flex shrink-0 items-start justify-between gap-3 py-4">
            <div className="flex items-center gap-3 min-w-0">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <Sparkles className="h-5 w-5" aria-hidden />
              </div>
              <div className="min-w-0">
                <h1 className="text-xl font-semibold text-foreground tracking-tight">Assistant</h1>
                <p className="text-sm text-muted-foreground">
                  Ask about routes, schedules, live status, and trip planning.
                </p>
              </div>
            </div>
            <Button type="button" variant="outline" size="sm" className="shrink-0" onClick={handleNewChat}>
              New chat
            </Button>
          </div>

          {error && (
            <Alert variant="destructive" className="mb-3 shrink-0">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {historyError && (
            <Alert variant="destructive" className="mb-3 shrink-0">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Could not load this conversation: {historyError}
              </AlertDescription>
            </Alert>
          )}

          <div className="flex flex-1 flex-col min-h-0 rounded-xl border border-border bg-card/50">
            <div className="flex-1 overflow-y-auto px-3 py-4 sm:px-4">
              {historyLoading && messages.length === 0 && (
                <div className="flex items-center justify-center gap-2 py-16 text-muted-foreground">
                  <Spinner className="h-5 w-5" />
                  <span className="text-sm">Loading conversation…</span>
                </div>
              )}

              {messages.length === 0 && !loading && !historyLoading && (
                <div className="flex flex-col items-center justify-center gap-2 py-12 text-center text-sm text-muted-foreground">
                  <Bot className="h-10 w-10 opacity-40" aria-hidden />
                  <p className="max-w-sm">
                    Start a conversation. The assistant uses live shuttle data through tools when
                    answering.
                  </p>
                </div>
              )}

              <ul className="space-y-4">
                {messages.map((m) => (
                  <li
                    key={m.id}
                    className={cn(
                      "flex gap-3",
                      m.role === "user" ? "flex-row-reverse" : "flex-row",
                    )}
                  >
                    <div
                      className={cn(
                        "flex h-8 w-8 shrink-0 items-center justify-center rounded-lg",
                        m.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted text-foreground",
                      )}
                      aria-hidden
                    >
                      {m.role === "user" ? (
                        <User className="h-4 w-4" />
                      ) : (
                        <Bot className="h-4 w-4" />
                      )}
                    </div>
                    <div
                      className={cn(
                        "max-w-[min(100%,28rem)] rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-sm",
                        m.role === "user"
                          ? "bg-primary text-primary-foreground"
                          : "bg-muted/90 text-foreground border border-border/60",
                      )}
                    >
                      {m.role === "user" ? (
                        <p className="whitespace-pre-wrap break-words">{m.content}</p>
                      ) : (
                        <div
                          className={cn(
                            "break-words text-sm leading-relaxed",
                            "[&_p]:mb-2 [&_p:last-child]:mb-0",
                            "[&_strong]:font-semibold [&_em]:italic",
                            "[&_ul]:my-2 [&_ul]:list-disc [&_ul]:pl-4",
                            "[&_ol]:my-2 [&_ol]:list-decimal [&_ol]:pl-4",
                            "[&_a]:underline [&_a]:text-primary",
                            "[&_code]:rounded [&_code]:bg-background/80 [&_code]:px-1 [&_code]:py-0.5 [&_code]:font-mono [&_code]:text-[0.85em]",
                          )}
                        >
                          <ReactMarkdown>{m.content}</ReactMarkdown>
                        </div>
                      )}
                    </div>
                  </li>
                ))}
              </ul>

              {loading && (
                <div className="mt-4 flex gap-3">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted text-foreground">
                    <Bot className="h-4 w-4" aria-hidden />
                  </div>
                  <div className="flex items-center gap-2 rounded-2xl border border-border/60 bg-muted/90 px-4 py-3 text-sm text-muted-foreground">
                    <Spinner className="h-4 w-4" />
                    <span>Thinking…</span>
                  </div>
                </div>
              )}

              <div ref={bottomRef} />
            </div>

            <div className="shrink-0 border-t border-border bg-background/80 px-3 py-3 sm:px-4">
              <p className="mb-3 text-xs leading-relaxed text-muted-foreground">
                <span className="font-medium text-foreground/90">Disclaimer: </span>
                AI answers can be wrong or incomplete. Do not rely on them for safety-critical
                decisions.{" "}
                {modelDisplay ? (
                  <>
                    Model in use: <span className="font-mono text-[0.8rem] text-foreground/80">{modelDisplay}</span>.
                  </>
                ) : modelLoadFailed ? (
                  <>
                    Model name will appear after the API responds, or when{" "}
                    <code className="rounded bg-muted px-1 py-0.5 font-mono text-[0.7rem]">GET /api/chat/model</code>{" "}
                    is reachable.
                  </>
                ) : (
                  <>Loading model info…</>
                )}
              </p>
              <div className="flex gap-2">
                <Textarea
                  ref={inputRef}
                  id="chat-input"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={onKeyDown}
                  placeholder={
                    !sessionId
                      ? "Preparing session…"
                      : historyLoading
                        ? "Loading conversation…"
                        : "Message the assistant…"
                  }
                  disabled={!sessionId || loading || historyLoading}
                  rows={2}
                  className="min-h-[2.75rem] resize-none bg-background"
                  aria-label="Message"
                />
                <Button
                  type="button"
                  size="icon"
                  className="h-11 w-11 shrink-0 self-end"
                  disabled={!canSend}
                  onClick={() => void sendMessage()}
                  aria-label="Send message"
                >
                  {loading ? <Spinner className="h-5 w-5" /> : <SendHorizontal className="h-5 w-5" />}
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}
