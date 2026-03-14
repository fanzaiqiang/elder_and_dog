"use client"

import { User } from "lucide-react"
import { PanelCard } from "@/components/shared/panel-card"
import type { FaceState, FaceIdentityEvent } from "@/contracts/types"

interface FacePanelProps {
  data: FaceState
  events: FaceIdentityEvent[]
}

export function FacePanel({ data, events }: FacePanelProps) {
  return (
    <PanelCard
      title="人臉辨識"
      icon={<User className="h-4 w-4" />}
      status={data.face_count > 0 ? "active" : "inactive"}
      count={data.face_count}
    >
      <div className="flex items-center justify-center h-32 text-[#55556A] text-sm">
        <p>TODO: 鄔負責實作（見 face-panel-spec.md）</p>
      </div>
    </PanelCard>
  )
}
