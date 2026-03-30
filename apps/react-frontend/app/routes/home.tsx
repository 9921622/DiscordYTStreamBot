import type { Route } from "./+types/home";
import { useEffect, useState } from "react";

import { youtubeAPI } from "~/api/youtube/youtube-wrapper";
import type { YoutubeVideo } from "~/api/youtube/youtube-types";

import Navbar from "~/components/Navbar";
import Musicbar from "~/components/Musicbar";
import SongContainer from "~/components/SongContainer";
import SideBar from "~/components/SideBar";
import { BotProvider, useBotContext } from "~/contexts/BotContext"
import { UserProvider, useUser } from "~/contexts/UserContext";
import { PlaybackProvider, usePlayback } from "~/contexts/PlaybackContext";


export function meta({}: Route.MetaArgs) {
	return [
		{ title: `${import.meta.env.VITE_APP_NAME}` },
		{ name: "description", content: `Welcome to ${import.meta.env.VITE_APP_NAME}!` },
	];
}



function useSongs() {
	const [songs, setSongs] = useState<YoutubeVideo[]>([])

	useEffect(() => {
		youtubeAPI.video.list().then(setSongs).catch(() => {})
	}, [])

	return songs
}



function HomePage() {
    const songs = useSongs()

    return (
        <>
            <SideBar
                navbar={<Navbar />}
                content={
                    <div className="bg-zinc-900 p-5 rounded-md">
                        <p className="text-xl font-bold mb-3">All Songs</p>
                        <SongContainer songs={songs} />
                    </div>
                }
            />
            <div className="fixed bottom-0 left-0 w-full z-50">
                <Musicbar />
            </div>
        </>
    )
}

function HomeContextWrapper() {
    const discordUser = useUser()
    return (
        <BotProvider discordUser={discordUser}>
		<PlaybackProvider>
			<HomePage />
		</PlaybackProvider>
        </BotProvider>
    )
}

export default function Home() {
    return (
        <UserProvider>
            <HomeContextWrapper />
        </UserProvider>
    )
}
