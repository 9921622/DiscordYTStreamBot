import { useEffect, useState } from "react";
import type { DiscordUser } from "~/api/backend-types";
import { useBotContext } from "~/contexts/BotContext";
import { useSocketContext } from "~/contexts/SocketContext";
import type { WSResponse } from "~/api/backend-types";
import { Headphones } from "lucide-react";

const AVATAR_SIZE = 28;
const AVATAR_GAP = 8;
const STACK_OVERLAP = 5;
const MEMBER_STACK = 3;

function useMembers() {
    const { guildID, botInChannel } = useBotContext();
    const { send, on, connected } = useSocketContext();
    const [members, setMembers] = useState<DiscordUser[]>([]);

    useEffect(() => on("users", (resp: WSResponse) => {
        if (resp.data && resp.data.members) setMembers(resp.data.members);
    }), [on]);

    useEffect(() => {
        if (!guildID || !botInChannel || !connected) return;
        send({ type: "users" });
    }, [guildID, botInChannel, connected]);

    return { members };
}

export default function VCMembersContainer() {
    const { members } = useMembers();

    if (members.length === 0) return null;

    const stacked = members.length > MEMBER_STACK;

    const lockedAvatarWidth = MEMBER_STACK * AVATAR_SIZE + (MEMBER_STACK - 1) * AVATAR_GAP;

    const stackedWidth = AVATAR_SIZE + (members.length - 1) * (AVATAR_SIZE - STACK_OVERLAP);
    const neededOverlap =
        stackedWidth > lockedAvatarWidth && members.length > 1
            ? AVATAR_SIZE - Math.floor((lockedAvatarWidth - AVATAR_SIZE) / (members.length - 1))
            : STACK_OVERLAP;
    const clampedOverlap = Math.min(neededOverlap, AVATAR_SIZE - 4);

    return (
        <div
            className="
                inline-flex items-center gap-2
                w-fit
                px-2.5 py-1.5
                mx-2 my-1.5
                rounded-full
                bg-base-200/60 backdrop-blur-sm
                border border-base-content/8
                shadow-sm
                cursor-pointer
                hover:bg-base-200/90
                hover:border-base-content/15
                hover:shadow-md
                transition-all duration-200
                select-none
                group
            "
        >
            {/* Voice icon */}
            <Headphones
                className="w-3.5 h-3.5 text-success/80 flex-shrink-0 group-hover:text-success transition-colors duration-200"
            />

            {/* Avatar strip */}
            <div
                className="flex items-center overflow-hidden flex-shrink-0"
                style={{ width: lockedAvatarWidth }}
            >
                {members.map((member, i) => (
                    <div
                        key={member.discord_id}
                        className="tooltip flex-shrink-0"
                        data-tip={member.global_name}
                        style={{
                            marginLeft: i === 0 ? 0 : stacked ? -clampedOverlap : AVATAR_GAP,
                            zIndex: members.length - i,
                            position: "relative",
                            animation: "vcAvatarIn 200ms ease both",
                            animationDelay: `${i * 30}ms`,
                        }}
                    >
                        <img
                            src={member.avatar}
                            alt={member.global_name}
                            style={{ width: AVATAR_SIZE, height: AVATAR_SIZE }}
                            className={`
                                rounded-full flex-shrink-0
                                transition-transform duration-150
                                hover:scale-110 hover:z-50
                                ${stacked
                                    ? "ring-[2px] ring-base-200 shadow-sm"
                                    : ""}
                            `}
                        />
                    </div>
                ))}
            </div>

            {/* Member count */}
            {stacked && (
                <span className="text-[10px] font-semibold tabular-nums text-base-content/50 leading-none flex-shrink-0 -ml-0.5">
                    {members.length}
                </span>
            )}

            {/* Keyframe injection */}
            <style>{`
                @keyframes vcAvatarIn {
                    from { opacity: 0; transform: scale(0.7); }
                    to   { opacity: 1; transform: scale(1); }
                }
            `}</style>
        </div>
    );
}
