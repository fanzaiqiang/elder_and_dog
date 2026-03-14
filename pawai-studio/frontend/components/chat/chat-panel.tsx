"use client"

import { useState, useRef, useEffect } from "react"
import { Send } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { EventItem } from "@/components/shared/event-item"
import { cn } from "@/lib/utils"
import type { PawAIEvent } from "@/contracts/types"

interface UserMessage {
  id: string
  type: "user"
  text: string
  timestamp: string
}

interface AIMessage {
  id: string
  type: "ai"
  text: string
  timestamp: string
}

interface EventMessage {
  id: string
  type: "event"
  event: PawAIEvent
}

type ChatMessage = UserMessage | AIMessage | EventMessage

function formatTime(date: Date): string {
  return date.toLocaleTimeString("zh-TW", { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false })
}

interface ChatPanelProps {
  events?: PawAIEvent[]
}

export function ChatPanel({ events = [] }: ChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      type: "ai",
      text: "你好！我是 PawAI，有什麼我可以幫你的嗎？",
      timestamp: formatTime(new Date()),
    },
  ])
  const [inputText, setInputText] = useState("")
  const [isThinking, setIsThinking] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const prevEventsLenRef = useRef(0)

  // Auto-scroll on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, isThinking])

  // Inject incoming events as inline event cards
  useEffect(() => {
    if (events.length > prevEventsLenRef.current) {
      const newEvents = events.slice(prevEventsLenRef.current)
      prevEventsLenRef.current = events.length
      setMessages((prev) => [
        ...prev,
        ...newEvents.map((e) => ({
          id: `event-${e.id}`,
          type: "event" as const,
          event: e,
        })),
      ])
    }
  }, [events])

  async function handleSend() {
    const text = inputText.trim()
    if (!text || isThinking) return

    const userMsg: UserMessage = {
      id: `user-${Date.now()}`,
      type: "user",
      text,
      timestamp: formatTime(new Date()),
    }
    setMessages((prev) => [...prev, userMsg])
    setInputText("")
    setIsThinking(true)

    try {
      const gatewayUrl = process.env.NEXT_PUBLIC_GATEWAY_URL ?? "http://localhost:8000"
      const res = await fetch(`${gatewayUrl}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          command_type: "chat",
          text,
          session_id: "studio-session",
        }),
      })
      const json = await res.json()
      const aiMsg: AIMessage = {
        id: `ai-${Date.now()}`,
        type: "ai",
        text: json.reply ?? "（無回應）",
        timestamp: formatTime(new Date()),
      }
      setMessages((prev) => [...prev, aiMsg])
    } catch {
      const errMsg: AIMessage = {
        id: `ai-err-${Date.now()}`,
        type: "ai",
        text: "連線失敗，請確認 Gateway 是否啟動。",
        timestamp: formatTime(new Date()),
      }
      setMessages((prev) => [...prev, errMsg])
    } finally {
      setIsThinking(false)
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex flex-col h-full bg-[#0E0E13]">
      {/* Message list */}
      <ScrollArea className="flex-1 px-4 py-4">
        <div className="flex flex-col gap-3">
          {messages.map((msg) => {
            if (msg.type === "user") {
              return (
                <div key={msg.id} className="flex justify-end">
                  <div className="max-w-[75%] flex flex-col items-end gap-1">
                    <div className="bg-[#7C6BFF]/10 rounded-lg p-3 text-sm text-[#F0F0F5] border border-[#7C6BFF]/20">
                      {msg.text}
                    </div>
                    <span className="text-[10px] text-[#55556A]">{msg.timestamp}</span>
                  </div>
                </div>
              )
            }

            if (msg.type === "ai") {
              return (
                <div key={msg.id} className="flex justify-start">
                  <div className="max-w-[75%] flex flex-col gap-1">
                    <div className="bg-[#141419] rounded-lg p-3 text-sm text-[#F0F0F5] border-l-2 border-[#7C6BFF]">
                      {msg.text}
                    </div>
                    <span className="text-[10px] text-[#55556A]">{msg.timestamp}</span>
                  </div>
                </div>
              )
            }

            // event card
            const e = msg.event
            const summary = typeof e.data === "object" && e.data !== null
              ? Object.entries(e.data).map(([k, v]) => `${k}=${v}`).join(" ")
              : ""
            return (
              <div key={msg.id} className="rounded-lg border border-[#2A2A35] overflow-hidden">
                <EventItem
                  timestamp={new Date(e.timestamp).toLocaleTimeString("zh-TW", { hour12: false })}
                  eventType={e.event_type}
                  source={e.source}
                  summary={summary}
                />
              </div>
            )
          })}

          {/* Thinking indicator */}
          {isThinking && (
            <div className="flex justify-start">
              <div className="bg-[#141419] rounded-lg px-4 py-3 border-l-2 border-[#7C6BFF]">
                <span className="text-[#7C6BFF] text-sm tracking-widest animate-pulse">● ● ●</span>
              </div>
            </div>
          )}
        </div>
        <div ref={bottomRef} />
      </ScrollArea>

      {/* Input bar */}
      <div className="flex items-center gap-2 p-3 bg-[#141419] border-t border-[#2A2A35] shrink-0">
        <Input
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="輸入訊息…"
          disabled={isThinking}
          className={cn(
            "flex-1 bg-[#1C1C24] border-[#2A2A35] text-[#F0F0F5] placeholder:text-[#55556A]",
            "focus-visible:ring-[#7C6BFF] focus-visible:border-[#7C6BFF]"
          )}
        />
        <Button
          onClick={handleSend}
          disabled={isThinking || !inputText.trim()}
          size="icon"
          className="bg-[#7C6BFF] hover:bg-[#6A5AE8] text-white shrink-0"
        >
          <Send className="h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}
