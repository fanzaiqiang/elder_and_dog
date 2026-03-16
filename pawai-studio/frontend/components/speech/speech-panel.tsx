'use client'

import { useEffect, useState } from 'react'
import { Mic, VolumeX, Mic2, UserCircle2 } from 'lucide-react'
import { PanelCard } from '@/components/shared/panel-card'
import { useStateStore } from '@/stores/state-store'
import { useEventStore } from '@/stores/event-store'
import type { SpeechState, SpeechPhase, PawAIEvent, SpeechIntentEvent } from '@/contracts/types'

const PHASE_CONFIG: Record<SpeechPhase, { label: string; colorClass: string }> = {
  idle_wakeword: { label: '等待喚醒', colorClass: 'bg-muted-foreground' },
  wake_ack: { label: '喚醒確認', colorClass: 'bg-warning' },
  loading_local_stack: { label: '載入模型中', colorClass: 'bg-warning' },
  listening: { label: '聆聽中', colorClass: 'bg-success' },
  transcribing: { label: '轉寫中', colorClass: 'bg-primary' },
  local_asr_done: { label: 'ASR 完成', colorClass: 'bg-primary' },
  cloud_brain_pending: { label: '等待大腦', colorClass: 'bg-warning' },
  speaking: { label: '播放中', colorClass: 'bg-success' },
  keep_alive: { label: '保持連線', colorClass: 'bg-muted-foreground' },
  unloading: { label: '卸載中', colorClass: 'bg-muted-foreground' },
}

const EXPECTED_MODELS = ['kws', 'asr', 'tts']

// 🛡️ 終極解法：型別保鑣 (Type Guard)
// 這會明確告訴 TypeScript：「只要通過這個檢查的事件，它的 data 裡面絕對有 text 跟 intent！」
function isSpeechEvent(e: PawAIEvent): e is SpeechIntentEvent {
  return e.source === 'speech'
}

