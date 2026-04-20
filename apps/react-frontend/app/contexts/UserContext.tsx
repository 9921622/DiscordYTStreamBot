import { createContext, useContext, useState, useEffect, type ReactNode } from "react"
import { backendAPI } from "~/api/backend-wrapper"
import type { DiscordUser } from "~/api/backend-types"

interface UserContextValue {
    discordUser: DiscordUser | undefined
    loading: boolean
}

const UserContext = createContext<UserContextValue>({ discordUser: undefined, loading: true })

export function UserProvider({ children }: { children: ReactNode }) {
    const [discordUser, setDiscordUser] = useState<DiscordUser>()
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        console.log("fetching user...")
        backendAPI.discord.get_user()
            .then(u => { console.log("user:", u); setDiscordUser(u) })
            .catch(() => { console.log("user fetch failed") })
            .finally(() => { console.log("loading done"); setLoading(false) })
    }, [])

    return (
        <UserContext.Provider value={{ discordUser, loading }}>
            {children}
        </UserContext.Provider>
    )
}

export const useUserContext = () => useContext(UserContext)
