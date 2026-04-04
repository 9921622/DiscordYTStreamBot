import { createContext, useContext, useEffect, useRef, useState, useCallback } from "react"
import type { WSResponse } from "~/api/backend-types"

type MessageHandler = (resp: WSResponse) => void

interface SocketContextValue {
  send: (data: Record<string, unknown>) => void
  on: (type: string, handler: MessageHandler) => () => void
  connected: boolean
}

const SocketContext = createContext<SocketContextValue | null>(null)

export function SocketProvider({ guildID, children }: { guildID?: string, children: React.ReactNode }) {
  const ws = useRef<WebSocket | null>(null)
  const handlers = useRef<Map<string, Set<MessageHandler>>>(new Map())
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    if (typeof WebSocket === "undefined") return;
    if (!guildID) return;
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:"
    const socket = new WebSocket(`${protocol}//${window.location.host}${import.meta.env.VITE_DISCORD_BOT_WS}/${guildID}`)
    ws.current = socket

    socket.onopen = () => setConnected(true)
    socket.onclose = () => setConnected(false)

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      const type = data.type as string
      handlers.current.get(type)?.forEach(h => h(data))
      handlers.current.get("*")?.forEach(h => h(data))  // wildcard listeners
    }

    return () => socket.close()
  }, [guildID])

  const send = useCallback((data: Record<string, unknown>) => {
    console.log("ws readyState:", ws.current?.readyState)
    if (typeof WebSocket === "undefined") return;
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(data))
    }
  }, [])

  // returns an unsubscribe function
  const on = useCallback((type: string, handler: MessageHandler) => {
    if (!handlers.current.has(type)) {
      handlers.current.set(type, new Set())
    }
    handlers.current.get(type)!.add(handler)
    return () => handlers.current.get(type)?.delete(handler)
  }, [])

  return (
    <SocketContext.Provider value={{ send, on, connected }}>
      {children}
    </SocketContext.Provider>
  )
}

export function useSocketContext() {
  const ctx = useContext(SocketContext)
  if (!ctx) throw new Error("useSocket must be used within a SocketProvider")
  return ctx
}