export function SpeechPanel() {
  const speechState = useStateStore((s) => s.speechState) as SpeechState | null
  const updateSpeechState = useStateStore((s) => s.updateSpeechState)
  const addEvent = useEventStore((s) => s.addEvent)

  // 🖱️ 手動控制狀態
  const [isWaking, setIsWaking] = useState(false)
  
  const handleWakeUp = () => {
    setIsWaking(true)
    
    updateSpeechState({
      ...speechState!,
      phase: 'listening',
      last_asr_text: '',
      last_intent: ''
    })
    
    setTimeout(() => setIsWaking(false), 2000)
  }

  const handleStop = () => {
    updateSpeechState({
      ...speechState!,
      phase: 'idle_wakeword',
      last_tts_text: '已強制終止語音對話'
    })
  }

  // 🧪 注入假資料 (Mock Data) 僅供 UI 開發預覽使用
  useEffect(() => {
    if (updateSpeechState) {
      // 模擬語音狀態
      updateSpeechState({
        stamp: Math.floor(Date.now() / 1000),
        phase: 'transcribing',
        models_loaded: ['kws', 'asr', 'tts'],
        last_asr_text: '幫我打開客廳的燈',
        last_tts_text: '好的，馬上為您開啟客廳的燈',
        last_intent: 'turn_on_light',
      })
    }
  }, [updateSpeechState])

  // 先從 store 取出陣列，再在元件內過濾，避免 Zustand selector 每次回傳新陣列觸發無限重繪
  const allEvents = useEventStore((s) => s.events)
  const speechEvents = allEvents.filter(isSpeechEvent)
  const recentEvents = [...speechEvents].reverse().slice(0, 10)

  const latestIntentEvent = [...speechEvents].reverse().find(e => e.event_type === 'intent_recognized')
  const confidence = latestIntentEvent?.data?.confidence ?? 0
  const provider = latestIntentEvent?.data?.provider ?? 'unknown'

  // 🛡️ 終極解法：明確宣告 Literal Type，絕不讓 TS 亂猜
  let panelStatus: "loading" | "active" | "inactive" | "error" = "loading"
  if (!speechState) {
    panelStatus = "loading"
  } else if (speechState.phase !== 'idle_wakeword') {
    panelStatus = "active"
  } else {
    panelStatus = "inactive"
  }

  const phase = speechState?.phase ?? 'idle_wakeword'
  const phaseConfig = PHASE_CONFIG[phase as SpeechPhase] || { label: phase, colorClass: 'bg-muted-foreground' }

  const isListening = phase === 'listening'
  const isIdleEmpty = phase === 'idle_wakeword' && recentEvents.length === 0

  return (
    <PanelCard
      title="語音互動"
      icon={< Mic className="h-4 w-4" />}
      status={panelStatus}
    >
      {!speechState && (
        <div className="py-8 flex flex-col items-center justify-center text-muted-foreground" >
          <Mic className="h-6 w-6 mb-2 motion-safe:animate-pulse" />
          <span className="text-sm" > 正在連線語音模組...</span>
        </div>
      )}

      {
        speechState && isIdleEmpty && (
          <div className="py-10 flex flex-col items-center justify-center text-muted-foreground" >
            <Mic className="h-8 w-8 mb-3 opacity-20" />
            <span className="text-sm" > 等待喚醒詞...</span>
          </div>
        )
      }

      {
        speechState && !isIdleEmpty && (
          <div className="flex flex-col gap-4" >

            <div className="flex items-center gap-2" >
              <span className={`h-2.5 w-2.5 rounded-full ${phaseConfig.colorClass} motion-safe:transition-colors motion-safe:duration-150`} />
              < span className="text-sm font-medium text-foreground" > {phaseConfig.label} </span>

              {
                isListening && (
                  <div className="flex gap-1 ml-1" >
                    <span className="h-1.5 w-1.5 rounded-full bg-success motion-safe:animate-pulse" style={{ animationDelay: '0ms' }
                    } />
                    < span className="h-1.5 w-1.5 rounded-full bg-success motion-safe:animate-pulse" style={{ animationDelay: '300ms' }
                    } />
                    < span className="h-1.5 w-1.5 rounded-full bg-success motion-safe:animate-pulse" style={{ animationDelay: '600ms' }} />
                  </div>
                )}
            </div>

            {/* 使用三元運算子避免 React 渲染布林值警告 */}
            {
              speechState.last_asr_text ? (
                <div className="flex flex-col gap-2 p-3 bg-surface-hover rounded-lg border border-border/50" >
                  <span className="text-xs text-muted-foreground" > 最近轉寫 </span>
                  < p className="text-sm text-foreground motion-safe:animate-in motion-safe:fade-in duration-300" >
                    {speechState.last_asr_text}
                  </p>

                  {
                    speechState.last_intent ? (
                      <div className="flex items-center gap-2 mt-1" >
                        <span className="text-xs font-medium px-2 py-0.5 rounded-sm bg-primary/20 text-primary motion-safe:animate-in motion-safe:zoom-in duration-200" >
                          {speechState.last_intent} {confidence > 0 ? `${Math.round(confidence * 100)}%` : ''}
                        </span>
                        < span className="text-[10px] text-muted-foreground uppercase" > {provider} </span>
                      </div>
                    ) : null
                  }
                </div>
              ) : null
            }

            <div className="flex flex-col gap-2" >
              <span className="text-xs text-muted-foreground" > 已載入模型 </span>
              < div className="flex gap-2 pb-2" >
                {
                  EXPECTED_MODELS.map(model => {
                    const isLoaded = speechState.models_loaded?.includes(model)
                    return (
                      <span
                        key={model}
                        className={`text-xs px-2 py-1 rounded-sm uppercase motion-safe:transition-colors motion-safe:duration-200 ${isLoaded
                          ? 'bg-success/20 text-success'
                          : 'bg-muted/50 text-muted-foreground'
                          }`
                        }
                      >
                        {model}
                      </span>
                    )
                  })}
              </div>
            </div>

            {/* 🎛️ 手動操作控制區 */}
            <div className="grid grid-cols-3 gap-2 mt-2 pt-4 border-t border-border/40">
              <button
                onClick={handleWakeUp}
                disabled={isWaking || phase === 'listening'}
                className="flex flex-col items-center justify-center gap-1.5 p-2 rounded-lg bg-surface-hover hover:bg-surface-active active:scale-95 transition-all outline-none border border-border/50 disabled:opacity-50"
              >
                <div className={`p-1.5 rounded-full ${isWaking || phase === 'listening' ? 'bg-success/20 text-success animate-pulse' : 'bg-primary/20 text-primary'}`}>
                  <Mic2 className="h-4 w-4" />
                </div>
                <span className="text-[10px] text-muted-foreground font-medium">強制喚醒</span>
              </button>

              <button
                onClick={handleStop}
                className="flex flex-col items-center justify-center gap-1.5 p-2 rounded-lg bg-surface-hover hover:bg-surface-active active:scale-95 transition-all outline-none border border-border/50"
              >
                <div className="p-1.5 rounded-full bg-destructive/20 text-destructive">
                  <VolumeX className="h-4 w-4" />
                </div>
                <span className="text-[10px] text-muted-foreground font-medium">終止發聲</span>
              </button>

              <button
                onClick={() => {
                  alert('切換聲音功能：準備開啟 CosyVoice 設定視窗')
                }}
                className="flex flex-col items-center justify-center gap-1.5 p-2 rounded-lg bg-surface-hover hover:bg-surface-active active:scale-95 transition-all outline-none border border-border/50"
              >
                <div className="p-1.5 rounded-full bg-warning/20 text-warning">
                  <UserCircle2 className="h-4 w-4" />
                </div>
                <span className="text-[10px] text-muted-foreground font-medium">切換發聲人</span>
              </button>
            </div>

          </div>
        )}
    </PanelCard>
  )
}
