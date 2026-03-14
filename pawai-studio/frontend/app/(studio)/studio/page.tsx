"use client";

import { useEventStream } from "@/hooks/use-event-stream";
import { useEventStore } from "@/stores/event-store";
import { useStateStore } from "@/stores/state-store";
import { useLayoutStore } from "@/stores/layout-store";
import { StudioLayout } from "@/components/layout/studio-layout";
import { ChatPanel } from "@/components/chat/chat-panel";
import { FacePanel } from "@/components/face/face-panel";
import { SpeechPanel } from "@/components/speech/speech-panel";
import { GesturePanel } from "@/components/gesture/gesture-panel";
import { PosePanel } from "@/components/pose/pose-panel";
import type { FaceState, SpeechState, GestureState, PoseState } from "@/contracts/types";

const DEFAULT_FACE_STATE: FaceState = { stamp: 0, face_count: 0, tracks: [] };
const DEFAULT_SPEECH_STATE: SpeechState = { stamp: 0, phase: "idle_wakeword", last_asr_text: "", last_intent: "", last_tts_text: "", models_loaded: [] };
const DEFAULT_GESTURE_STATE: GestureState = { stamp: 0, active: false, current_gesture: null, confidence: 0, hand: null, status: "inactive" };
const DEFAULT_POSE_STATE: PoseState = { stamp: 0, active: false, current_pose: null, confidence: 0, track_id: null, status: "inactive" };

export default function StudioPage() {
  const { isConnected } = useEventStream();
  const events = useEventStore((s) => s.events);
  const faceState = useStateStore((s) => s.faceState) ?? DEFAULT_FACE_STATE;
  const speechState = useStateStore((s) => s.speechState) ?? DEFAULT_SPEECH_STATE;
  const gestureState = useStateStore((s) => s.gestureState) ?? DEFAULT_GESTURE_STATE;
  const poseState = useStateStore((s) => s.poseState) ?? DEFAULT_POSE_STATE;
  const activePanels = useLayoutStore((s) => s.activePanels);

  const faceEvents = events.filter((e) => e.source === "face");
  const speechEvents = events.filter((e) => e.source === "speech");
  const gestureEvents = events.filter((e) => e.source === "gesture");
  const poseEvents = events.filter((e) => e.source === "pose");

  // Build sidebar panels based on active layout
  const sidebarPanels: React.ReactNode[] = [];
  if (activePanels.has("face")) {
    sidebarPanels.push(<FacePanel key="face" data={faceState} events={faceEvents as any} />);
  }
  if (activePanels.has("speech")) {
    sidebarPanels.push(<SpeechPanel key="speech" data={speechState} events={speechEvents as any} />);
  }
  if (activePanels.has("gesture")) {
    sidebarPanels.push(<GesturePanel key="gesture" data={gestureState} events={gestureEvents as any} />);
  }
  if (activePanels.has("pose")) {
    sidebarPanels.push(<PosePanel key="pose" data={poseState} events={poseEvents as any} />);
  }

  return (
    <StudioLayout
      isConnected={isConnected}
      mainPanel={<ChatPanel events={events} />}
      sidebarPanels={sidebarPanels.length > 0 ? sidebarPanels : undefined}
    />
  );
}
