import type { Route } from "./+types/home";
import { useEffect, useState } from "react";

import { youtubeAPI } from "~/api/youtube/youtube-wrapper";
import type { YoutubeVideo } from "~/api/youtube/youtube-types";

import Navbar from "~/components/Navbar";
import Musicbar from "~/components/Musicbar";
import SongContainer from "~/components/SongContainer";
import SideBarContent from "~/components/SideBar";
import SongQueue from "~/components/SongQueue";
import HorizontalAccordion from "~/components/utilities/HorizontalAccordion";
import { BotProvider, useBotContext } from "~/contexts/BotContext";
import { UserProvider, useUser } from "~/contexts/UserContext";
import { SocketProvider } from "~/contexts/SocketContext";
import { PlaybackVideoProvider } from "~/contexts/PlaybackVideoContext";
import { PlaybackQueueProvider } from "~/contexts/PlaybackQueueContext";
import SongQueueClosed from "~/components/SongQueueClosed";

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

function HomePage() {
    const songs = useSongs();

    return (
        <>
            <div className="flex flex-col h-screen">
                <nav className="sticky top-0 z-50 navbar w-full bg-base-300 flex-shrink-0">
                    <div className="flex-1">
                        <Navbar />
                    </div>
                </nav>

                <div className="flex-1 overflow-hidden p-4 pb-[calc(var(--musicbar-height,80px)+50px)]">
                    <div className="flex gap-3 h-full overflow-hidden">

                        {/* Sidebar as left HorizontalAccordion */}
                        <div className="bg-zinc-900 rounded-md flex-shrink-0 h-full overflow-hidden">
                            <HorizontalAccordion
                                closedWidth="w-14"
                                width="w-56"
                            >
                                <SideBarContent />
                            </HorizontalAccordion>
                        </div>

                        {/* Main content */}
                        <div className="flex-1 bg-zinc-900 p-5 rounded-md overflow-y-auto">
                            <p className="text-xl font-bold mb-3">All Songs</p>
                            <SongContainer songs={songs} />
                            <div>&nbsp;</div>
                            <div>&nbsp;</div>
                        </div>

                        {/* Queue as right HorizontalAccordion */}
                        <div className="bg-zinc-900 rounded-md flex-shrink-0 h-full overflow-hidden">
                            <HorizontalAccordion
                                closedWidth="w-48"
                                width="w-112"
                                childrenClosed={<SongQueueClosed />}
                            >
                                <SongQueue />
                            </HorizontalAccordion>
                        </div>

                    </div>
                </div>
            </div>

            <div className="fixed bottom-0 left-0 w-full z-50">
                <Musicbar />
            </div>
        </>
    );
}

function HomeContextWrapperWrapper() {
    const { guildID } = useBotContext();
    return (
        <SocketProvider guildID={guildID ?? undefined}>
            <PlaybackVideoProvider>
                <PlaybackQueueProvider>
                    <HomePage />
                </PlaybackQueueProvider>
            </PlaybackVideoProvider>
        </SocketProvider>
    );
}

function HomeContextWrapper() {
    const discordUser = useUser();
    return (
        <BotProvider discordUser={discordUser}>
            <HomeContextWrapperWrapper />
        </BotProvider>
    );
}

export default function Home() {
    return (
        <UserProvider>
            <HomeContextWrapper />
        </UserProvider>
    );
}
