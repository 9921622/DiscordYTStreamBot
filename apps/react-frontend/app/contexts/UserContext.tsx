import { createContext, useContext, useState, useEffect, type ReactNode } from "react"
import { backendAPI } from "~/api/backend-wrapper"
import type { DiscordUser } from "~/api/backend-types"

const UserContext = createContext<DiscordUser | undefined>(undefined)

export function UserProvider({ children }: { children: ReactNode }) {
    const [discordUser, setDiscordUser] = useState<DiscordUser>()

    useEffect(() => {
        backendAPI.discord.get_user().then(setDiscordUser).catch(() => {})
    }, [])

    return <UserContext.Provider value={discordUser}>{children}</UserContext.Provider>
}

export const useUser = () => useContext(UserContext)
