import { createContext, useContext, useState, useEffect, type ReactNode } from "react"
import { discordBotAPI } from "~/api/discord/discord-wrapper"
import type { DiscordUser } from "~/api/backend-types"

interface BotContextType {
    botInChannel: boolean
    setBotInChannel: (v: boolean) => void
    guildID: string | null
}

const BotContext = createContext<BotContextType>({
    botInChannel: false,
    setBotInChannel: () => {},
    guildID: null,
})

export function BotProvider({ discordUser, children }: { discordUser?: DiscordUser, children: ReactNode }) {
    const [botInChannel, setBotInChannel] = useState(false)
    const [guildID, setGuildID] = useState<string | null>(null)

    useEffect(() => {
        if (!discordUser) return
        discordBotAPI.voice.get_user_vc(discordUser.discord_id).then(data => {
            if (data.guild_id) setGuildID(data.guild_id)
            setBotInChannel(data.bot_in_channel ?? false)
        })
    }, [discordUser])

    return (
        <BotContext.Provider value={{ botInChannel, setBotInChannel, guildID }}>
            {children}
        </BotContext.Provider>
    )
}

export const useBotContext = () => useContext(BotContext)
