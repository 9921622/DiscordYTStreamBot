import type { Route } from "./+types/layout";
import { useEffect, type ReactNode } from "react";

import Navbar from "~/components/Navbar";
import Musicbar from "~/components/musicbar/Musicbar";
import SideBarContent from "~/components/SideBar";
import HorizontalAccordion from "~/components/utilities/HorizontalAccordion";
import { BotProvider, useBotContext } from "~/contexts/BotContext";
import { UserProvider, useUserContext } from "~/contexts/UserContext";
import { SocketProvider, useSocketContext } from "~/contexts/SocketContext";
import { LibraryBig, ListMusic, PanelLeftClose, PanelRightClose } from "lucide-react";
import type { WSResponse } from "~/api/backend-types";
import { PlaylistProvider } from "~/contexts/PlaylistContext";
import { PlaybackStatusProvider } from "~/contexts/PlaybackStatusContext";
import PlaylistSidebar from "~/components/playlistsidebar/PlaylistSidebar";
import { Navigate, Outlet } from "react-router";

export function meta({}: Route.MetaArgs) {
    return [
        { title: `${import.meta.env.VITE_APP_NAME}` },
        { name: "description", content: `Welcome to ${import.meta.env.VITE_APP_NAME}!` },
    ];
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

function LayoutPage() {

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

                    <main className="flex-1 min-w-0 bg-base-200/60 backdrop-blur-sm border border-base-content/5 rounded-xl overflow-y-auto shadow-lg">
                        <Outlet />
                    </main>

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

export default function Layout() {
    return (
        <UserProvider>
            <LayoutGate />
        </UserProvider>
    )
}

function LayoutGate() {
    const { discordUser, loading } = useUserContext()

    if (loading) return <LoadingScreen />
    if (!discordUser) return <Navigate to="/login" replace />

    return (
        <BotProvider>
            <SocketProviderWrapper>
                <PlaylistProvider>
                <PlaybackStatusProvider>
                <LayoutPage />
                </PlaybackStatusProvider>
                </PlaylistProvider>
            </SocketProviderWrapper>
        </BotProvider>
    )
}

function LoadingScreen() {
    return (
        <div className="flex items-center justify-center h-screen bg-zinc-950">
            <span className="loading loading-spinner loading-lg text-primary" />
        </div>
    )
}
