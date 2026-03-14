"use client"

import { PersonStanding } from "lucide-react"
import { PanelCard } from "@/components/shared/panel-card"
import type { PoseState, PoseEvent } from "@/contracts/types"

interface PosePanelProps {
  data: PoseState
  events: PoseEvent[]
}

export function PosePanel({ data, events }: PosePanelProps) {
  return (
    <PanelCard
      title="姿勢辨識"
      icon={<PersonStanding className="h-4 w-4" />}
      status={data.active ? "active" : "inactive"}
    >
      <div className="flex items-center justify-center h-32 text-[#55556A] text-sm">
        <p>TODO: 負責實作（見 pose-panel-spec.md）</p>
      </div>
    </PanelCard>
  )
}
