import { useEffect, useState } from "react";
import type { DiscordUser } from "~/api/backend-types";
import { useBotContext } from "~/contexts/BotContext";
import { useSocketContext } from "~/contexts/SocketContext";
import type { WSResponse } from "~/api/backend-types";

function useMembers() {
    const { guildID, botInChannel } = useBotContext()
    const { send, on, connected } = useSocketContext()
    const [members, setMembers] = useState<DiscordUser[]>([])

    useEffect(() => on("users", (resp: WSResponse) => {
        if (resp.data && resp.data.members) setMembers(resp.data.members)
    }), [on])

    useEffect(() => {
        if (!guildID || !botInChannel || !connected) return
        send({ type: "users" })
    }, [guildID, botInChannel, connected])

    return members
}

export default function VCMembersContainer() {
    const members = useMembers();

    if (members.length === 0) return null;

    return (
        <div className="p-2 m-2 bg-base-100 rounded-md flex items-center gap-2 self-start">
            <svg className="w-4 h-4 text-zinc-400 flex-shrink-0" fill="currentColor" viewBox="0 0 24 24">
                <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02z"/>
            </svg>
            {members.map(member => (
                <div key={member.discord_id} className="tooltip" data-tip={member.global_name}>
                    <img
                        src={member.avatar}
                        alt={member.global_name}
                        className="w-7 h-7 rounded-full"
                    />
                </div>
            ))}
        </div>
    )
}
