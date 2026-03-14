"use client"

import { Hand } from "lucide-react"
import { PanelCard } from "@/components/shared/panel-card"
import type { GestureState, GestureEvent } from "@/contracts/types"

interface GesturePanelProps {
  data: GestureState
  events: GestureEvent[]
}

export function GesturePanel({ data, events }: GesturePanelProps) {
  return (
    <PanelCard
      title="手勢辨識"
      icon={<Hand className="h-4 w-4" />}
      status={data.active ? "active" : "inactive"}
    >
      <div className="flex items-center justify-center h-32 text-[#55556A] text-sm">
        <p>TODO: 負責實作（見 gesture-panel-spec.md）</p>
      </div>
    </PanelCard>
  )
}
