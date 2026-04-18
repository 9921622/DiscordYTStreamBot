import type { Route } from "./+types/layout";
import { useEffect, useState, type ReactNode } from "react";

import { youtubeAPI } from "~/api/youtube/youtube-wrapper";
import type { YoutubeVideo } from "~/api/youtube/youtube-types";

import Navbar from "~/components/Navbar";
import Musicbar from "~/components/musicbar/Musicbar";
import SongContainer from "~/components/SongContainer";
import SideBarContent from "~/components/SideBar";
import HorizontalAccordion from "~/components/utilities/HorizontalAccordion";
import { BotProvider, useBotContext } from "~/contexts/BotContext";
import { UserProvider } from "~/contexts/UserContext";
import { SocketProvider, useSocketContext } from "~/contexts/SocketContext";
import { LibraryBig, ListMusic, PanelLeftClose, PanelRightClose } from "lucide-react";
import type { WSResponse } from "~/api/backend-types";
import { PlaylistProvider } from "~/contexts/PlaylistContext";
import { PlaybackStatusProvider } from "~/contexts/PlaybackStatusContext";
import PlaylistSidebar from "~/components/playlistsidebar/PlaylistSidebar";

export function meta({}: Route.MetaArgs) {
    return [
        { title: `${import.meta.env.VITE_APP_NAME}` },
        { name: "description", content: `Welcome to ${import.meta.env.VITE_APP_NAME}!` },
    ];
}

function useSongs() {
    const [songs, setSongs] = useState<YoutubeVideo[]>([]);

    useEffect(() => {
        youtubeAPI.video.list().then(setSongs).catch(() => {});
    }, []);

    return songs;
}

const MUSICBAR_HEIGHT = "var(--musicbar-height, 80px)";


function SidebarPanel() {
    return (
        <aside className="bg-base-200/60 backdrop-blur-sm border border-base-content/5 rounded-xl flex-shrink-0 h-full overflow-hidden shadow-lg">
            <HorizontalAccordion
                closedWidth="w-14"
                width="w-56"
                closeIcon={<PanelLeftClose size={16} />}
                openIcon={<LibraryBig size={16} />}
                iconSide="left"
            >
                <SideBarContent />
            </HorizontalAccordion>
        </aside>
    );
}

function MainContent({ songs }: { songs: YoutubeVideo[] }) {
    return (
        <main className="flex-1 min-w-0 bg-base-200/60 backdrop-blur-sm border border-base-content/5 rounded-xl overflow-y-auto shadow-lg">
            <div className="p-6">
                <header className="mb-5">
                    <h1 className="text-2xl font-semibold tracking-tight">All Songs</h1>
                    <p className="text-base-content/40 text-sm mt-0.5">
                        {songs.length > 0 ? `${songs.length} tracks` : "Loading…"}
                    </p>
                </header>
                <SongContainer songs={songs} />
                <div className="h-4" />
            </div>
        </main>
    );
}

function QueuePanel() {
    return (
        <aside className="bg-base-200/60 backdrop-blur-sm border border-base-content/5 rounded-xl flex-shrink-0 h-full overflow-hidden shadow-lg">
            <HorizontalAccordion
                closedWidth="w-48"
                width="w-112"
                closeIcon={<PanelRightClose size={16} />}
                openIcon={<ListMusic size={16} />}
            >
                <PlaylistSidebar />
            </HorizontalAccordion>
        </aside>
    );
}

// Page =====================================================================

function HomePage() {
    const songs = useSongs();

    const { on } = useSocketContext()
    useEffect(() => on("*", (resp: WSResponse) => {
		console.log("Received socket event:", resp)
	}), [on])

    return (
        <div className="flex flex-col h-screen bg-zinc-950">

            {/* Navbar */}
            <nav className="sticky top-0 z-50 flex-shrink-0 navbar bg-zinc-950/80 backdrop-blur-md border-b border-base-content/5 shadow-sm px-4">
                <div className="flex-1">
                    <Navbar />
                </div>
            </nav>

            {/* Body */}
            <div
                className="flex-1 overflow-hidden p-3"
                style={{ paddingBottom: `calc(${MUSICBAR_HEIGHT} + 2rem)` }}
            >
                <div className="flex gap-3 h-full overflow-hidden">
                    <SidebarPanel />
                    <MainContent songs={songs} />
                    <QueuePanel />
                </div>
            </div>

            {/* Musicbar */}
            <div className="fixed bottom-0 left-0 w-full z-50">
                <Musicbar />
            </div>
        </div>
    );
}


function BotSocketBridge() {
    /* This is here so when the bot sends the on_disconnect event. we can disable the bot */
    const { setBotInChannel } = useBotContext();
    const { on } = useSocketContext();

    useEffect(() => on("on_disconnect", (resp: WSResponse) => {
        if (!resp.success) return;
        setBotInChannel(false);
    }), [on]);

    return null;
}

function SocketProviderWrapper({ children }: { children: ReactNode }) {
    const { guildID } = useBotContext();
    return (
        <SocketProvider guildID={guildID ?? undefined}>
            <BotSocketBridge />
            {children}
        </SocketProvider>
    );
}

export default function Home() {
    return (
        <UserProvider>
            <BotProvider>
                <SocketProviderWrapper>

                    <PlaylistProvider>
                    <PlaybackStatusProvider>
                    <HomePage />
                    </PlaybackStatusProvider>
                    </PlaylistProvider>

                </SocketProviderWrapper>
            </BotProvider>
        </UserProvider>
    );
}
