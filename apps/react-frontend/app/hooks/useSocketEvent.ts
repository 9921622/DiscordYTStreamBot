import { useEffect } from "react"
import { useSocketContext } from "~/contexts/SocketContext"

export function useSocketEvent(cmd: string, handler: (data: any) => void) {
  const { on } = useSocketContext()
  useEffect(() => on(cmd, handler), [cmd, handler])
}
