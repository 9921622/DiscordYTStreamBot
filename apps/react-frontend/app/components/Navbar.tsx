import SongSearchbar from "./SongSearchbar";
import { discordBotAPI } from "~/api/discord/discord-wrapper";
import type { DiscordUser } from "~/api/backend-types";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import { useUserContext } from "~/contexts/UserContext";
import { useBotContext } from "~/contexts/BotContext";

function ProfileDropdown({ profile }: { profile?: DiscordUser }) {
    const navigate = useNavigate();

    const handleLogout = () => {
        localStorage.removeItem("access");
        localStorage.removeItem("refresh");
        navigate("/login");
    };

    if (!profile)
        return (
            <button
                className="btn btn-sm btn-primary rounded-full px-4"
                onClick={() => navigate("/login")}
            >
                Login
            </button>
        );

    return (
        <div className="dropdown dropdown-end">
            <div tabIndex={0} role="button" className="btn btn-ghost btn-circle avatar w-12 h-12 min-h-0">
                <div className="w-12 rounded-full ring-1 ring-base-content/10">
                    <img alt="Profile" src={profile.avatar_url} />
                </div>
            </div>
            <ul
                tabIndex={-1}
                className="menu menu-sm dropdown-content bg-base-100 rounded-xl z-10 mt-2 w-44 p-1.5 shadow-lg border border-base-200"
            >
                <li>
                    <a className="rounded-lg text-sm" onClick={() => navigate("/settings")}>
                        Settings
                    </a>
                </li>
                <li>
                    <a className="rounded-lg text-sm text-error" onClick={handleLogout}>
                        Logout
                    </a>
                </li>
            </ul>
        </div>
    );
}

function JoinChannel() {
    const { discordUser } = useUserContext();
    const { botInChannel, setBotInChannel } = useBotContext();
    const [loading, setLoading] = useState(false);
    const [inVC, setInVC] = useState<boolean | null>(null);

    useEffect(() => {
        if (!discordUser) return;
        discordBotAPI.voice.get_user_vc(discordUser.discord_id).then((data) => {
            setInVC(!!data.channel_id);
        });
    }, [discordUser]);

    const handleJoin = async () => {
        if (!discordUser) return;
        setLoading(true);
        await discordBotAPI.voice.join_user_vc(discordUser.discord_id);
        setBotInChannel(true);
        setLoading(false);
    };

    if (inVC === null) return null;

    if (!inVC)
        return (
            <div className="tooltip tooltip-bottom" data-tip="Join a voice channel first">
                <div className="flex items-center gap-1.5 text-xs text-base-content/30 px-3 py-1.5 rounded-full border border-base-content/10 select-none cursor-not-allowed">
                    <svg className="w-3.5 h-3.5" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
                        <path d="M2 2l12 12M6 4.268A2 2 0 018 4a2 2 0 012 2v2.268M4.341 7A4 4 0 008 12a4 4 0 003.607-2.3M8 12v3M5 15h6" />
                    </svg>
                    Not in VC
                </div>
            </div>
        );

    if (botInChannel)
        return (
            <div className="flex items-center gap-1.5 text-xs font-medium text-success bg-success/10 px-3 py-1.5 rounded-full">
                <span className="w-1.5 h-1.5 rounded-full bg-success animate-pulse" />
                In your channel
            </div>
        );

    return (
        <button
            className="btn btn-sm rounded-full px-4 gap-1.5 font-medium border border-base-content/15 bg-transparent hover:bg-base-200 text-base-content"
            onClick={handleJoin}
            disabled={loading}
        >
            {loading ? (
                <span className="loading loading-spinner loading-xs" />
            ) : (
                <svg className="w-3.5 h-3.5" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
                    <path d="M6 4a2 2 0 012-2 2 2 0 012 2v5a2 2 0 01-2 2 2 2 0 01-2-2V4zM4 9a4 4 0 004 4 4 4 0 004-4M8 13v3M5 16h6" />
                </svg>
            )}
            Join my VC
        </button>
    );
}

function DisconnectChannel() {
    const { botInChannel, setBotInChannel } = useBotContext();
    const { discordUser } = useUserContext();
    const [loading, setLoading] = useState(false);

    if (!botInChannel) return null;

    const handleDisconnect = async () => {
        if (!discordUser) return;
        setLoading(true);
        const vc = await discordBotAPI.voice.get_user_vc(discordUser.discord_id);
        if (vc.guild_id) {
            await discordBotAPI.voice.disconnect_vc(vc.guild_id);
        }
        setBotInChannel(false);
        setLoading(false);
    };

    return (
        <button
            className="btn btn-sm rounded-full px-4 gap-1.5 font-medium border border-error/30 bg-transparent hover:bg-error/10 text-error"
            onClick={handleDisconnect}
            disabled={loading}
        >
            {loading ? (
                <span className="loading loading-spinner loading-xs" />
            ) : (
                <svg className="w-3.5 h-3.5" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
                    <path d="M2 2l12 12M6 4.268A2 2 0 018 4a2 2 0 012 2v2.268M4.341 7A4 4 0 008 12a4 4 0 003.607-2.3M8 12v3M5 15h6" />
                </svg>
            )}
            Disconnect
        </button>
    );
}

export default function Navbar() {
    const { discordUser } = useUserContext();

    return (
        <nav className="h-[52px] px-4 flex items-center gap-3 bg-inherit z-50">
            {/* Logo */}
            <a className="text-[15px] font-semibold tracking-tight shrink-0">
                {import.meta.env.VITE_APP_NAME}
            </a>

            {/* Centered searchbar */}
            <div className="flex-1 flex justify-center">
                <div className="w-full max-w-sm">
                    <SongSearchbar />
                </div>
            </div>

            {/* Right side */}
            <div className="flex items-center gap-2 ml-auto shrink-0">
                <JoinChannel />
                <DisconnectChannel />
                <div className="w-px h-5 bg-base-content/10" />
                <ProfileDropdown profile={discordUser} />
            </div>
        </nav>
    );
}
