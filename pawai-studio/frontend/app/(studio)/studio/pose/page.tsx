"use client";

import { useEventStream } from "@/hooks/use-event-stream";
import { StudioLayout } from "@/components/layout/studio-layout";
import { PosePanel } from "@/components/pose/pose-panel";

export default function PosePage() {
  const { isConnected } = useEventStream();

  return (
    <StudioLayout
      isConnected={isConnected}
      mainPanel={
        <div className="flex flex-col items-center justify-center h-full gap-6 px-6">
          <div className="w-full max-w-lg">
            <PosePanel />
          </div>
          <div className="text-sm text-muted-foreground text-center max-w-md space-y-2">
            <p>姿勢辨識面板開發頁</p>
            <p>
              修改 <code className="text-xs bg-muted px-1.5 py-0.5 rounded font-mono">components/pose/pose-panel.tsx</code>
            </p>
            <p>
              規格 <code className="text-xs bg-muted px-1.5 py-0.5 rounded font-mono">docs/pose-panel-spec.md</code>
            </p>
            <p className="text-xs">觸發測試事件：<code className="bg-muted px-1.5 py-0.5 rounded font-mono">curl -X POST http://localhost:8001/mock/scenario/demo_a</code></p>
          </div>
        </div>
      }
    />
  );
}
