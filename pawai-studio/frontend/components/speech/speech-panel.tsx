"use client"

import { Mic } from "lucide-react"
import { PanelCard } from "@/components/shared/panel-card"
import type { SpeechState, SpeechIntentEvent } from "@/contracts/types"

interface SpeechPanelProps {
  data: SpeechState
  events: SpeechIntentEvent[]
}

export function SpeechPanel({ data, events }: SpeechPanelProps) {
  return (
    <PanelCard
      title="語音互動"
      icon={<Mic className="h-4 w-4" />}
      status={data.phase !== "idle_wakeword" ? "active" : "inactive"}
    >
      <div className="flex items-center justify-center h-32 text-[#55556A] text-sm">
        <p>TODO: 負責實作（見 speech-panel-spec.md）</p>
      </div>
    </PanelCard>
  )
}
